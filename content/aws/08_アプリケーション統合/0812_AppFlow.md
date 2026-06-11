# Amazon AppFlow

> [!info]
> **SaaSアプリ ↔ AWS** 間のデータ転送を**コードなし（ノーコード）**で実現するフルマネージド統合サービス。

## たとえ話：他社サービスとAWSをつなぐ自動定期便

Salesforceの顧客データを毎朝S3に取り込みたい——
本来はAPI連携プログラムを書く必要があるが、AppFlowなら
**画面でポチポチ設定するだけ**で「定期便（フロー）」が走り、データを運んでくれる。

## 特徴

- 連携できるSaaS例: **Salesforce / SAP / Slack / ServiceNow / Zendesk / Google Analytics / Marketo** 等
- AWS側の宛先: **S3 / Redshift** など
- **双方向**転送可能（SaaS→AWS、AWS→SaaS）
- 転送時に**フィルタ・変換・マッピング・検証**ができる
- **スケジュール実行**／イベント駆動／オンデマンド

## 似たサービスとの違い

| サービス | 役割 |
|---|---|
| **AppFlow** | SaaS↔AWSの**データ転送**（ノーコード） |
| [[1107_AWS Glue]] | AWS内のデータの**ETL**（抽出・変換・ロード） |
| [[0804_EventBridge]] | SaaSの**イベント**を起点に処理を起動 |

## SAAポイント

- 「**SaaS**（Salesforce等）のデータを**コードを書かず**にS3/Redshiftへ」→ AppFlow
- 「SaaSとAWS間を**定期的に**データ同期」→ AppFlow

## 関連

- [[0804_EventBridge]]（SaaSイベント連携）/ [[1107_AWS Glue]]（ETL）
- [[0801_アプリケーション統合サービス一覧]]
