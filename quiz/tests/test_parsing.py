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


if __name__ == "__main__":
    unittest.main()
