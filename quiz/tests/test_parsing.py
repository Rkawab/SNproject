import unittest

from quiz.parsing import parse_exam


class ParseExamTests(unittest.TestCase):
    def test_ignores_problem_set_metadata_and_parses_exam_sections(self):
        text = """\
# 【問題】サービス用途確認（4択・全2問）

## この問題集の目的

主要サービスの用途を確認する。

## 対象レベル

初心者向け。

## 問題数

2問。

## 使い方

不正解の理由まで確認する。

---

## 第1問（ストレージ）
大量のファイルを保存するサービスはどれか。

- A. Amazon S3
- B. Amazon EBS
- C. Amazon EFS
- D. Amazon RDS

> [!success]- 答え：**A**（Amazon S3）
> S3はオブジェクトストレージである。
> **他の選択肢が違う理由**
> - B：ブロックストレージ。

## 第2問（監視）
メトリクスを監視するサービスはどれか。

- A. AWS CloudTrail
- B. Amazon CloudWatch
- C. AWS Config
- D. AWS Artifact

> [!success]- 答え：**B**（Amazon CloudWatch）
> CloudWatchはメトリクスとログを監視する。
"""

        questions = parse_exam(text)

        self.assertEqual([1, 2], [question["number"] for question in questions])
        self.assertEqual("ストレージ", questions[0]["genre"])
        self.assertEqual(
            {"A": "Amazon S3", "B": "Amazon EBS", "C": "Amazon EFS", "D": "Amazon RDS"},
            questions[0]["choices"],
        )
        self.assertEqual("A", questions[0]["answer"])
        self.assertIn("S3はオブジェクトストレージ", questions[0]["explanation_md"])
        self.assertEqual("B", questions[1]["answer"])

    def test_parses_multiple_answer_letters(self):
        text = """\
## 第1問（可用性）
次の要件を満たす選択肢を2つ選べ。

- A. Application Load Balancer
- B. Auto Scaling group
- C. NAT Gateway
- D. AWS Artifact

> [!success]- 答え：**A, B**
> - A：正解。
> - B：正解。
"""

        questions = parse_exam(text)

        self.assertEqual("A,B", questions[0]["answer"])

    def test_parses_five_choices_with_e(self):
        """SAA公式サンプル形式の5択（A〜E）を取り込めること。"""
        text = """\
## 第1問（ネットワーク）
プライベートサブネットのEC2がパッチを取得する構成を2つ選べ。

- A. 各AZのパブリックサブネットにNAT Gatewayを構成する。
- B. NAT Gatewayへのルートをプライベートサブネットに関連付ける。
- C. 各EC2にElastic IPを割り当てる。
- D. Internet Gatewayをプライベートサブネットに関連付ける。
- E. プライベートサブネットにNATインスタンスを単一AZで構成する。

> [!success]- 答え：**A, B**
> - A：正解。
> - B：正解。
> - E：単一AZのNATインスタンスは可用性に欠ける。
"""

        questions = parse_exam(text)

        # E を含む全5択が選択肢として抽出される
        self.assertEqual(
            {"A", "B", "C", "D", "E"},
            set(questions[0]["choices"].keys()),
        )
        self.assertEqual("A,B", questions[0]["answer"])

    def test_parses_e_as_correct_answer(self):
        """正答に E が含まれる場合も認識すること。"""
        text = """\
## 第1問（テスト）
正しいものを選べ。

- A. 誤り
- B. 誤り
- C. 誤り
- D. 誤り
- E. 正しい

> [!success]- 答え：**E**
> - E：正解。
"""

        questions = parse_exam(text)

        self.assertEqual("E", questions[0]["answer"])


if __name__ == "__main__":
    unittest.main()
