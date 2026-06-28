# Elastic Beanstalk・CloudFormation・App Runner の違い（混同しやすいTOP3）

> [!info] 一言で
> 3つとも「AWSがリソースをまとめて自動で用意してくれる」ので混ざるが、**目的のレイヤーが違う**。
> CloudFormation だけは「実行環境」ではなく「**インフラの作り方を記述するツール**」で、1段レイヤーが違う。

## なぜ混同するのか
共通点は「リソースを自動でまとめて作ってくれる」こと。だが役割は別物。

| サービス | 一言で | レイヤー | マネージド度 |
|---|---|---|---|
| **CloudFormation** | インフラの**設計図**を書くと、その通り何でも建てる（IaC） | インフラ構築の**手段** | （手段なので別軸） |
| **Elastic Beanstalk** | Webアプリを置くと EC2 一式を自動構築（PaaS） | アプリの**実行環境** | 中（EC2が見える/触れる） |
| **App Runner** | コンテナ/ソースを置くだけで動く・自動スケール | アプリの**実行環境** | 高（インフラ不可視） |

> [!important] いちばん大事な気づき
> **CloudFormation だけ仲間外れ**。「実行環境」ではなく「作り方を記述するツール」。
> だから **Elastic Beanstalk は内部で CloudFormation を使って** EC2/ELB/ASG を建てている。
> 並列に比較するものではなく、レイヤーが1段違う。

## たとえ話（家）
- **CloudFormation = 設計図＋建設会社**
  自分で図面（YAML/JSON）を書く → その通りに何でも建てる（家でもビルでも倉庫でも）。
  「建てる手段」であって「住む家」ではない。図面を捨てる（スタック削除）と建物もまとめて解体。
- **Elastic Beanstalk = 建売住宅パッケージ**
  「Webアプリ用の家ください」で、土地・基礎・電気・水道（EC2 / ELB / Auto Scaling / CloudWatch）を標準セットで一式建ててくれる。
  入居後は自分で改装OK（**EC2にSSHして中身を触れる**）。裏では建設会社（CloudFormation）が動いている。
- **App Runner = サービスアパート（家具・管理付き）**
  スーツケース（**コンテナイメージ or ソースコードURL**）だけ持って入居。建物管理はノータッチ。
  混んだら勝手に部屋を増やす（**自動スケール**）。ただし**壁の中の配線（インフラ）は触れない/見えない**。

## SAA 判断フロー
```
何をしたい？
├─ インフラ全体をコードで管理・再現したい（アプリに限らず何でも）
│    → CloudFormation
├─ 既存のWebアプリ(Django/Flask等)を素早く動かしたい
│  ＋ OS/EC2にある程度アクセスは残したい
│    → Elastic Beanstalk
├─ コンテナ化済みのWeb API/アプリを、インフラ意識ゼロで動かし自動スケール
│    → App Runner
├─ イベント駆動・短時間処理・関数単位スケール
│    → Lambda
└─ コンテナを細かく制御したい（ネットワーク/サイドカー等）
     → ECS / EKS
```

> [!tip] ひっかけ対策の合言葉
> - 「**再現性・バージョン管理・複数環境を同じ構成で**」→ CloudFormation（IaC）
> - 「**EC2管理は減らしたいが完全サーバーレスは不要・既存Webアプリ**」→ Elastic Beanstalk
> - 「**コンテナをとにかく簡単に・インフラ見たくない**」→ App Runner
> - マネージド度（楽さ）：`EC2 < Beanstalk < App Runner < Lambda`（楽になるほど制御は減る）

## 補足：似た仲間との線引き
- **CloudFormation vs Terraform**：Terraformはマルチクラウド対応のサードパーティIaC。CloudFormationはAWS専用。
- **Beanstalk vs App Runner**：両方ともアプリ実行環境。Beanstalkは**EC2が見える**ぶん柔軟（OS設定・SSH可）。App Runnerは**コンテナ前提でインフラ完全隠蔽**、その代わり一番手軽。
- **App Runner vs ECS/Fargate**：App Runnerは「Web向けに振り切った超シンプル版」。細かいネットワーク制御やサイドカーが要るならECS/EKS。
- **App Runner vs Lambda**：App Runnerは常時起動のWebサービス向け。Lambdaはイベント駆動・短時間実行向け。

## 関連ノート
- [[0702_Lambda・ECS・RDS・Beanstalk比較]]
- [[0701_コンピューティングサービス一覧]]
- [[1402_CloudFormation]]
- [[0901_AWS_コンテナサービス概要]]
