# AWS AppSync

> [!info]
> マネージドな **GraphQL**（および Pub/Sub）API を構築するサービス。複数データソースをまとめ、**リアルタイム更新・オフライン同期**に強い。モバイル/Webアプリ向き。

## たとえ話：必要なデータだけ過不足なく出す総合受付

RESTだと「顧客API」「注文API」「在庫API」を別々に叩いて寄せ集める必要がある。
AppSync（GraphQL）なら**受付カウンターで「これとこれが欲しい」と一度頼むだけ**で、
裏側の複数データソースから必要分だけまとめて返してくれる。

## 特徴

- **GraphQL** スキーマでAPIを定義
- 複数データソースを統合: **DynamoDB / Lambda / RDS(Aurora) / OpenSearch / HTTP**
- **リアルタイム（Subscription）**: データ変更を購読クライアントへ即時プッシュ
- **オフライン同期**: モバイルでオフライン中の変更を再接続時に同期
- 認証は [[0810_Cognito]] / IAM / API キー / OIDC

## API Gateway との違い（SAA頻出）

| | [[0809_API_Gateway]] | AppSync |
|---|---|---|
| 方式 | REST / HTTP / WebSocket | **GraphQL** |
| データ取得 | エンドポイント単位 | **必要なフィールドだけ**1リクエストで |
| 強み | 汎用的なAPI管理 | リアルタイム同期・オフライン・複数ソース集約 |
| 主な用途 | 一般的なバックエンドAPI | モバイル/Webのデータ駆動アプリ |

## SAAポイント

- 「**GraphQL** のAPIを構築」→ AppSync
- 「モバイルアプリで**リアルタイム更新**・**オフライン同期**」→ AppSync
- 「複数データソースを**1つのAPIに集約**」→ AppSync
- 単純なREST API → [[0809_API_Gateway]]

## 関連

- [[0809_API_Gateway]] / [[0810_Cognito]] / [[0303_DynamoDB]]
- [[0801_アプリケーション統合サービス一覧]]
