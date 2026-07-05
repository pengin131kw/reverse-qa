# 逆質問箱(Reverse Mailbox)

質問箱の逆バージョン。**あなた(ホスト)が質問を作り**、URLを配って**みんなに回答してもらう**サービスです。
ログイン不要。URLだけで完結します。

- ホスト用URL(例: `/host/xxxxx`) … あなただけが知っている「回答を見るための鍵」
- 公開用URL(例: `/q/yyyyy`) … SNSやDMで配る「回答してもらうためのリンク」

---

## 0. 全体の仕組み(先に理解しておくと迷わない)

```
[あなた] --質問を投稿--> [サーバー] --host用URLを発行--> [あなた]
                              |
                              +--public用URLを発行--> [あなたがSNS等で拡散]
                                                            |
                                                       [フォロワーがアクセス]
                                                            |
                                                     回答を送信 → サーバーに保存
                                                            |
                                            [あなた] host用URLを開くと回答一覧が見える
```

技術構成:

| 役割 | 使うもの |
|---|---|
| プログラミング言語 | Python |
| Webフレームワーク | Flask(軽量で学習コストが低い) |
| データベース | SQLite(ファイル1つで完結、追加インストール不要) |
| 公開先(サーバー) | Render.com(無料枠あり) |
| ドメイン | 最初は不要。慣れたら独自ドメインを追加(月100円程度〜) |

---

## 1. ローカルで動かしてみる

### 1-1. Pythonをインストール
公式サイトから最新版(3.11以降)をインストールしてください。
https://www.python.org/downloads/

インストール後、ターミナル(Mac)またはコマンドプロンプト/PowerShell(Windows)で確認:

```bash
python3 --version
```

### 1-2. プロジェクトのファイルを用意
このzipを展開したフォルダ(`reverse-qa`)に移動します。

```bash
cd reverse-qa
```

### 1-3. 仮想環境を作る(プロジェクトごとにライブラリを分離する仕組み)

```bash
python3 -m venv venv

# Macの場合
source venv/bin/activate

# Windowsの場合
venv\Scripts\activate
```

ターミナルの先頭に `(venv)` と表示されればOKです。

### 1-4. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

### 1-5. 起動

```bash
python3 app.py
```

ターミナルに `http://127.0.0.1:5000` のようなURLが表示されるので、ブラウザで開いてください。
質問を投稿すると `data.db` というファイルが自動で作られ、そこに質問と回答が保存されます。

---

## 2. インターネットに公開する(Render.com / 無料)

ローカルで動くURL(`127.0.0.1`)は自分のパソコンの中だけでしか見られません。
他の人からアクセスできるようにするには、サーバーにアップロードする必要があります。

### 2-1. GitHubにコードを置く
1. https://github.com でアカウント作成(無料)
2. 新しいリポジトリを作成(例: `reverse-qa`)
3. このフォルダをアップロード。ターミナルからなら:

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/reverse-qa.git
git push -u origin main
```

### 2-2. Renderでデプロイ
1. https://render.com でアカウント作成(GitHubアカウントでログイン可能)
2. ダッシュボードで **New +** → **Web Service** を選択
3. 先ほどのGitHubリポジトリを選択
4. 設定項目:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. **Create Web Service** をクリック

数分待つと `https://reverse-qa-xxxx.onrender.com` のようなURLが発行され、これが本番URLになります。

> **無料枠の注意点**: しばらくアクセスがないとサーバーが自動的に眠り(スリープ)、次のアクセス時に起動まで数十秒かかることがあります。個人利用や小規模な用途なら問題ありません。

### 2-3. データが消えることがある点に注意
Renderの無料プランはファイル(=`data.db`)が再デプロイ時にリセットされることがあります。
最初のうちは気にしなくてOKですが、本格運用したくなったら:
- Render純正の「PostgreSQL(無料枠あり)」に切り替える
- もしくは Railway.app や Fly.io など、永続ディスクが使える他サービスを検討する

このあたりは「動くものが完成してから」で十分です。

---

## 3. 独自ドメインを取得する(任意・あとからでOK)

`onrender.com` のままでも十分使えますが、自分だけのドメイン(例: `gyaku-shitsumon.com`)にしたくなったら:

1. ドメイン取得サービスで購入
   - Cloudflare Registrar(原価販売で安い。日本語対応あり): https://www.cloudflare.com/products/registrar/
   - お名前.com、ムームードメインなど国内サービスでも可
   - `.com` や `.jp` 以外に `.net`, `.dev`, `.me` なども選べます(安いものだと年1,000円前後)
2. Renderの管理画面 → 対象のWeb Service → **Settings** → **Custom Domains** で購入したドメインを追加
3. ドメイン取得サービス側のDNS設定で、Renderが指示するCNAME/Aレコードを設定
4. 反映まで数分〜数時間待つと、独自ドメインでアクセスできるようになります

---

## 4. Twitter / Misskeyとの連携について

現状の設計は「ログイン不要のURL方式」なので、Twitter/MisskeyのOAuth連携は組み込んでいません。
ただし、拡張は難しくありません:

- **簡易版(おすすめ)**: ホストページに「この質問をTwitterでシェア」ボタンを置くだけ。
  ログインは不要で、公開用URLを含んだツイート下書き画面を開くだけの実装です。
  ```html
  <a href="https://twitter.com/intent/tweet?text=この質問に答えてね&url={{ public_url }}" target="_blank">
    Xでシェア
  </a>
  ```
  Misskeyの場合はインスタンスごとに投稿画面のURLが異なるため、
  `https://(インスタンスのドメイン)/share?text=...&url=...` の形式で概ね同様に組めます。

- **本格版**: Twitter/Misskeyアカウントでログインさせ、「フォロワーにだけ公開する」等をやりたい場合はOAuth連携が必要になり、実装量が大きく増えます。まずはURL方式で公開して、必要になったら追加するのがおすすめです。

---

## 5. 今後の拡張アイデア

- 質問の削除機能(host_tokenが分かる人だけ削除できるようにする)
- 回答へのいいね機能
- 1人が同じ質問に何度も回答できないようにする(Cookieやレート制限)
- 回答をCSVでダウンロードする機能
- 質問の有効期限・回答受付終了機能

分からない箇所や、次に実装したい機能があれば教えてください。
