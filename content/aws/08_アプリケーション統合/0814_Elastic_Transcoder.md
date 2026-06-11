# Elastic Transcoder

> [!warning] 旧世代サービス
> 現在は **AWS Elemental MediaConvert** が後継として推奨されている。MediaConvert の方が高機能・コスト効率も良く、AWSの公式案内も MediaConvert に移っている。SAAでも MediaConvert が答えになることが多い。

## 概要

S3 に保存された動画ファイルを、別のフォーマット・解像度・ビットレートに**変換**するメディアトランスコーディングサービス。

## たとえ話

**動画変換業者**。
撮影した1本の元動画を、iPhone用・Android用・PC用・タブレット用に**自動で複数フォーマットに変換**してくれる。
入力（S3） → 変換（プリセット選択） → 出力（S3）の流れ。

---

## 主な構成要素

| 要素 | 役割 |
|------|------|
| **パイプライン** | 入力S3バケット・出力S3バケットの組み合わせ |
| **ジョブ** | 1つの変換タスク（入力ファイル + プリセット） |
| **プリセット** | 出力フォーマット定義（解像度・ビットレート・コーデック） |
| **通知** | 完了/失敗を [[0803_SNS]] で受け取れる |

### よくある使い方

```
[ユーザーが動画アップロード]
       ↓
[S3 (input)] → S3イベント → [Lambda] → Elastic Transcoder ジョブ作成
                                          ↓
                                  [変換処理]
                                          ↓
                                  [S3 (output)]
                                  ├─ iPhone用 720p
                                  ├─ Android用 480p
                                  └─ PC用 1080p
                                          ↓
                                  [SNS で完了通知]
```

---

## AWS Media サービス群（試験では区別が重要）

Elastic Transcoder だけでなく、Mediaシリーズを全体感で理解しておくべき:

| サービス | 役割 |
|---------|------|
| **MediaConvert** | ファイルベースの動画変換（Elastic Transcoder の後継・本命） |
| **MediaLive** | **ライブ配信**用のリアルタイムエンコード |
| **MediaPackage** | 配信用フォーマットへのパッケージング（HLS / DASH 等） |
| **MediaStore** | 動画専用の低レイテンシストレージ |
| **MediaTailor** | 動画への**パーソナライズ広告挿入** |
| **MediaConnect** | プロ放送品質のライブ動画伝送 |
| **Elastic Transcoder** | **旧世代**の動画変換 |

---

## Elastic Transcoder vs MediaConvert

| 観点 | Elastic Transcoder | MediaConvert |
|------|--------------------|--------------|
| 機能 | 基本的なフォーマット変換 | **4K / HDR / 字幕 / 複数音声トラック / 広告挿入**等の高度な機能 |
| 入力フォーマット | 限定的 | 多種多様 |
| 出力フォーマット | 限定的 | HLS / DASH / CMAF など最新ストリーミングフォーマット対応 |
| 料金 | 出力時間ベース | 出力時間ベース・**ティア別料金**でより細かい |
| 推奨度 | 旧世代 | **現行推奨** |
| AWSの今後 | メンテナンスのみ | 機能拡張継続 |

---

## 典型構成（現代版）

```
[クライアント]
   ↓ 動画アップロード
[S3 (input bucket)]
   ↓ S3 Event Notification
[Lambda]
   ↓ ジョブ作成
[MediaConvert]
   ↓ 変換完了
[S3 (output bucket)]
   ↓ CloudFront 経由で配信
[エンドユーザー（HLS/DASH 再生）]
```

---

## SAA頻出パターン

| 問題文のキーワード | 答え |
|---------------------|------|
| 「動画ファイルを**複数フォーマットに変換**」 | **MediaConvert**（または Elastic Transcoder） |
| 「**ライブ配信**のエンコード」 | MediaLive |
| 「HLS / DASH の**パッケージング**」 | MediaPackage |
| 「**広告の動的挿入**」 | MediaTailor |
| 「**4K動画**変換」 | MediaConvert |

> [!tip] 試験での選び方
> 問題文が「基本的な動画変換」のみなら両方候補。**「新しい」「現代の」「高機能」**のニュアンスがあれば **MediaConvert**。古い教材では Elastic Transcoder が出るが、現実は MediaConvert を覚えれば十分。

---

## 関連

- [[0201_S3]] - 入出力先
- [[0803_SNS]] - 完了通知先
- [[Lambda]] - イベント駆動でジョブ作成
- [[CloudFront]] - 変換後動画の配信
