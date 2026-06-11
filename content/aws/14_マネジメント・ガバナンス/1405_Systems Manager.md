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

## 関連ノート
- [[1401_マネジメント・ガバナンスサービス一覧]]
- [EC2やVPCとは](../01_EC2/01_EC2やVPCとは.md)
