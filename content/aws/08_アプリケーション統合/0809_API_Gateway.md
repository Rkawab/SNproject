# API Gateway

> [!info] 概要
> APIの**作成・公開・運用・保護**をフルマネージドで提供するサービス。外部からのHTTPリクエストを受け付け、Lambda / EC2 / ECS / 他AWSサービス / 外部HTTPに振り分ける「**APIの玄関口**」。サーバーレスアーキテクチャの中心的存在。

## そもそもAPI Gatewayとは

API Gatewayは、Webサイトやスマホアプリから来た依頼を受け付け、適切な処理先へ渡す**AWS管理の受付窓口**。

```text
スマホ・ブラウザ
   ↓ 「注文を登録して」
API Gateway     依頼を受け付けて振り分ける
   ↓
Lambda          実際の処理を行う
   ↓
DynamoDB        データを保存する
```

API Gateway自身は、通常は業務処理やデータ保存をしない。

- HTTPSでアクセスできるURLを公開する
- URLとHTTPメソッドに応じて処理先を振り分ける
- 必要に応じて認証、アクセス制限、記録を行う

```text
GET    /products  → 商品一覧を取得するLambda
POST   /orders    → 注文を登録するLambda
DELETE /orders/10 → 注文を削除するLambda
```

> [!note] 従来型Webアプリとの違い
> Djangoなどは、Webリクエストの受付と業務処理を1つのアプリが担当することが多い。
> サーバーレス構成では、**受付をAPI Gateway、処理をLambda**というように役割を分ける。

## たとえ話

**ホテルのフロントデスク**。
- 来館客（クライアント）の用件をすべてフロントで受け付ける
- 「予約」「ルームサービス」「会計」と適切な部署に取り次ぐ
- VIP判定（**認証**）、混雑時のお断り（**スロットリング**）、よくある質問の即答（**キャッシュ**）、館内ルール（**WAF**）、お客様の声記録（**ロギング**）もここで一括処理
- 裏で誰が働いているか（Lambda / EC2 / ECS）はお客様には見せない

---

## 最初に結論：REST APIとHTTP APIは何が違う？

> [!important] ここが最大の混乱ポイント
> **REST APIもHTTP APIも、HTTPで呼び出すRESTful APIを作るためのAPI Gateway製品**。
> 「REST方式かHTTP方式か」という通信方式の比較ではなく、AWSが用意した**高機能版と軽量版という2つの商品名**である。

```text
Amazon API Gateway
├─ REST API      高機能版。APIの細かな管理・制御まで行う
├─ HTTP API      軽量版。受けたリクエストを素早くバックエンドへ渡す
└─ WebSocket API 接続を維持して双方向通信する
```

一言で分けると次のとおり。

- **HTTP API**：API Gatewayを「シンプルな転送係」として使う
- **REST API**：転送に加えて「顧客別の利用管理・検査・キャッシュ・防御」まで任せる

## 同じ注文APIで比べる

どちらでも、次のAPIは作れる。

```text
スマホアプリ
   │ POST /orders
   ▼
API Gateway
   ▼
Lambda
   ▼
DynamoDB
```

### HTTP APIで作る場合

客から注文を受けた受付係が、注文票をほぼそのまま厨房のLambdaへ渡すイメージ。

- `/orders` をLambdaへ転送する
- JWTやIAMで利用者を認可する
- CORSを設定する
- アクセスログやメトリクスを記録する

これで足りるなら、**HTTP APIの方が簡単で低コスト**。

### REST APIで作る場合

受付係に加えて、会員管理、注文票の検査、整理券、作り置きまで備えた高機能な窓口。

- 顧客Aと顧客Bに別々のAPIキーを発行する
- 使用量プランで「Aは月1万回、Bは月10万回」と制限する
- 注文票の必須項目をLambdaへ渡す前に検証する
- 同じ問い合わせ結果をキャッシュする
- AWS WAFで不審なリクエストを遮断する
- カナリアリリースで新バージョンへ一部だけ流す

このような**API管理機能が必要だからREST APIを選ぶ**のであり、URLがREST風だから選ぶわけではない。

## 機能比較

| 判断軸 | REST API | HTTP API |
|---|---|---|
| 基本的なHTTPルーティング | 対応 | 対応 |
| Lambda・公開HTTPへの接続 | 対応 | 対応 |
| IAM認可 | 対応 | 対応 |
| Lambda Authorizer | 対応 | 対応 |
| JWT Authorizer | Lambda Authorizer等で実装 | **標準対応** |
| CORS設定 | 対応 | 対応・設定が簡単 |
| 自動デプロイ | 非対応 | **対応** |
| APIキー・使用量プラン | **対応** | 非対応 |
| 顧客ごとのレート制限 | **対応** | 非対応 |
| リクエスト検証 | **対応** | 非対応 |
| API Gateway内キャッシュ | **対応** | 非対応 |
| AWS WAF連携 | **対応** | 非対応 |
| Private APIエンドポイント | **対応** | 非対応 |
| Edge-Optimizedエンドポイント | **対応** | 非対応（Regionalのみ） |
| カナリアリリース | **対応** | 非対応 |
| X-Rayトレーシング | **対応** | 非対応 |
| 相対的な料金 | 高い | **安い** |

> [!note] 「HTTP APIには制限がない」わけではない
> API全体やルート単位のスロットリングは設定できる。HTTP APIにないのは、主に**APIキーと使用量プランを使った顧客別の利用管理**。

## 迷ったときの選び方

```text
APIキー・使用量プランが必要？ ── Yes → REST API
        │ No
キャッシュ・WAF・リクエスト検証・Private APIが必要？
        ├─ Yes → REST API
        └─ No  → HTTP APIを第一候補
```

> [!tip] 実務上の出発点
> 新規のLambda APIやHTTPバックエンドの公開なら、まずHTTP APIで要件を満たせるか確認する。
> 「REST APIの機能が必要」と分かった時点でREST APIを選ぶ。

## 名前に惑わされないための確認

| 誤解 | 正しい理解 |
|---|---|
| REST APIだけがREST設計に使える | **両方ともRESTful APIに使える** |
| HTTP APIだけがHTTP通信する | **両方ともHTTPリクエストを受ける** |
| REST APIが新しく、HTTP APIが古い | REST APIが先。HTTP APIは後発の軽量版 |
| HTTP APIは小規模専用 | 規模ではなく**必要な管理機能**で選ぶ |
| 高機能なREST APIを選べば無難 | 不要な機能のために料金と設定の複雑さが増える |

---

## サポートするAPIタイプ

| タイプ | 役割 | 主な用途 |
|---|---|---|
| **REST API** | HTTP受付 + 高度なAPI管理 | APIキー、キャッシュ、WAF、Private API等が必要 |
| **HTTP API** | 軽量なHTTP受付・転送 | Lambda API、既存HTTPサービスの公開、JWT認可 |
| **WebSocket API** | 接続を維持した双方向通信 | チャット、通知、ゲーム |

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

## エンドポイントの種類（REST API）

| 種類 | 特徴 |
|------|------|
| **Edge-Optimized**（デフォルト） | CloudFront経由でグローバル配信。海外ユーザー向け |
| **Regional** | 同一リージョン向け。自前のCloudFrontを前に置きたい場合 |
| **Private** | VPC内からのみアクセス可能。社内システム |

---

## 認証・認可

| 方式 | 用途 | 動作 |
|------|------|------|
| **IAM 認証** | AWSサービス間 / IAMユーザー | SigV4 署名でリクエスト |
| **Lambda Authorizer**（旧 Custom Authorizer） | 独自トークン・サードパーティ認証 | Lambda関数で検証ロジック実装 |
| **Cognito Authorizer** | アプリ利用者の認証 | [[0810_Cognito]] User Pools のJWTを検証 |
| **APIキー + 使用量プラン** | 顧客ごとのレート制限 | APIキーヘッダーで識別 |
| **Resource Policy** | IP制限・VPC制限・クロスアカウント制御 | リソースベースのIAM |

> [!warning] APIタイプによる違い
> APIキー・使用量プラン、Resource PolicyはREST APIで利用する。HTTP APIはJWT Authorizerを標準サポートしており、CognitoやOIDC/OAuth 2.0と組み合わせやすい。

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

### カナリアリリース（REST API）

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
| 「低コストでシンプルなLambda API」「JWT認可」 | **HTTP API** |
| 「APIキー・使用量プラン・キャッシュ・WAF・リクエスト検証」 | **REST API** |

---

## 関連

- [[0810_Cognito]] - 認証統合（Cognito Authorizer）
- [[0802_SQS]] - AWS Service統合で直接Put可能
- [[Lambda]] - 最も多い統合先

## 公式資料

- [Choose between REST APIs and HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)
- [API Gateway HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
- [Amazon API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/)
