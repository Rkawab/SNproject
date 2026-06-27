# Amazon EventBridge（旧 CloudWatch Events）

> [!info]
> AWSサービスやSaaSで発生した**イベント**を、**ルール**に基づいて適切な宛先へ振り分ける**サーバーレスのイベントバス**。イベント駆動アーキテクチャの中核。

## たとえ話：出来事を仕分ける賢い秘書

会社にいろんな「出来事（イベント）」が舞い込む。秘書（EventBridge）がその中身を見て、
「これは経理へ」「これは開発チームへ」とルールに従って適切な担当（Lambda等）へ渡す。
[[0803_SNS]] が“とりあえず全員に放送”なのに対し、EventBridge は**中身を見て条件分岐**できるのが違い。

## 仕組み

```
[イベントソース]            [イベントバス]        [ルール]            [ターゲット]
AWSサービス / SaaS / 自作  →  EventBridge  →  内容でフィルタ  →  Lambda / SQS / SNS / Step Functions ...
```

- **イベントバス**: イベントが流れる経路。デフォルト／カスタム／SaaS(パートナー)用がある
- **ルール**: イベントのJSONパターンにマッチしたものだけを宛先へ送る
- **ターゲット**: 20以上のAWSサービスに連携可能

## SNS との違い（SAA頻出）

| | [[0803_SNS]] | EventBridge |
|---|---|---|
| 方式 | 単純なPub/Sub一斉配信 | **ルールで内容フィルタリング** |
| レイテンシ | 低い（速い） | やや高い |
| 連携先 | AWS中心 | **多数のSaaS**・スケジュール・多彩なAWS |
| スループット | 非常に高い | 高い |
| ユースケース | ファンアウト通知 | イベント駆動の振り分け・SaaS連携 |

## 主な機能

- **スケジュール実行**: cron式で定期的にLambdaを起動（旧 CloudWatch Events の機能）
- **Schema Registry**: イベント構造をスキーマ管理
- **Pipes**: ソース→フィルタ→変換→ターゲットを直結（ポイントツーポイント連携）

## EventBridge Scheduler

**Amazon EventBridge Scheduler** は、cron式やrate式でAWSサービス/APIを指定時刻に呼び出すスケジューラ。旧来の EventBridge ルールのスケジュール機能より、スケジュールを大量に管理しやすく、タイムゾーン、1回限りの実行、柔軟な実行時間枠、リトライ/DLQ などを個別に設定できる。

> [!example] たとえ
> EventBridgeルールが「掲示板に貼った定期当番表」なら、EventBridge Schedulerは「各タスクごとにアラーム・再通知・失敗時の連絡先まで持つ予定管理アプリ」。

| 使いどころ | 例 |
|---|---|
| 定期バッチ起動 | 毎日2時にLambda、5分ごとにECSタスク |
| 1回限りの予約実行 | 指定日時にStep Functionsを開始 |
| コンテナジョブのcron移行 | EventBridge Scheduler → ECS RunTask / AWS Batch SubmitJob |

> [!tip] SAAひっかけ
> 「何かが起きたら処理」= EventBridgeのイベントルール。
> 「決まった時刻/間隔で処理」= EventBridge Scheduler。
> 長時間コンテナジョブなら Scheduler は起動係であり、実行本体は ECS/Fargate や AWS Batch。

## SAAポイント

- 「**サーバーレスのイベント駆動**」→ EventBridge
- 「**SaaSのイベント**（Zendesk, Datadog等）を起点に処理」→ EventBridge
- 「**定期的（cron）**にLambda/ECS/Batchを実行」→ EventBridge Scheduler
- 「イベントの**内容に応じて**異なる処理へ振り分け」→ EventBridge（SNSは不可）

## 関連

- [[0803_SNS]] / [[0802_SQS]] / [[0807_Step_Functions]]
- [[0801_アプリケーション統合サービス一覧]]
- [[1001_CloudWatch]]（旧称 CloudWatch Events 由来）
