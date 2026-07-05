---
tags: [AWS, SAA, データベース, Keyspaces, Timestream, MemoryDB]
---

# Keyspaces・Timestream・MemoryDB（残りの専用DB3種）

> [!info] このノートの位置づけ
> `03_データベース` の他ノート（[[0301_RDS]] / [[0303_DynamoDB]] / [[0304_ElastiCache]] / [[0305_Neptune]] / [[0306_QLDB]] / [[0307_Aurora詳細]] / [[0308_DocumentDB]]）でカバーしていない**残りの専用データベース3つ**をまとめる。
> いずれも出題頻度は低めで、**選択肢に出たとき「何者か」を即答できれば十分**（Keyspaces と Timestream は SAA-C03 公式の試験範囲リストに掲載あり。MemoryDB はリスト外だが誤答選択肢としてよく登場する）。

## 3つの正体（ここだけ覚えれば切れる）

| サービス | 一言で | 反射キーワード |
|---|---|---|
| **Amazon Keyspaces** | **Apache Cassandra 互換**のサーバーレスNoSQL | 「Cassandra」 |
| **Amazon Timestream** | **時系列データ専用**のサーバーレスDB | 「時系列」「IoTセンサーの計測値」「メトリクス」 |
| **Amazon MemoryDB** | **Redis互換**なのに**データが消えない**インメモリDB | 「Redis互換＋耐久性」「インメモリをプライマリDBに」 |

> [!tip] たとえ話：DB商店街の専門店
> AWSのDBは「汎用スーパー（RDS）」だけでなく専門店が並ぶ商店街。
> - **Keyspaces**＝「Cassandraブランド専門店」。今までCassandraを自前運用していた客が、**買い物リスト（アプリのコード）をそのまま**持ち込める。
> - **Timestream**＝「時刻表専門の記録所」。センサーの計測値のように「**いつ・いくつ**」が延々続くデータを、時刻順に安く速く捌くことだけに特化。
> - **MemoryDB**＝「金庫付きの超高速カウンター」。ElastiCache（Redis）と同じ速さなのに、**裏で金庫（マルチAZのトランザクションログ）に控えを取る**ので停電してもデータが消えない。

---

## Amazon Keyspaces (for Apache Cassandra)

- **Apache Cassandra 互換**のフルマネージド・サーバーレスNoSQL。CQL（Cassandra Query Language）や既存のCassandraドライバが**そのまま使える**
- サーバーレス（キャパシティのオンデマンド/プロビジョンドはDynamoDBと同じ考え方）、マルチAZで高可用
- **選ばれる条件は1つだけ**：「既存の**Cassandra**ワークロードを、**アプリを書き換えずに**AWSへ移行したい」

> [!warning] DynamoDBとの引っかけ
> 「NoSQLだから」でDynamoDBを選ばせる誤答が定番。**問題文に「Cassandra」の一語があればKeyspaces**、なければNoSQLの定番はDynamoDB。

## Amazon Timestream

- **時系列（time series）データ専用**のフルマネージド・サーバーレスDB
- IoTセンサーのテレメトリ・アプリのメトリクス・産業機器のログなど「**タイムスタンプ＋値**」が大量に流れ込むデータ向け
- 直近データはメモリ層・古いデータは磁気層へ**自動で階層化**して低コスト化。SQLライクなクエリで時系列分析（移動平均・補間など）ができる
- 典型構成：**IoT Core / Kinesis → Timestream → Grafana / QuickSight で可視化**

> [!warning] 代用させる引っかけ
> - **DynamoDB＋TTL**でも時系列っぽいことはできるが、「時系列分析クエリ」「自動階層化」が要件なら**Timestream**
> - **Kinesis**は「流すための土管」であって保存・分析する場所ではない（輸送 vs 保管の役割違い）

## Amazon MemoryDB（旧称：MemoryDB for Redis）

- **Redis互換のインメモリDB**。ここまでは ElastiCache for Redis と同じ
- 違いは**耐久性**：書き込みを**マルチAZのトランザクションログ**に記録するため、ノード障害・再起動でも**データを失わない**（＝キャッシュではなく**プライマリDBとして使える**）
- マイクロ秒の読み取り・1桁ミリ秒の書き込み

| 観点 | **ElastiCache for Redis** | **MemoryDB** |
|---|---|---|
| 役割 | **キャッシュ**（DBの前座。裏に本物のDBがいる前提） | **プライマリDB**（これ自体が本体） |
| 耐久性 | 揮発前提（スナップショットはあるが消えうる） | **マルチAZトランザクションログで耐久** |
| 反射キーワード | 「DBの読み取り負荷を下げる」「セッションキャッシュ」 | 「Redis互換」＋「**データ損失が許されない**」 |

---

## SAA試験ポイント

| 問題文のキーワード | 答え |
|---|---|
| 「Cassandraワークロードを書き換えずAWSへ」 | **Keyspaces** |
| 「IoTセンサーの時系列データを保存・分析」 | **Timestream** |
| 「Redis互換で超高速、かつデータを失えない（プライマリDB）」 | **MemoryDB** |
| 「Cassandraの指定なし・NoSQLでスケール」 | DynamoDB（[[0303_DynamoDB]]） |
| 「既存DBの前段キャッシュ」 | ElastiCache（[[0304_ElastiCache]]） |

> [!note] 覚え方：互換シリーズで整理
> 「**○○互換のマネージドDB**」ファミリーとして束ねると忘れない。
> MongoDB互換→**DocumentDB** ／ Cassandra互換→**Keyspaces** ／ Redis互換（耐久あり）→**MemoryDB**

## 関連ノート

- [[0303_DynamoDB]]（Cassandra指定がないNoSQLの定番）
- [[0304_ElastiCache]]（MemoryDBとの対比：キャッシュ vs プライマリ）
- [[0308_DocumentDB]]（互換シリーズの仲間：MongoDB互換）
- [[3001_サービス早見表（キーワードで引く）]]
