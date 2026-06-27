# AWS Systems Manager (SSM)（SAA頻出 ★★★）

> [!info] 一言で
> **サーバー群（EC2/オンプレ）を遠隔で一元運用する万能ツール箱**。SAAでは特に Session Manager と Parameter Store が頻出。

## たとえ話
ビルの各部屋（=EC2）を見回らず、**管制室のデスクから全部屋を遠隔操作** できる仕組み。
鍵（SSHキー）を持ち歩かなくても、管制室から安全に各部屋へ入れる。

## 主要機能（名前と役割を押さえる）

| 機能 | 役割 | SAA重要度 |
|---|---|---|
| **Session Manager** | SSHキー・踏み台・インバウンドポート開放 **なし** でEC2にシェル接続 | ★★★ |
| **Parameter Store** | 設定値・パスワードを安全に保管（無料、KMS暗号化可） | ★★★ |
| **Patch Manager** | OS/ソフトのパッチ自動適用 | ★★ |
| **Run Command** | 多数のインスタンスへ一括コマンド実行 | ★★ |
| **State Manager** | 望ましい構成状態を維持 | ★ |
| **Automation** | 定型運用ワークフローの自動化 | ★ |
| **Inventory** | インストール済みソフト等の棚卸し | ★ |

前提：対象に **SSM Agent** が入っていて、IAMロールで権限が付与されていること（多くのAmazon Linux等はプリインストール）。

## SAA頻出ポイント
> [!tip] 出題パターン
> - 「**SSHキーや踏み台サーバーなし**で、セキュアにEC2へアクセスしたい」→ **Session Manager**
>   （ポート22を開けなくてよい＝攻撃面が減る。操作ログはCloudTrail/S3/CloudWatchに記録）
> - 「アプリの設定値やパスワードを安全に保存・参照」→ **Parameter Store**
> - 「数百台に一斉にパッチ適用／コマンド実行」→ **Patch Manager / Run Command**

## Parameter Store vs Secrets Manager（頻出の比較）
| | Parameter Store | Secrets Manager |
|---|---|---|
| コスト | 標準は無料 | 有料 |
| 自動ローテーション | なし | **あり**（RDS等と連携） |
| 用途 | 一般設定値＋簡易シークレット | 本格的なシークレット管理 |

> [!note] 「自動ローテーションが必要」なら **Secrets Manager**、「無料で済む設定値・簡易な秘密情報」なら **Parameter Store**。

## AWS Systems Manager Parameter Store

**AWS Systems Manager Parameter Store** は、アプリの設定値や簡易的な秘密情報を階層的に保存する機能。`/prod/db/host` のようなパスで管理でき、IAMで読み取り権限を細かく制御できる。

| パラメータ種別 | 内容 | SAAでの見方 |
|---|---|---|
| **String** | 平文の設定値 | DBホスト名、機能フラグなど |
| **StringList** | カンマ区切りの複数値 | サブネットID一覧など |
| **SecureString** | KMSで暗号化した値 | 簡易シークレット。ただし自動ローテーションは別途実装 |

> [!tip] ひっかけ
> 認証情報を「安全に保管」だけなら Parameter Store でも足りる場面がある。
> ただし「**定期的な自動ローテーション**」「RDS認証情報の管理」まで求めるなら [[1605_データ保護・暗号化|Secrets Manager]] が本命。

## Session Manager / EC2 Instance Connect Endpoint / Client VPN

プライベートサブネットのEC2へ入る選択肢として混同しやすい。

| 方法 | 何を提供するか | SAAでの判断 |
|---|---|---|
| **Session Manager** | SSM Agent経由のシェル接続。SSHポート・踏み台・鍵管理なし。ログ記録しやすい | 「SSHを開けない」「監査ログ」「踏み台なし」なら本命 |
| **EC2 Instance Connect Endpoint（EC2 Instance Connect エンドポイント）** | VPC内のエンドポイント経由でプライベートEC2へSSH接続 | 踏み台不要だが、SSH運用・鍵・OS側のログ管理は残る |
| **AWS Client VPN** | 利用者端末をVPCへVPN接続し、プライベートIPに到達可能にする | ネットワーク到達性の提供。各EC2へのSSH運用は別問題 |

> [!tip] ひっかけ
> 「接続できる」だけなら Client VPN や EC2 Instance Connect Endpoint でもよい。
> しかし「**インバウンドポートを開けず、鍵管理を避け、操作ログも記録**」まで揃うと Session Manager が選ばれる。

## 関連ノート
- [[1401_マネジメント・ガバナンスサービス一覧]]
- [[0101_EC2やVPCとは]]
- [[0405_ネットワークとコンテンツ配信]]
