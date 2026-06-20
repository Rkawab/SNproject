---
tags: [AWS, SAA, Lambda, Serverless, コンピューティング]
---

# AWS Lambda

> [!info] 一言でいうと
> **イベントが来たときだけ短時間のコードを実行するサーバーレスコンピューティング**。
> サーバーを起動し続けるのではなく、S3アップロード、API呼び出し、SQSメッセージ、EventBridgeのスケジュールなどをきっかけに関数を動かす。

> [!tip] たとえ
> 常駐の店員を雇うのではなく、注文が来た瞬間だけ作業員を呼ぶイメージ。
> ただし、呼ばれてから準備する時間（コールドスタート）が問題になることがある。

---

## 基本

| 観点 | 内容 |
|---|---|
| 実行単位 | 関数 |
| 主な入口 | API Gateway / S3イベント / SQS / SNS / EventBridge / DynamoDB Streams |
| 課金 | リクエスト数と実行時間 |
| 実行時間 | 1回の実行は最大15分 |
| 向く処理 | 短時間、イベント駆動、スパイク対応、サーバー管理を避けたい処理 |
| 向かない処理 | 長時間ジョブ、常時接続、OSやランタイムを細かく管理したい処理 |

> [!warning] SAAでのひっかけ
> 「サーバーレス」でも、**何でもLambdaが正解**ではない。
> 1回の処理が数十分以上、コンテナの実行環境を細かく使いたい、常時プロセスが必要、という文脈なら [[0904_ECS]] / Fargate や [[0703_AWS_Batch]] を疑う。

---

## 同時実行とコールドスタート

### 同時実行

同時実行数は、同時に処理中のLambda実行環境の数。

```
同時実行数 = 1秒あたりのリクエスト数 × 平均実行時間（秒）
```

例: 100 req/s のAPIで平均実行時間が0.5秒なら、必要な同時実行は約50。

### 予約済み同時実行

**特定の関数に同時実行枠を確保しつつ、最大値も制限する**設定。

| 使いどころ | 理由 |
|---|---|
| 重要な関数に枠を確保したい | 他の関数にアカウントの同時実行枠を食い尽くされにくい |
| DBなど下流サービスを守りたい | Lambdaが増えすぎてDB接続数を超えるのを防ぐ |
| 一時的に止めたい | 予約済み同時実行を0にするとスロットリングできる |

> [!warning] 予約済み同時実行はコールドスタート対策ではない
> 枠を「予約」するだけで、実行環境を事前に暖めるわけではない。
> コールドスタートを減らす主役は次の **プロビジョンド同時実行**。

### プロビジョンド同時実行

**実行環境を事前に初期化して待機させる**設定。

| 向く場面 | 理由 |
|---|---|
| ユーザー向けAPI | 初回遅延を避けたい |
| レイテンシ要件が厳しい | 安定した応答時間が必要 |
| コールドスタートが問題化している | 初期化済み環境を用意できる |

> [!tip] 覚え方
> - 予約済み同時実行 = 枠を確保し、最大数も縛る
> - プロビジョンド同時実行 = 起動済みの作業員を待機させる

---

## よくある構成

| 構成 | 何を解決するか |
|---|---|
| API Gateway + Lambda | HTTPS APIをサーバーレスに公開 |
| S3イベント + Lambda | 画像リサイズ、メタデータ抽出、軽いETL |
| SQS + Lambda | 非同期処理、スパイク吸収、リトライ |
| EventBridge + Lambda | スケジュール実行、イベントルーティング |
| DynamoDB Streams + Lambda | テーブル変更に反応した後続処理 |
| Lambda + RDS Proxy | Lambda急増時のDB接続数を抑える |

---

## SAA判断フロー

```
処理は短時間で終わる？
├── No → Fargate / ECS / AWS Batch
└── Yes
    ├── イベント発生時だけ動けばよい？ → Lambda
    ├── HTTPS APIとして公開したい？ → API Gateway + Lambda
    ├── DB接続が増えすぎる？ → RDS Proxyを追加
    └── コールドスタートが問題？ → プロビジョンド同時実行
```

---

## 関連

- [[0701_コンピューティングサービス一覧]]
- [[0702_Lambda・ECS・RDS・Beanstalk比較]]
- [[0809_API_Gateway]]
- [[0802_SQS]]
- [[0804_EventBridge]]
- [[0302_RDSProxy]]

## 参考

- [AWS Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [Configuring reserved concurrency for a function](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)
- [Configuring provisioned concurrency for a function](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html)
