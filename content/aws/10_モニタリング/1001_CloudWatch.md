---
tags: [AWS, モニタリング, CloudWatch, SAA]
---

# CloudWatch（AWS監視の司令塔）

## TL;DR

> [!info] ひとことで
> **CloudWatch = AWSの「集中監視室」**。あらゆるAWSリソースの状態（メトリクス・ログ・イベント）を集め、可視化し、異常時にアラートを鳴らす。

---

## たとえ話：病院のナースステーション

CloudWatchは大病院のナースステーション（中央監視室）に近い。

| 病院での役割 | CloudWatchで対応するもの |
| --- | --- |
| 各病室の心拍数・血圧モニター | **CloudWatch Metrics**（CPU使用率・NW通信量等） |
| 看護師が書く日誌・カルテ | **CloudWatch Logs**（アプリ・OSログ） |
| 「血圧180超えたらアラーム鳴らせ」設定 | **CloudWatch Alarms** |
| ナースが見ている大型表示パネル | **CloudWatch Dashboards** |
| アラーム鳴ったら自動で当直医を呼ぶ | **EventBridge → SNS/Lambda連携** |
| 院内に置く血糖値測定器（自前計測） | **CloudWatch Agent**（OS内部メトリクス取得） |

つまりCloudWatchは「**集める→見える化する→異常を検知する→自動対応につなぐ**」の一連を担う。

---

## CloudWatchの4大構成要素

### 1. Metrics（メトリクス）

数値データの時系列収集。

- **標準メトリクス**：EC2のCPU使用率、ネットワーク通信量、ディスクI/O、ELBのリクエスト数…AWS側が自動で出してくれる
- **カスタムメトリクス**：自分でPutMetricData APIで送るやつ（アプリ独自の値）
- **EC2のメモリ使用率・ディスク空き容量は標準メトリクスに含まれない** ← SAA頻出ポイント
  - これらを取りたい場合は **CloudWatch Agent** をEC2にインストールする必要がある

> [!warning] よくある誤解
> 「EC2のCPUは見えるからメモリも見えるはず」→ ❌ メモリはハイパーバイザーから見えないので**Agent必須**

#### 基本モニタリング vs 詳細モニタリング

| 種別 | 取得間隔 | 料金 |
| --- | --- | --- |
| 基本モニタリング（デフォルト） | **5分** | 無料 |
| 詳細モニタリング | **1分** | 有料 |
| 高解像度カスタムメトリクス | 最小**1秒** | 有料 |

### 2. Logs（ログ）

各種ログを集約・検索・保存。

- **ロググループ** > **ログストリーム** > ログイベント の階層
- 取り込み方法
  - **CloudWatch Agent**（EC2/オンプレ）
  - **Lambda**は自動でログ送信
  - **VPC Flow Logs**、**ALBアクセスログ**、**Route53クエリログ**等もここへ
- **Logs Insights**でSQLライクなクエリ検索可能
- **メトリクスフィルター**：ログから「ERROR」を数えてメトリクス化 → アラーム可能

### CloudWatch Logs Insights

**CloudWatch Logs Insights** は、CloudWatch Logsに保存されたログを必要なタイミングでクエリ検索・集計する機能。SQLそのものではないが、`filter` / `stats` / `sort` / `limit` のような専用クエリで、エラー件数や特定ユーザーの操作などを調べられる。

| 向いていること | 向いていないこと |
|---|---|
| 直近のアプリログ・Lambdaログをその場で調査 | 長期保管した大量ログの安価な分析 |
| CloudWatch Logsに既に集約されたログの検索 | S3上のログを直接SQL分析 |
| 一時的なトラブルシュート | BI用途のダッシュボード分析 |

> [!tip] SAAひっかけ
> CloudTrailログをS3に長期保管し、たまにSQLで調べるなら [[1109_Amazon Athena]]。
> CloudWatch Logsに流れているログを運用担当が即時調査するなら **CloudWatch Logs Insights**。

### 3. Alarms（アラーム）

メトリクスが閾値を超えたら通知・アクションを起動。

- 状態：`OK` / `ALARM` / `INSUFFICIENT_DATA`
- アクション例：
  - **SNS**通知（メール・SMS）
  - **Auto Scaling**のスケールアウト/イン
  - **EC2自動復旧**（StatusCheckFailed_System連動）
  - **Lambda関数**起動

> [!note] VPNトンネル監視
> AWS Site-to-Site VPN のトンネル状態は CloudWatch メトリクス（例：`TunnelState`）で監視し、CloudWatch Alarm からSNS通知できる。
> AWS Configは設定準拠や変更履歴を見るサービスで、VPNトンネルのUP/DOWNをアラームする主役ではない。

> [!tip] 複合アラーム（Composite Alarm）
> 複数アラームをAND/ORで組み合わせ。誤検知を減らせる。

### 4. Dashboards（ダッシュボード）

複数メトリクス・ログを1画面に並べて可視化。クロスリージョン・クロスアカウント表示も可能。

---

## CloudWatch Agent（重要）

EC2やオンプレサーバの**内部情報**を取るための常駐エージェント。

| 取れるもの | デフォルト標準メトリクス |
| --- | --- |
| メモリ使用率 | ❌（Agent必須） |
| ディスク使用率（OS視点） | ❌（Agent必須） |
| スワップ使用率 | ❌（Agent必須） |
| プロセス数 | ❌（Agent必須） |
| CPU使用率 | ✅ |
| ネットワーク I/O | ✅ |
| ディスク I/O（EBS視点） | ✅ |

**SSM Parameter Store** に設定ファイルを置いて配布する運用がベストプラクティス。

---

## イベント駆動：EventBridge（旧CloudWatch Events）

> [!note] 名前の変遷
> CloudWatch Events → **Amazon EventBridge** に名称変更（機能上位互換）。SAAでは両方の名前が出る。

- AWSサービスの状態変化を**イベント**として受け取り、ルールで振り分け
  - 例：「EC2がterminatedになったらSlack通知」「毎朝9時にLambda起動（cron）」
- **スケジュールルール（cron式）** と **イベントパターン** の2系統
- 連携先：Lambda / SNS / SQS / Step Functions / ECSタスク 等

---

## 関連サービスとの使い分け（SAA頻出）

| サービス | 役割 | たとえ |
| --- | --- | --- |
| **CloudWatch** | パフォーマンス・運用監視 | 病院のモニター類 |
| **CloudTrail** | API呼び出しの**監査ログ**（誰が何をしたか） | 出入り口の防犯カメラ |
| **AWS Config** | リソース構成変更の追跡・コンプラ評価 | 院内設備の点検記録 |
| **X-Ray** | 分散アプリのトレーシング（どこで遅いか） | 患者の検査経路追跡 |
| **VPC Flow Logs** | VPC内NW通信のログ | 院内通路の人流計測 |

> [!warning] CloudWatch vs CloudTrail（試験頻出）
> - 「ユーザーAがいつEC2を停止したかを調べたい」→ **CloudTrail**
> - 「停止前のCPU使用率を調べたい」→ **CloudWatch**

---

## ログ・メトリクスの保持期間

| データ | デフォルト保持 |
| --- | --- |
| メトリクス（高解像度1秒） | 3時間 |
| メトリクス（1分） | 15日 |
| メトリクス（5分） | 63日 |
| メトリクス（1時間） | **15ヶ月** |
| Logs | **デフォルトは無期限**（ロググループごとに保持期間設定推奨） |

> [!tip] コスト最適化
> Logsの長期保管はS3エクスポート or S3 + Glacierが定石。CloudWatch Logsに置きっぱなしは高くつく。

---

## SAA頻出シナリオ集

### ① EC2のメモリ監視
**答え**：CloudWatch Agentを導入してカスタムメトリクスとして送信

### ② オンプレサーバも監視したい
**答え**：CloudWatch Agent はオンプレでも動く。IAMロール代わりにIAMユーザの認証情報を使用

### ③ ALBのレスポンスタイムが遅延した時に自動通知
**答え**：CloudWatch Alarm（TargetResponseTime）→ SNSトピック→メール/Slack

### ④ Lambdaの異常を検知して自動再実行
**答え**：CloudWatch Alarm or EventBridgeルール → Lambda or Step Functions

### ⑤ 複数アカウントの監視を1か所に集約
**答え**：**Cross-account Observability**機能（モニタリングアカウントに集約）

### ⑥ コンテナ監視
**答え**：**Container Insights**（ECS/EKS用の特化機能）

### ⑦ アプリ性能の詳細監視
**答え**：**Application Insights** + X-Ray

---

## 料金の勘所

- **メトリクス**：標準は無料、カスタム・詳細・高解像度は有料
- **Logs**：取り込みGB単位 + 保管GB単位の二重課金
- **ダッシュボード**：3つまで無料、それ以上は有料
- **アラーム**：10個まで無料

> [!info] コスト爆発しやすいポイント
> Lambdaが大量にログを吐く / VPC Flow Logsを全VPCで有効化 / アプリがINFOログを大量出力 → 月数万円コース

---

## 関連ノート

- [[0601_IAM基礎]]（CloudWatch Agentに必要なIAMロール）
- [[0904_ECS]]（Container Insights連携）
- [[0101_EC2やVPCとは]]
- [[0502_Elastic Load Balancing]]（ALBメトリクス）

---

## まとめ図

```
┌─────────── AWS環境 ───────────┐
│  EC2 / RDS / Lambda / ELB ... │
│       │ メトリクス・ログ           │
│       ▼                           │
│  ┌─ CloudWatch ──────────────┐  │
│  │ Metrics  Logs  Events     │  │
│  │   │        │      │       │  │
│  │   ▼        ▼      ▼       │  │
│  │  Alarms  Insights  Rules  │  │
│  └────────┬─────────┬────────┘  │
│           ▼         ▼            │
│         SNS      Lambda          │
│       (通知)   (自動対応)         │
└──────────────────────────────────┘
```
