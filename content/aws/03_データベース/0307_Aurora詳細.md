---
tags: [AWS, SAA, RDS, Aurora, Database]
---

# Aurora詳細

> [!info] 一言でいうと
> **MySQL / PostgreSQL互換の、AWSクラウド向けに作られた高性能リレーショナルDB**。
> SAAでは「RDSの一種」ではあるが、通常のRDSより高可用・高性能・グローバルDRの文脈で別格扱いされる。

> [!tip] たとえ
> RDSが「運転手付きの普通車」なら、Auroraは「AWS専用道路に最適化された高性能車」。
> SQLの使い方は似ているが、ストレージやレプリケーションの仕組みがクラウド向けに強い。

---

## Auroraの基本

| 観点 | 内容 |
|---|---|
| 互換性 | MySQL / PostgreSQL互換 |
| ストレージ | 自動拡張。複数AZにまたがって冗長化 |
| 可用性 | 障害時の高速フェイルオーバーが強み |
| 読み取り | AuroraレプリカとReaderエンドポイントで分散 |
| 向く用途 | 高性能RDB、読み取り急増、高可用性、グローバル読み取り |

> [!warning] DynamoDBとの違い
> AuroraはリレーショナルDB。SQL、トランザクション、既存RDB互換が必要なとき。
> DynamoDBはNoSQL。キーアクセス中心で、超スケール・サーバーレス寄りのとき。

---

## Aurora Serverless

**負荷に応じてDB容量を自動で増減するAuroraの利用形態**。

| 向く場面 | 理由 |
|---|---|
| 開発・検証環境 | 使わない時間のコストを抑えやすい |
| 断続的なワークロード | 負荷がない時間と急な負荷の差が大きい |
| 予測しづらい負荷 | 容量計画の負担を下げられる |

> [!tip] SAAキーワード
> 「利用されない時間が長い」「断続的」「予測困難」「アイドル時のコストを抑えたい」→ Aurora Serverless を疑う。

---

## Aurora Global Database

**複数リージョンにまたがるAurora構成**。

| 観点 | 内容 |
|---|---|
| 書き込み | プライマリリージョンに書き込む |
| 読み取り | セカンダリリージョンは読み取り用に使える |
| レプリケーション | Aurora専用インフラでリージョン間に低遅延複製 |
| 主目的 | グローバル読み取り、リージョン障害へのDR |
| 障害対応 | セカンダリを昇格して別リージョンで再開 |

> [!tip] RPO / RTO
> - **RPO** = 障害時に失ってよいデータ量を「時間」で表す。Aurora Global Databaseでは通常、秒単位を狙う。
> - **RTO** = 障害後に復旧するまでの時間。Aurora Global Databaseでは分単位の復旧を狙う。

### Multi-AZ / リードレプリカ / Global Database の違い

| 機能 | 主目的 | 範囲 | 読み取り分散 | 障害対策 |
|---|---|---|---|---|
| Multi-AZ | 高可用性 | 同一リージョン内のAZ | 原則しない | AZ障害 |
| リードレプリカ | 読み取りスケール | 同一/別リージョン | する | 手動昇格で補助的 |
| Aurora Global Database | グローバル読み取り・リージョンDR | 複数リージョン | する | リージョン障害 |

---

## SAA判断フロー

```
リレーショナルDBが必要？
├── No → DynamoDB / Redshift / Athena など
└── Yes
    ├── 標準的なマネージドRDBで十分？ → RDS
    ├── 高性能・高速フェイルオーバー・多数レプリカ？ → Aurora
    ├── 断続的でアイドル時コストを下げたい？ → Aurora Serverless
    ├── 読み取り急増？ → Auroraレプリカ + Readerエンドポイント
    └── リージョン障害DR・グローバル読み取り？ → Aurora Global Database
```

---

## 関連

- [[0301_RDS]]
- [[0302_RDSProxy]]
- [[0303_DynamoDB]]
- [[1113_Amazon Redshift]]

## 参考

- [Using Amazon Aurora Global Database](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database.html)
- [Using switchover or failover in Amazon Aurora Global Database](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-global-database-disaster-recovery.html)
