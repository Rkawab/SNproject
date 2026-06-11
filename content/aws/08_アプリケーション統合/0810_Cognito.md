# Cognito

> [!info] 概要
> Web・モバイルアプリ向けの**ユーザー認証・認可・ID管理**をまるごと肩代わりするサービス。サインアップ・ログイン・パスワードリセット・MFA・ソーシャル連携を自前実装せずに済む。

## たとえ話

**アプリの「会員証システム」**。
- 新規会員登録（サインアップ）
- 会員カードでログイン
- カードに応じてどの施設が使えるか管理（権限）
- 他社の会員証（Google / Facebook）でも入場OKにする連携
- 二重チェック（MFA）の運用

---

## ⚠️ 最重要 ― 2つのPoolの違い

Cognito は2つの独立した機能群からなる。混同しないよう要注意。

| Pool | 役割 | キーワード | 出力 |
|------|------|----------|------|
| **User Pools** | **誰か（Who）** の管理 | サインアップ・ログイン・パスワード・MFA | **JWT トークン** |
| **Identity Pools**<br>（旧 Federated Identities） | **何ができるか（What）** の管理 | AWSリソースへの一時アクセス権 | **一時的なIAM認証情報** |

```
[ユーザー]
   ↓ ID/PW
[Cognito User Pools] ── 認証OK ──> [JWTトークン発行]
   ↓ JWT
[Identity Pools] ── 検証 ──> [一時的なIAM Credentials]
   ↓ アクセス
[S3 / DynamoDB / その他AWSリソース]
```

> [!tip] 使い分け
> - 「アプリのログイン機能だけ」→ **User Pools**
> - 「ログイン後にユーザーが直接S3にアクセス」→ **Identity Pools**
> - 両方使う場合が多い（特にモバイルアプリ）

---

## ① User Pools の詳細

### 基本機能

- **サインアップ**: メール / 電話番号 / カスタム属性 で登録
- **検証**: メール / SMS で確認コード送信
- **サインイン**: ID/PWでログイン
- **パスワードポリシー**: 最小長・大文字小文字・記号必須など設定
- **アカウントロックアウト**: 失敗回数で自動ロック

### MFA（多要素認証）

| 種類 | 詳細 |
|------|------|
| **SMS MFA** | 携帯電話にコード送信 |
| **TOTP MFA** | Google Authenticator 等のアプリでコード生成（推奨） |
| **Adaptive Authentication** | リスク判定（普段と違うIP・端末）で動的にMFAを要求 |

### ソーシャル / フェデレーション

外部IDプロバイダで「ソーシャルログイン」を実現:

- **ソーシャル**: Google / Facebook / Apple / Amazon
- **エンタープライズ**: **SAML 2.0** / **OIDC**

設定すると、ユーザーは「Googleでログイン」ボタンを押すだけで自分のアプリに入れる。

### JWT トークン（3種類）

ログイン成功時にUser Poolsが発行するトークン:

| トークン | 含まれる情報 | 用途 |
|---------|------------|------|
| **IDトークン** | ユーザー属性（名前・メール等） | フロント表示用 |
| **アクセストークン** | スコープ（権限） | API呼び出し時に添付 |
| **リフレッシュトークン** | 長期的（30日等） | 上記2つの再発行用 |

[[0809_API_Gateway]] の **Cognito Authorizer** がこのアクセストークン/IDトークンを検証してくれる。

### Lambda トリガー（カスタマイズの要）

User Pools の各イベントで Lambda を起動できる:

| トリガー | タイミング | 用途例 |
|---------|----------|--------|
| **Pre Sign-up** | 登録直前 | ドメイン制限・自動承認 |
| **Post Confirmation** | 登録完了直後 | DynamoDBにプロファイル作成 |
| **Pre Authentication** | ログイン直前 | 不正検知・IPブロック |
| **Post Authentication** | ログイン直後 | 監査ログ記録 |
| **Pre Token Generation** | トークン発行時 | カスタムClaim追加 |
| **Custom Message** | 確認メール送信時 | メール文面カスタマイズ |
| **Custom Auth Challenge** | カスタム認証フロー | パスワードレス認証 |

### App Client（アプリクライアント）

User Pools内で「どのアプリから使うか」を分離して設定する単位。

- iOS用・Android用・Web用で別App Clientにできる
- それぞれ別々のクライアントID/Secretを持つ
- 認証フロー・有効トークン期間も個別設定

### Hosted UI

Cognitoがホスティングする**ログイン画面**を使える。
- 自前でログイン画面を作らなくていい
- 配色・ロゴをカスタマイズ可能
- 独自ドメイン（auth.example.com）にも割当可能

### 認証フロー

| フロー | 動作 |
|-------|------|
| **SRP**（Secure Remote Password） | パスワードを送らずに認証（推奨） |
| **USER_PASSWORD_AUTH** | ID/PWをそのまま送信（HTTPS必須） |
| **ADMIN_NO_SRP_AUTH** | サーバー側からの管理者認証 |
| **CUSTOM_AUTH** | Lambdaで独自フロー（パスワードレス等） |

---

## ② Identity Pools の詳細

### 役割

「認証済みユーザー」「未認証ユーザー」それぞれに**IAMロール**を割り当て、**一時的なAWS認証情報**を発行する。

```
[認証されたユーザー]
       ↓ JWT (User Pools / Google / Facebook)
[Identity Pool]
       ↓ STS:AssumeRoleWithWebIdentity
[認証済みロール（Authenticated Role）]
   - S3 の自分のフォルダにRead/Write
   - DynamoDB の自分のレコードに Read/Write
```

### 認証済み / 未認証ロール

| ロール | 用途 |
|--------|------|
| **Authenticated Role** | ログインユーザー向け（フル機能） |
| **Unauthenticated Role** | ゲスト向け（読み取り限定など） |

### ロールの動的選択

ユーザー属性に応じて**ロールを切り替える**ことも可能（Role Mapping）:
- 管理者属性のユーザーには管理者ロール
- 一般ユーザーには一般ロール

### きめ細かい権限制御

IAMポリシーで `${cognito-identity.amazonaws.com:sub}` 変数を使って「**自分のリソースだけアクセス可**」を実現:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::mybucket/${cognito-identity.amazonaws.com:sub}/*"
}
```

これで「自分のIDのフォルダ配下しか読めない」が実現できる。

---

## 典型構成

### モバイルアプリの認証＆S3直アクセス

```
[iOSアプリ]
   ↓ ① サインイン
[Cognito User Pools]
   ↓ ② JWT発行
[iOSアプリ]
   ↓ ③ JWTを送る
[Cognito Identity Pool]
   ↓ ④ 一時IAM認証情報を発行
[iOSアプリ]
   ↓ ⑤ 一時認証情報でS3アクセス
[S3 バケット（ユーザーごとのプレフィックス）]
```

### サーバーレスAPIの認証

```
[SPA / Mobile]
   ↓ サインイン
[Cognito User Pools] → JWT
   ↓ JWT付きAPI呼び出し
[API Gateway + Cognito Authorizer]  ← JWT検証
   ↓
[Lambda]
   ↓
[DynamoDB]
```

---

## Cognito vs IAM（混同注意）

| 観点 | Cognito | [[0601_IAM基礎]] |
|------|---------|-------|
| 対象 | アプリの**エンドユーザー**（消費者） | AWS操作する**開発者・運用者** |
| 想定数 | 数百万〜数千万人 | 数十〜数百人 |
| 認証情報 | ID/PW / ソーシャルログイン | アクセスキー / コンソールPW |
| 主目的 | アプリの会員管理 | AWSリソース操作の権限管理 |

> アプリのユーザー向けは **Cognito**、社内エンジニア向けは **IAM**。

---

## SAA頻出パターン

| 問題文のキーワード | 答え |
|---------------------|------|
| 「**モバイルアプリ**のユーザー認証」 | Cognito User Pools |
| 「**ソーシャルログイン**（Google等）」 | Cognito + 外部IDプロバイダ |
| 「**ユーザーごとのS3フォルダ**にアクセス」 | Cognito Identity Pools + IAMポリシー |
| 「[[0809_API_Gateway]] でJWTを使った認可」 | Cognito Authorizer |
| 「数百万ユーザーのスケーラブルな認証」 | Cognito |
| 「**MFA**を組み込みたい」 | Cognito User Pools の MFA |
| 「**サインアップ時に独自処理**」 | Cognito Lambda トリガー |
| 「**SAML**による企業認証」 | Cognito + SAML プロバイダ |

---

## 料金

- **User Pools**: MAU（Monthly Active Users）課金。50,000 MAU まで無料枠
- **Identity Pools**: **無料**（STSの呼び出し費用のみ）

---

## 関連

- [[0809_API_Gateway]] - Cognito Authorizer で認証統合
- [[0601_IAM基礎]] - AWS操作する人向け（こちらと混同注意）
- [[Lambda]] - User Pools のトリガーで使う
