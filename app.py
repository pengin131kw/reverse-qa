import os
import secrets
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, abort, g

# ------------------------------------------------------------
# 初期設定
# ------------------------------------------------------------
app = Flask(__name__)

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASEDIR, "data.db")


def get_db():
    """リクエスト中で使い回すDB接続を取得する"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """テーブルが無ければ作成する"""
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            host_token TEXT UNIQUE NOT NULL,
            public_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS answer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            name TEXT,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (question_id) REFERENCES question (id)
        );
        """
    )
    db.commit()
    db.close()


def make_token() -> str:
    """衝突しにくいランダムな文字列トークンを作る"""
    return secrets.token_urlsafe(12)


# ------------------------------------------------------------
# ルーティング(URLごとの処理)
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create_question():
    text = request.form.get("question", "").strip()
    if not text:
        return redirect(url_for("index"))

    db = get_db()
    host_token = make_token()
    public_token = make_token()
    db.execute(
        "INSERT INTO question (text, host_token, public_token, created_at) "
        "VALUES (?, ?, ?, ?)",
        (text, host_token, public_token, datetime.utcnow().isoformat()),
    )
    db.commit()

    return redirect(url_for("host_view", host_token=host_token))


@app.route("/host/<host_token>")
def host_view(host_token):
    db = get_db()
    question = db.execute(
        "SELECT * FROM question WHERE host_token = ?", (host_token,)
    ).fetchone()
    if question is None:
        abort(404)

    rows = db.execute(
        "SELECT * FROM answer WHERE question_id = ? ORDER BY created_at DESC",
        (question["id"],),
    ).fetchall()
    answers = [
        {
            "name": row["name"],
            "text": row["text"],
            "created_at": datetime.fromisoformat(row["created_at"]),
        }
        for row in rows
    ]

    public_url = url_for(
        "public_view", public_token=question["public_token"], _external=True
    )
    return render_template(
        "host.html", question=question, public_url=public_url, answers=answers
    )


@app.route("/q/<public_token>", methods=["GET", "POST"])
def public_view(public_token):
    db = get_db()
    question = db.execute(
        "SELECT * FROM question WHERE public_token = ?", (public_token,)
    ).fetchone()
    if question is None:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        text = request.form.get("answer", "").strip()
        if text:
            db.execute(
                "INSERT INTO answer (question_id, name, text, created_at) "
                "VALUES (?, ?, ?, ?)",
                (question["id"], name or None, text, datetime.utcnow().isoformat()),
            )
            db.commit()
            return render_template("thanks.html", question=question)

    return render_template("question.html", question=question)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# アプリ起動時に一度だけテーブルを作成しておく(gunicorn経由の本番起動でも実行される)
init_db()


# ------------------------------------------------------------
# ローカル実行用(python app.py で直接動かす時だけ通る)
# ------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
