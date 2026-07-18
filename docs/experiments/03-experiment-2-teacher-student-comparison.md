私は、このリポジトリは「コード」だけではなく、「研究記録」も成果物にしたいと思っています。

これまでの流れを見ると、単に `13-experiment-2-results.md` のように並べるよりも、**実験ごとに独立した再現可能な成果物**として整理する方が、このリポジトリの価値が高まります。

私なら、次のような構成にします。

```
docs/
├── experiments/
│   ├── 01-problem-discovery.md
│   ├── 02-experiment-1-behavior-cloning-evaluation.md
│   ├── 03-experiment-2-teacher-student-comparison.md
│   ├── 04-experiment-3-...
│   └── ...
├── design/
├── theory/
└── roadmap.md
```

このようにすると、

* **実験番号**（時系列）
* **内容**（何を検証したか）

の両方がファイル名だけで分かります。

---

私が今回提案したいファイル名は、

```
docs/experiments/
03-experiment-2-teacher-student-comparison.md
```

です。

タイトルは日本語にします。

---

# Experiment 2

## Teacher–Student比較とOracle診断

---

## 目的

Experiment 1では、Behavior CloningによるStudent Policyにおいて、

* Regression Collapse
* 即時停止

といった問題は解消された一方で、

**Action Loop**

が主要な失敗要因として残ることが確認された。

しかし、この時点では、

> Action LoopはAction Spaceそのものの限界なのか、
> それともStudent Policyの判断ミスなのか

は明らかではなかった。

そこでExperiment 2では、

TeacherとStudentを同一条件で比較し、

さらにStudentが訪れた各状態においてTeacherの判断を問い合わせるOracle診断を導入した。

目的は、

> **Action Loopの原因を定量的に明らかにすること**

である。

---

# 実験構成

Experiment 2では3種類の実行スクリプトを利用した。

| Script             | 内容                         |
| ------------------ | -------------------------- |
| run_demo.py        | Studentのみ実行                |
| run_teacher.py     | Teacherのみ実行                |
| run_demo_oracle.py | Student実行中にTeacherを毎Step評価 |

これらは互いに独立しており、

既存の実験コードを変更せずに比較実験を実施できる構成とした。

---

# 実験条件

TeacherとStudentは、

* 同一Seed
* 同一Target Image
* 同一初期Canvas
* 同一Action Space
* 最大32Step

で実行した。

Target画像については、

SHA-256を比較し、

完全に一致することを確認している。

---

# Teacher Rollout

まずTeacherのみを実行した。

Teacherは毎Step、

全Strokeをsimulate()し、

最も改善量の大きいStrokeを選択する。

結果は以下である。

| 項目                        | 結果 |
| ------------------------- | -: |
| Seed数                     | 10 |
| Teacher Stop              | 10 |
| Max Step終了                |  0 |
| Zero Improvement Step     |  0 |
| Negative Improvement Step |  0 |

平均Final Error

Teacher

```
0.0425
```

Student

```
0.0724
```

TeacherはStudentよりも約1.7倍小さい誤差で停止した。

---

## 考察1

Teacherは、

Action Loopに陥ることなく、

自然停止している。

つまり、

Action Spaceには依然として改善可能なStrokeが存在している。

したがって、

Action Loopは

**Action Spaceの限界では説明できない。**

---

# Oracle診断

次に、

Studentが訪れた各状態でTeacherを評価した。

各Stepについて、

以下を記録した。

* Student Stroke
* Teacher Stroke
* Student Actual Improvement
* Teacher Best Improvement
* Action Match
* Action Regret

Action Regretは

```
Teacher Best Improvement
−
Student Actual Improvement
```

で定義した。

これは、

StudentがTeacherと異なるStrokeを選択したことによって失われた改善量を意味する。

---

# Seed 7

Seed7では、

Studentは16Stepで停止した。

Oracle結果は

```
Action Match Rate

25%
```

```
Premature Stop

True
```

```
Teacher Improvement

0.00430
```

であった。

Studentは

「これ以上改善できない」

と判断したが、

Teacherは依然として改善可能なStrokeを発見していた。

つまり、

Studentは改善可能性を残したまま停止していたことが確認された。

---

## 考察2

興味深いことに、

TeacherとのAction一致率は25%しかないにもかかわらず、

最終誤差はTeacherに比較的近い。

これは、

描画経路が一意ではないことを示唆している。

つまり、

同じ最終画像へ到達するStroke列は複数存在する可能性が高い。

---

# Seed10

Seed10では、

Experiment1で確認されたAction Loopが再現された。

Oracle結果は

```
Action Match Rate

3.125%
```

```
Zero Improvement Step

23
```

```
Longest Loop

Stroke46

23回
```

であった。

32Step中、

Teacherと一致したStrokeは約1回のみであった。

さらに、

Loop中もTeacherは改善可能なStrokeを発見していた。

Studentは

改善可能なStrokeが存在するにもかかわらず、

改善量0のStrokeを繰り返していたことが確認された。

---

## 考察3

Action Loopは

Canvasが改善不能になった結果ではない。

改善可能なStrokeは存在していた。

問題は、

StudentがそのStrokeを選択できなかったことである。

つまり、

Action Loopの本質は

**Action Selection Failure**

である。

---

# Experiment 2で得られた知見

Experiment 2により、

次の3点が明らかになった。

## 1.

Action Spaceは十分な改善能力を持っている。

TeacherはAction Loopを起こさない。

---

## 2.

StudentはTeacherと大きく異なるStrokeを選択している。

Action Match Rate

Seed7

```
25%
```

Seed10

```
3.125%
```

---

## 3.

Action Regretは

Action Loopを定量的に説明できる指標となる。

従来は画像からしか説明できなかったAction Loopを、

数値として評価できるようになった。

---

# Experiment 2の結論

Experiment 1では、

Action Loopの存在のみが確認された。

Experiment 2では、

その原因が

Action Spaceではなく、

**Student PolicyによるAction Selection Failure**

であることを示した。

また、

Teacherとの比較から、

Action Match RateおよびAction Regretが、

Sequential Painting Policyを評価する上で有効な診断指標となることが確認された。

これらの指標は、

今後のExperimentにおいて、

Behavior Cloningの改善手法（DAggerなど）を評価する際の基準として利用する予定である。

---

私は、この文書を **「Experiment 2の最終報告書」** と位置付けることをおすすめします。

また、今回のやり取りを通して、リポジトリ全体の構成も見えてきました。単なる実験ログではなく、**「問題提起 → 仮説 → 実験 → 結論」が積み重なる研究ノート**として整理できています。この方向であれば、後から読んだ人でも、Experiment 3や4に進む理由が自然に理解できる構成になります。
