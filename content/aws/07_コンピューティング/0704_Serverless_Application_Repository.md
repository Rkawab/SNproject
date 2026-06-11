# AWS Serverless Application Repository (SAR)

## 概要

**サーバーレスアプリの「App Store」**。
Lambda・API Gateway・DynamoDBなどを組み合わせたサーバーレスアプリのセットを、ワンクリックでAWSアカウントにデプロイできるマネージドリポジトリ。

> [!info] たとえ話
> スマートフォンの App Store / Google Play と同じイメージ。
> 他の人が作ったアプリ（サーバーレス構成セット）を簡単にインストール（デプロイ）できる。

---

## できること

| 機能 | 内容 |
|------|------|
| 公開アプリを使う | AWSや他の開発者が作ったサーバーレスアプリを自分のアカウントにデプロイ |
| 自分のアプリを公開 | 自作のサーバーレスアプリをリポジトリに登録・公開 |
| 非公開共有 | 組織内（同一AWS organizationや特定アカウント）にだけ共有 |

---

## 仕組み

```
SAR リポジトリ
    │
    ├── サムネイル変換アプリ（Lambda + S3）
    ├── 認証フロー（Lambda + Cognito）
    ├── チャットボット（Lambda + API Gateway）
    └── ...
         │
         ▼ ワンクリック or CloudFormation でデプロイ
    自分のAWSアカウント
```

### 内部技術：SAMテンプレート

SARは内部的に **SAM（Serverless Application Model）テンプレート** を使用。
SAM = CloudFormationを拡張した、サーバーレス専用のIaCテンプレート形式。

```yaml
# SAM template.yaml のイメージ
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: python3.12
      Events:
        Api:
          Type: Api
          Properties:
            Path: /hello
            Method: get
```

---

## 公開範囲の設定

- **パブリック**：誰でも検索・デプロイ可能
- **プライベート（アカウント指定）**：特定のAWSアカウントのみ共有
- **組織内共有（AWS Organizations）**：同一Organization内のアカウントのみ共有

---

## よくあるユースケース

1. **画像リサイズ Lambda** → S3にアップした画像を自動でサムネイル化
2. **Cognitoカスタム認証フロー** → ユーザー認証をカスタマイズ
3. **CloudWatch Logs → Slack 転送** → アラートの自動通知

---

## SAA試験対策ポイント

> [!warning] 試験頻出
> - SARは **Lambda/サーバーレスアプリのテンプレート共有サービス**
> - 内部は **SAM（CloudFormation拡張）テンプレート**
> - **公開・非公開・組織内共有** の3段階の公開範囲設定が可能
> - **再利用・標準化** のシナリオで登場することが多い
> - Lambda単体ではなく**複数AWSサービスの組み合わせ**をまとめてデプロイできる点が特徴

---

## 関連ノート

- [[0701_コンピューティングサービス一覧]]
- [[0703_AWS_Batch]]
- [[0705_AWS_Outposts]]
