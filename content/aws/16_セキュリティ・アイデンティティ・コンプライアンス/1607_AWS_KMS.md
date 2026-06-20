---
tags: [AWS, SAA, KMS, 暗号化, セキュリティ]
---

# AWS KMS

> [!info] 一言でいうと
> **暗号化に使う鍵を作成・管理・監査するマネージドサービス**。
> S3、EBS、RDS、DynamoDBなどの保存時暗号化で頻出する。

> [!tip] たとえ
> データそのものをしまう倉庫ではなく、倉庫を開ける「鍵」を管理する金庫。
> Secrets Managerが「パスワード保管箱」なら、KMSは「暗号鍵の金庫」。

---

## KMSで何ができるか

| 機能 | 内容 |
|---|---|
| 鍵の作成・管理 | KMSキーを作成し、無効化、ローテーション、削除予定設定などを管理 |
| アクセス制御 | キーポリシー、IAMポリシー、グラントで利用者を制御 |
| AWSサービス連携 | S3 / EBS / RDS / DynamoDBなどの保存時暗号化に利用 |
| 監査 | KMS APIの呼び出しをCloudTrailで追跡 |
| マルチリージョンキー | 別リージョンに関連キーを複製し、DRやグローバル構成に使う |

> [!warning] KMSは秘密情報そのものを管理するサービスではない
> DBパスワードやAPIキーを保存して自動ローテーションしたいなら [[1605_データ保護・暗号化]] の Secrets Manager。
> KMSはその秘密情報やデータを暗号化するための「鍵」を管理する。

---

## KMSキーの種類

| 種類 | 管理者 | 見える/制御できる範囲 | SAAでの使いどころ |
|---|---|---|---|
| Customer managed key | 利用者 | キーポリシー、ローテーション、削除、タグ、エイリアスなどを制御 | 鍵の利用者・監査・ローテーションを自分で管理したい |
| AWS managed key | AWSサービス | メタデータは見えるが、権限やライフサイクルは原則管理しない | 手軽にサービス側暗号化を使いたい |
| AWS owned key | AWSサービス | 利用者アカウントからは見えない | デフォルト暗号化など、最も運用負荷を下げたい |

> [!tip] SAAキーワード
> 「企業が鍵を管理」「キーポリシー」「CloudTrailで鍵利用を監査」「自動ローテーション」→ Customer managed key。

---

## キーポリシー・IAM・グラント

| 制御 | 役割 |
|---|---|
| キーポリシー | KMSキーに必ず1つ付くリソースポリシー。KMSでは最重要 |
| IAMポリシー | ユーザーやロール側の権限。キーポリシーで許可されていないと効かないことがある |
| グラント | 一時的・限定的な利用許可。AWSサービス連携で使われることがある |

> [!warning] KMS権限は「IAMだけ」では不足することがある
> KMSキーを使うには、IAM権限に加えてキーポリシー側でも利用を許可する設計を意識する。

---

## S3暗号化での見分け

| 方式 | 鍵の管理 | 向く場面 |
|---|---|---|
| SSE-S3 | S3側の管理キー | とにかく簡単に保存時暗号化したい |
| SSE-KMS（AWS managed key） | AWS管理のKMSキー | KMS統合は使いたいが、鍵管理は簡素化したい |
| SSE-KMS（Customer managed key） | 利用者管理のKMSキー | 鍵ポリシー、監査、ローテーション、権限制御を重視 |
| SSE-C | 顧客提供キー | AWSに鍵を保管させたくない特殊要件 |

---

## SAA判断フロー

```
守りたいものは何？
├── TLS証明書 → ACM
├── DBパスワード/APIキー → Secrets Manager / Parameter Store
└── 暗号化キー
    ├── AWSにおまかせでよい → AWS owned key / AWS managed key
    ├── 鍵ポリシー・監査・ローテーションを制御したい → Customer managed key
    ├── 専有HSMや厳格な鍵管理が必要 → CloudHSM
    └── リージョン間DRで同じ鍵ID体系が必要 → マルチリージョンキー
```

---

## 関連

- [[1605_データ保護・暗号化]]
- [[0207_S3の暗号化]]
- [[1002_CloudTrail]]
- [[0301_RDS]]

## 参考

- [AWS KMS keys](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html)
- [Key policies in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [Logging AWS KMS API calls with AWS CloudTrail](https://docs.aws.amazon.com/kms/latest/developerguide/logging-using-cloudtrail.html)
