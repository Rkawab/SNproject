# API Gateway

> [!info] 概要
> APIの**作成・公開・運用・保護**をフルマネージドで提供するサービス。外部からのHTTPリクエストを受け付け、Lambda / EC2 / ECS / 他AWSサービス / 外部HTTPに振り分ける「**APIの玄関口**」。サーバーレスアーキテクチャの中心的存在。

## たとえ話

**ホテルのフロントデスク**。
- 来館客（クライアント）の用件をすべてフロントで受け付ける
- 「予約」「ルームサービス」「会計」と適切な部署に取り次ぐ
- VIP判定（**認証**）、混雑時のお断り（**スロットリング**）、よくある質問の即答（**キャッシュ**）、館内ルール（**WAF**）、お客様の声記録（**ロギング**）もここで一括処理
- 裏で誰が働いているか（Lambda / EC2 / ECS）はお客様には見せない

---

## サポートするAPIタイプ

| タイプ | 特徴 | コスト | 用途 |
|--------|------|--------|------|
| **REST API** | 全機能（キャッシュ・APIキー・WAF・カナリア等） | 高 | 一般的なREST API |
| **HTTP API** | 軽量・**低レイテンシ**・低コスト | 低（REST比 約70%減） | シンプルなプロキシ・新規 |
| **WebSocket API** | 双方向通信 | 中 | チャット・通知・ゲーム |

> [!tip] 新規はまず HTTP API を検討
> HTTP APIは2020年から提供。RESTより機能は少ないが、必要十分な機能だけならHTTPの方が安くて速い。要件にキャッシュ・APIキー・リクエスト検証等が必要ならREST。

---

## 統合タイプ（バックエンドへの接続方式）

| 統合タイプ | 動作 |
|-----------|------|
| **Lambda Proxy** | リクエスト全体をLambdaに丸投げ（最頻出） |
| **Lambda（非Proxy）** | マッピングテンプレート（VTL）で変換してLambdaに渡す |
| **HTTP / HTTP Proxy** | 外部HTTPエンドポイントに転送 |
| **AWS Service** | 直接AWSサービス呼び出し（例: SQSへ直接Put） |
| **Mock** | バックエンド無しで固定レスポンス（テスト用） |
| **VPC Link** | プライベートな ALB / NLB / VPCリソースに接続 |

> [!info] AWS Service統合の使いどころ
> 例えば「POSTされたら直接SQSにメッセージを入れる」を**Lambdaを介さず**実現できる。コスト削減＆レイテンシ削減。

---

## エンドポイントの種類

| 種類 | 特徴 |
|------|------|
| **Edge-Optimized**（デフォルト） | CloudFront経由でグローバル配信。海外ユーザー向け |
| **Regional** | 同一リージョン向け。自前のCloudFrontを前に置きたい場合 |
| **Private** | VPC内からのみアクセス可能。社内システム |

---

## 認証・認可（4種類）

| 方式 | 用途 | 動作 |
|------|------|------|
| **IAM 認証** | AWSサービス間 / IAMユーザー | SigV4 署名でリクエスト |
| **Lambda Authorizer**（旧 Custom Authorizer） | 独自トークン・サードパーティ認証 | Lambda関数で検証ロジック実装 |
| **Cognito Authorizer** | アプリ利用者の認証 | [[0810_Cognito]] User Pools のJWTを検証 |
| **APIキー + 使用量プラン** | 顧客ごとのレート制限 | APIキーヘッダーで識別 |
| **Resource Policy** | IP制限・VPC制限・クロスアカウント制御 | リソースベースのIAM |

---

## スロットリング（4層構造）

リクエスト数の制御は階層構造になっている。低い方が優先される。

```
[AWSアカウントレベル]  10,000 req/秒（デフォルト・引き上げ申請可）
       ↓
[Stage / Method レベル]  ステージごとの上限
       ↓
[Usage Plan レベル]  APIキー単位の上限
       ↓
[Per-Client レベル]  個別クライアントの上限
```

突発トラフィックには **バースト容量**（バケット容量5000）で対応。

---

## キャッシュ機能（REST APIのみ）

ステージごとに**0.5GB〜237GB**のキャッシュを設定可能。
- TTLは0秒〜3600秒
- バックエンド呼び出しを減らしてコスト削減・低レイテンシ化
- `Cache-Control: max-age=0` でクライアント側からキャッシュ無効化も可

---

## ステージとデプロイメント

```
[開発] git push
       ↓
[CodePipeline]
       ↓ Deploy
[API Gateway]
   ├─ Stage: dev    (https://xxx.execute-api.../dev)
   ├─ Stage: staging (https://xxx.execute-api.../staging)
   └─ Stage: prod   (https://xxx.execute-api.../prod)
```

### カナリアリリース

新バージョンに **段階的にトラフィックを流す**機能。

```
prod ステージ
 ├─ 95% → 旧バージョン
 └─  5% → 新バージョン（カナリア）
```

問題なければ徐々に100%に上げる。問題があれば即ロールバック。

---

## CORS（Cross-Origin Resource Sharing）

ブラウザから別オリジンのAPIを叩く場合、**プリフライト（OPTIONS）リクエスト**に正しいヘッダーで応答する必要がある。

- コンソールから「Enable CORS」で自動生成
- `Access-Control-Allow-Origin` 等のヘッダーをマッピングテンプレートやLambda側で返す

---

## カスタムドメイン名

`xxxxx.execute-api.region.amazonaws.com/stage` ではなく `api.example.com` で公開できる。

- **ACM証明書**が必要
  - Edge-Optimized: **us-east-1（バージニア北部）** のACM必須
  - Regional: 同リージョンのACM
- Route 53 で A エイリアスレコードを設定

---

## ロギング・モニタリング

| 機能 | 詳細 |
|------|------|
| **CloudWatch Logs** | リクエスト/レスポンスログ |
| **CloudWatch Metrics** | レイテンシ・4XX/5XX・キャッシュヒット率 |
| **AWS X-Ray** | 分散トレーシング（Lambda・DynamoDBまで追跡可） |
| **Access Logs** | カスタムフォーマットでアクセスログ出力 |

---

## 典型構成

### サーバーレスAPI（最頻出）

```
クライアント
   ↓ HTTPS
[Route 53] → [CloudFront（任意）] 
   ↓
[API Gateway] ← [Cognito Authorizer]
   ↓
[Lambda] → [DynamoDB / RDS / S3]
```

### マイクロサービス集約

```
[API Gateway]
 ├─ /users    → Lambda A → DynamoDB
 ├─ /orders   → ECS Service B (via VPC Link)
 ├─ /payments → 外部API（HTTP Proxy）
 └─ /admin    → IAM認証 + Lambda C
```

### WebSocket チャット

```
[クライアント] ← WebSocket → [API Gateway WebSocket API]
                                     ↓
                                  [Lambda]
                                     ↓
                              [DynamoDB（接続ID保存）]
```

---

## SAA頻出パターン

| 問題文のキーワード | 答え |
|---------------------|------|
| 「**サーバーレスAPI**」「Lambdaの前段」 | API Gateway |
| 「**APIキー**で顧客ごとに制限」 | API Gateway + **Usage Plan** |
| 「**JWT認証**」「Cognitoユーザー認証」 | Cognito Authorizer |
| 「**カスタム認証ロジック**」「JWT以外のトークン」 | Lambda Authorizer |
| 「**Webソケット**でリアルタイム通信」 | WebSocket API |
| 「**バックエンドの負荷を減らす**」 | キャッシュ + スロットリング |
| 「**段階的リリース**」 | カナリアデプロイ |
| 「**プライベートAPI**」 | Private エンドポイント + VPCエンドポイント |

---

## 関連

- [[0810_Cognito]] - 認証統合（Cognito Authorizer）
- [[0802_SQS]] - AWS Service統合で直接Put可能
- [[Lambda]] - 最も多い統合先
