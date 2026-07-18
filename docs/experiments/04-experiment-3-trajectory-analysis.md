# Experiment 3: Trajectory Analysis

## 1. 概要

Experiment 3では、Behavior Cloningで学習したStudent Policyを閉ループで実行し、
各StepにおけるStudentの予測、実際の改善量、Teacherの最良改善量、
Action Regret、Actionの反復を分析した。

対象は次の2Seedである。

```text
Seed 7
Seed 10
```

この2つは、最終性能の良し悪しだけではなく、異なる失敗形態を示した。

- Seed 7: 改善余地を残したPremature Stop
- Seed 10: 改善しないActionを繰り返すRepeated Action Failure

---

## 2. 実行方法

既存の`result.json`を利用し、次のコマンドで分析成果物を再生成した。

### Seed 7

```bash
python scripts/run_trajectory_analysis.py \
  --model artifacts/model.pt \
  --output-dir artifacts/experiment-03-trajectory-analysis/seed-07 \
  --seed 7 \
  --skip-rollout
```

### Seed 10

```bash
python scripts/run_trajectory_analysis.py \
  --model artifacts/model.pt \
  --output-dir artifacts/experiment-03-trajectory-analysis/seed-10 \
  --seed 10 \
  --skip-rollout
```

---

## 3. 評価指標

主要な評価指標は次の通りである。

- Steps
- Final Error
- Stop Reason
- Oracle Action Match Rate
- Total / Mean / Max Action Regret
- Trajectory Prediction MAE
- Prediction Bias
- Zero Improvement Steps
- Negative Improvement Steps
- Longest Repeated Action
- Premature Stop
- Teacher Improvement at Student Stop
- First Zero Improvement Step
- First Repeated Action Step
- First Large Regret Step

---

## 4. 結果一覧

| 指標 | Seed 7 | Seed 10 |
|---|---:|---:|
| Steps | 16 | 32 |
| Final Error | 0.051479 | 0.131997 |
| Stop Reason | `policy_stop` | `max_steps` |
| Oracle Action Match Rate | 0.25000 | 0.03125 |
| Total Action Regret | 0.018786 | 0.303542 |
| Mean Action Regret | 0.001174 | 0.009486 |
| Max Action Regret | 0.003966 | 0.012902 |
| Trajectory Prediction MAE | 0.001357 | 0.007619 |
| Prediction Bias | -0.000108 | 0.006582 |
| Zero Improvement Steps | 0 | 23 |
| Negative Improvement Steps | 0 | 0 |
| Longest Repeated Action | 1 | 23 |
| Premature Stop | `true` | `false` |
| Teacher Improvement at Student Stop | 0.004296 | ― |
| First Zero Improvement Step | ― | 9 |
| First Repeated Action Step | ― | 10 |
| First Large Regret Step | ― | 9 |

---

## 5. Seed 7: Premature Stop

### 5.1 観測結果

Seed 7は16 Stepで終了した。

```text
stop_reason = policy_stop
premature_stop = true
teacher_improvement_at_student_stop = 0.004295721650123596
```

Studentが停止した時点でも、Teacherには正の改善量を持つActionが残っていた。

したがって、停止は環境が改善不能になったためではない。
Studentが改善余地を正しく評価できず、早い時点でStopを選択したと解釈できる。

### 5.2 Action Loopではない

Seed 7では、同一Actionの持続的反復は観測されなかった。

```text
longest_repeated_action.count = 1
first_repeated_action_step = null
```

この結果は重要である。Seed 7の失敗をAction Loopとして説明することはできない。

### 5.3 改善自体は継続していた

```text
zero_improvement_steps = 0
negative_improvement_steps = 0
```

Studentが選んだStrokeは、停止前まで少なくとも非負の改善を生んでいた。
それにもかかわらず、Teacherにはさらに大きな改善余地が残っていた。

これは、Stroke生成能力そのものが完全に崩れたというより、
Stop Actionを含むAction Valueの比較または停止判断に問題があった可能性を示す。

### 5.4 Prediction特性

```text
trajectory_prediction_mae = 0.001356803986709565
prediction_bias = -0.00010794581612572074
```

Prediction Biasはわずかに負であり、全体として大きな過大評価は見られない。
Seed 10と比較すると、予測誤差もAction Regretも小さい。

それでもPremature Stopが発生したことから、
平均的なPrediction Errorだけでは停止判断の失敗を説明しきれない。

今後は、停止直前の各Action ScoreとStop Scoreの相対関係を記録すると、
より直接的に原因を分析できる。

### 5.5 Seed 7の結論

Seed 7は、次の失敗形態を示す。

> Studentは有効なStrokeを選択できていたが、Teacherに改善余地が残る状態でStopを選択した。

これは**Premature Stop Failure**であり、Repeated Action Failureとは異なる。

---

## 6. Seed 10: Repeated Action Failure

### 6.1 観測結果

Seed 10は最大Step数である32 Stepに到達した。

```text
stop_reason = max_steps
premature_stop = false
```

StudentはStopを選択しなかったが、有効な改善を継続できたわけでもない。

### 6.2 Step 9から改善が停止

```text
first_zero_improvement_step = 9
zero_improvement_steps = 23
```

32 Step中23 StepでActual Improvementが0となった。

最初のZero ImprovementがStep 9で発生しているため、
Trajectoryの前半から後半へ移る時点で、状態更新が実質的に停止したと考えられる。

Negative Improvementは発生していない。

```text
negative_improvement_steps = 0
```

Canvasを悪化させるのではなく、改善しないActionを繰り返したことが特徴である。

### 6.3 同一Actionを23回繰り返した

```text
longest_repeated_action.stroke_index = 46
longest_repeated_action.count = 23
first_repeated_action_step = 10
```

Step 10以降、`stroke_index = 46`が連続して選択された。

Zero Improvementの開始がStep 9、Repeated Actionの検出がStep 10であるため、
改善停止とAction反復はほぼ同じ転換点で発生している。

これは局所的な重複ではなく、Trajectory後半を占める持続的な反復である。

### 6.4 Action Regretの蓄積

```text
total_action_regret = 0.30354193598032
mean_action_regret = 0.009485685499385
max_action_regret = 0.012902118265628815
first_large_regret_step = 9
```

Large Regretの開始もStep 9である。

したがって、次の3現象は同じ時点に集中している。

1. Actual Improvementが0になる
2. Teacherとの差が大きくなる
3. 同一Actionの反復が始まる

Teacherには有効なActionが存在する一方で、Studentは改善しないActionを固定的に選び続けた。

### 6.5 Prediction特性

```text
trajectory_prediction_mae = 0.007618804753292352
prediction_bias = 0.006581657682545483
```

Prediction Biasは正であり、Studentは改善量を過大評価する傾向を示した。

実際には改善を生まないActionを、改善すると予測したため、
同じActionが繰り返し選択された可能性がある。

Seed 7と比較すると、Prediction MAEは約5.6倍、Mean Action Regretは約8.1倍である。

### 6.6 Seed 10の結論

Seed 10は、次の失敗形態を示す。

> StudentはStep 9付近から改善しないActionを高く評価し、同じStrokeを繰り返してMax Stepsへ到達した。

これは**Repeated Action Failure**であり、
Predictionの過大評価とAction Selectionの固定化が組み合わさった失敗と解釈できる。

---

## 7. Seed間比較

Seed 7とSeed 10は、Behavior Cloningの閉ループ失敗が一種類ではないことを示した。

| 観点 | Seed 7 | Seed 10 |
|---|---|---|
| 主な失敗 | Premature Stop | Repeated Action Failure |
| 終了理由 | Policy Stop | Max Steps |
| 改善停止 | 観測されない | Step 9以降に集中 |
| 同一Action反復 | なし | 23回 |
| Prediction Bias | ほぼ0、わずかに過小評価 | 明確な過大評価 |
| Action Regret | 小さい | 大きく蓄積 |
| Teacherの改善余地 | 停止時に残る | 反復中に残る |

共通点は、Studentの判断がTeacherの最良判断から外れていることである。

相違点は、その外れ方である。

- Seed 7は、行動を続けるべき状態で停止した
- Seed 10は、停止も有効なStrokeへの切替も行わず、同じActionを続けた

この差は、単一の平均スコアだけでは見えない。
Trajectory Analysisを導入したことで初めて明確に分類できた。

---

## 8. Experiment 3から得られた知見

### 8.1 最終Errorだけでは失敗原因を説明できない

Seed 7はSeed 10よりFinal Errorが小さいが、それでもPremature Stopしている。

最終結果が比較的良くても、Policyの判断が正しいとは限らない。

### 8.2 Action Match Rateだけでも不十分である

両SeedともTeacherとの完全一致率は高くないが、
Seed 7は一定の改善を継続し、Seed 10はLoopへ入った。

Teacherと異なるActionを選ぶこと自体より、
そのActionが実際に改善を生むか、反復固定化するかが重要である。

### 8.3 Prediction Errorは失敗形態と対応する

Seed 10では正のPrediction Biasと大きなPrediction MAEが、
改善しないActionの反復と対応した。

一方、Seed 7は平均的なPrediction Errorが小さくても停止判断に失敗した。

したがってPhase 2では、Stroke ValueだけでなくStop Decisionも個別に評価する必要がある。

### 8.4 Behavior Cloningの問題は閉ループで現れる

Student自身のActionによって状態分布が変わると、
教師データ上での予測精度だけでは保証できない失敗が生じる。

この観測は、Studentが訪れた状態を教師データへ取り込むDAggerの導入理由になる。

---

## 9. 制約

今回の分析には次の制約がある。

- 中心的に分析したSeedは2つである
- 失敗形態の発生頻度はまだ推定していない
- Stop Actionの内部Scoreを直接保存していない
- Cumulative Action Regretを独立した列や図としては生成していない
- Repeated Action Countは連続する同一Strokeだけを検出する
- 周期2以上のAction Cycleは検出していない

したがって、Seed 7とSeed 10は代表例であり、
全Seedにおける発生割合を示すものではない。

---

## 10. Phase 2への示唆

Phase 2では、少なくとも次の改善を検証する。

1. Student自身が訪れた状態をDAggerでDatasetへ追加する
2. Premature Stopの発生率を測定する
3. Repeated Action Failureの発生率を測定する
4. Stop ScoreとBest Stroke Scoreの差を記録する
5. 複数Seedで失敗形態を自動分類する
6. Action RegretとPrediction Errorの分布をPhase 1と比較する

Phase 2の成功は、単にFinal Errorを下げることだけではない。

- 改善余地を残した停止を減らす
- 無効なActionの反復を減らす
- Teacherとの差をTrajectory全体で減らす

という閉ループPolicyとしての改善が必要である。

---

## 11. 結論

Experiment 3では、Behavior Cloning Studentの閉ループ失敗として、
少なくとも二つの異なる形態を観測した。

```text
Seed 7  = Premature Stop Failure
Seed 10 = Repeated Action Failure
```

これによりPhase 1は、Behavior Cloningを実装して結果を表示する段階から、
Student Policyの失敗をTrajectory単位で診断できる段階へ進んだ。

Experiment 3の成果は、DAggerを導入するPhase 2のBaselineとなる。
