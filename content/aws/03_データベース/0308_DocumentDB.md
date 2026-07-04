---
tags: [AWS, SAA, Database, DocumentDB, MongoDB]
---

# Amazon DocumentDB

> [!info] 一言でいうと
> **MongoDB互換APIで使える、AWSフルマネージドのドキュメントデータベース**。
> JSONのような柔軟なデータを保存したいが、MongoDBサーバーの運用・バックアップ・冗長化はAWSに任せたいときに使う。

> [!tip] たとえ
> RDSが「きっちり列が決まったExcel表」、DynamoDBが「超高速なキー付きロッカー」なら、DocumentDBは「書類フォルダ」。
> ユーザーごとに持っている項目が少し違っても、1つのドキュメントとしてまとめて保管しやすい。

---

## ドキュメントDBとは

RDBのように「行・列」を固定するのではなく、JSON形式に近い**ドキュメント**単位でデータを保存するDB。

```json
{
  "userId": "u-001",
  "name": "Taro",
  "profile": {
    "age": 32,
    "city": "Yokohama"
  },
  "favoriteServices": ["EC2", "S3", "DynamoDB"]
}
```

| RDB | DocumentDB |
|---|---|
| テーブル | コレクション |
| 行 | ドキュメント |
| 列 | フィールド |
| SQL | MongoDB互換API |

> [!warning] MongoDBそのものではない
> DocumentDBは「MongoDB互換」だが、MongoDBの全機能が完全に同じ挙動で使えるという意味ではない。
> 実案件では、使う演算子・API・バージョン互換性を公式ドキュメントで確認する。
> 2026-07-02時点の公式ドキュメントでは、MongoDB 3.6 / 4.0 / 5.0 / 8.0 互換と記載されている。

---

## 基本構成

DocumentDBは、Auroraに似た「コンピュートとストレージを分離したクラスター構成」になっている。

```text
アプリ
  |
  | 書き込み・強い整合性の読み取り
  v
[プライマリインスタンス]
  |
  | 共有ストレージ
  v
[クラスターVolume: 3AZに6コピー]
  ^
  |
[リードレプリカ] [リードレプリカ] ... 最大15台
```

| 要素 | 役割 |
|---|---|
| クラスター | DocumentDB全体のまとまり |
| クラスターVolume | データを保持する共有ストレージ。最大128TiBまで自動拡張 |
| プライマリインスタンス | 書き込みを担当。読み取りも可能 |
| レプリカインスタンス | 読み取り専用。最大15台まで追加でき、フェイルオーバー先にもなる |
| クラスターエンドポイント | 現在のプライマリへ接続するエンドポイント |
| リーダーエンドポイント | 読み取りをレプリカへ分散するためのエンドポイント |

---

## 可用性・バックアップ

| 機能 | 内容 |
|---|---|
| ストレージ冗長化 | 3つのAZに6コピーを自動保持 |
| 自動フェイルオーバー | プライマリ障害時、別AZのレプリカを昇格 |
| ストレージ自動拡張 | 10GB単位で最大128TiBまで増える |
| 自動バックアップ | 継続的・増分バックアップ。保持期間は最大35日 |
| PITR | 保持期間内で、直近5分前までの秒単位復元に対応 |
| 暗号化 | KMSによる保存時暗号化、TLSによる転送時暗号化 |
| VPC配置 | VPC内に配置し、セキュリティグループでアクセス制御 |

> [!tip] SAAの感覚
> 「MongoDB互換」だけでなく、**マネージド運用・Multi-AZ・自動バックアップ・レプリカ**までセットで覚える。
> 試験では「MongoDBアプリをAWSへ移行したい」「JSONドキュメントを扱いたい」が入口になりやすい。

---

## 読み書きと整合性

| 操作 | 接続先 | 整合性 |
|---|---|---|
| 書き込み | プライマリ | Durable write。書き込みはプライマリのみ |
| プライマリ読み取り | プライマリ | 通常はRead-after-write整合性 |
| レプリカ読み取り | レプリカ | 結果整合性。通常レプリカ遅延は小さいがゼロではない |

読み取りを増やしたい場合は、レプリカを追加して読み取りを分散する。
「書いた直後に必ず最新を読みたい」処理は、プライマリへ読みに行く設計にする。

---

## Elastic Clusters

通常のDocumentDBクラスターは、1つのプライマリと複数レプリカで構成する。
より大きな読み書きスケールが必要な場合は、**Elastic clusters** を使う選択肢がある。

| 観点 | 通常クラスター | Elastic clusters |
|---|---|---|
| スケール方法 | 主にインスタンスサイズ変更・リードレプリカ追加 | シャード数やシャードごとのvCPUを増減 |
| データ分散 | 共有クラスターVolume | シャードキーで分散 |
| 向く用途 | 一般的なMongoDB互換ワークロード | 大量読み書き・大容量データ |

> [!note] シャードキー
> DynamoDBのパーティションキーに少し似ていて、「どのシャードにデータを置くか」を決めるキー。
> 偏ったキーにすると一部のシャードだけ忙しくなるので、値がよく分散するキーを選ぶ。

---

## Global Clusters

DocumentDBにもグローバルクラスターがあり、1つのプライマリリージョンと複数の読み取り専用セカンダリリージョンで構成できる。

| 目的 | 内容 |
|---|---|
| リージョン障害対策 | セカンダリリージョンを昇格して復旧する |
| グローバル読み取り | 利用者に近いリージョンから低遅延で読む |
| 注意点 | 書き込みはプライマリリージョンのみ |

Aurora Global Databaseに似た考え方だが、DocumentDBはMongoDB互換のドキュメントDB向け。

---

## 他のDBとの違い

| サービス | データモデル | 得意なこと | 選ぶキーワード |
|---|---|---|---|
| [[0301_RDS]] | リレーショナル | SQL、JOIN、既存RDB互換 | MySQL / PostgreSQL / Oracleなど |
| [[0307_Aurora詳細]] | リレーショナル | 高性能RDB、グローバルDR | MySQL/PostgreSQL互換、高可用RDB |
| [[0303_DynamoDB]] | キー・バリュー / ドキュメント | 超スケール、低レイテンシ、サーバーレス | ミリ秒、キーアクセス、サーバーレスNoSQL |
| **DocumentDB** | ドキュメント | MongoDB互換、JSON風データ、柔軟なスキーマ | MongoDB互換、ドキュメントDB |
| [[0305_Neptune]] | グラフ | 関係性の探索 | 人・物・取引のつながり |
| [[0306_QLDB]] | 台帳 | 改ざん不可の履歴 | Ledger、監査、完全な変更履歴 |

> [!warning] DynamoDBとのひっかけ
> DynamoDBもドキュメントっぽい属性を持てるが、SAAでは基本的に「キーアクセス中心で超スケールするサーバーレスNoSQL」。
> **MongoDB互換APIや既存MongoDBアプリ移行**が強調されたらDocumentDBを疑う。

---

## よくある用途

| 用途 | なぜDocumentDBか |
|---|---|
| MongoDBアプリのAWS移行 | 既存のMongoDBドライバー・ツールを使いやすい |
| ユーザープロファイル | ユーザーごとにフィールド差が出やすい |
| コンテンツ管理 | 記事・メタデータ・タグなどを1ドキュメントにまとめやすい |
| カタログ | 商品ごとに属性が違っても表現しやすい |
| イベント・ログ系データ | JSON形式のデータをそのまま扱いやすい |

---

## SAA試験ポイント

| 問題文のキーワード | 答え |
|---|---|
| MongoDB互換のマネージドDBが必要 | **Amazon DocumentDB** |
| JSONドキュメントを柔軟なスキーマで保存したい | **Amazon DocumentDB** |
| 既存MongoDBアプリをAWSへ移行したい | **Amazon DocumentDB** |
| 読み取りを増やしたい | **リードレプリカ + リーダーエンドポイント** |
| 高可用性を上げたい | **複数AZにレプリカを配置** |
| リージョン障害に備えたい / グローバル読み取り | **DocumentDB Global Clusters** |
| もっと大規模な読み書きスケールが必要 | **Elastic clusters** |
| SQL・JOIN・既存RDB互換が必要 | **RDS / Aurora** |
| キー指定で超低レイテンシ・サーバーレスNoSQL | **DynamoDB** |
| 関係性を何段もたどる | **Neptune** |
| 改ざん不可の台帳 | **QLDB** |

---

## まとめ

- DocumentDB = **MongoDB互換APIで使えるフルマネージドなドキュメントDB**
- JSON風の柔軟なデータ、既存MongoDBアプリ移行で候補になる
- ストレージは3AZに6コピー、最大128TiBまで自動拡張
- 書き込みはプライマリ、読み取りは最大15台のレプリカで分散
- DynamoDBとの違いは、**MongoDB互換APIが必要かどうか**で見分ける

---

## 関連

- [[0301_RDS]]
- [[0303_DynamoDB]]
- [[0305_Neptune]]
- [[0306_QLDB]]
- [[0307_Aurora詳細]]

## 参考

- [What is Amazon DocumentDB](https://docs.aws.amazon.com/documentdb/latest/devguide/what-is.html)
- [Amazon DocumentDB: how it works](https://docs.aws.amazon.com/documentdb/latest/devguide/how-it-works.html)
- [Amazon DocumentDB elastic clusters: how it works](https://docs.aws.amazon.com/documentdb/latest/devguide/elastic-how-it-works.html)
- [Overview of Amazon DocumentDB global clusters](https://docs.aws.amazon.com/documentdb/latest/devguide/global-clusters.html)
