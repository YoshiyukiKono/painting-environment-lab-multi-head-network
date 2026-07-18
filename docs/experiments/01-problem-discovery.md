# 12. Next Experiments

## 方針

次の実験では、一度に多くの要素を変えない。

現在の成果は、Multi-head Networkが成立したことを確認できた点にある。

次は、Closed-loop後半の劣化原因を順番に切り分ける。

---

## Experiment 1: 複数Seedでの再現性

### 目的

今回の成功が特定Seedに依存していないか確認する。

### 実行例

```bash
for seed in 1 2 3 4 5 6 7 8 9 10
do
  python scripts/run_demo.py \
    --model artifacts/model.pt \
    --seed ${seed} \
    --output-dir artifacts/demo-seed-${seed}
done
```

### 記録する値

- final_error
- steps
- stop_reason
- repeated_action_streak
- predicted improvement / actual improvement
- zero or negative actual improvement count

### 成功基準

- 即Stopが頻発しない
- 大半のSeedで複数Strokeを実行する
- Improvement predictionとactual improvementが正の相関を持つ

---

## Experiment 2: Teacher Closed-loopとの比較

### 目的

同じTargetとAction Spaceで、TeacherとStudentの差を測る。

### 比較対象

```text
Greedy Teacher rollout
Multi-head Student rollout
```

### 必要な出力

- Teacher final_error
- Student final_error
- Teacher steps
- Student steps
- Stroke agreement
- Stop step gap

### 解釈

Teacherも同程度の粗さなら、主因はAction Spaceである。

Teacherが大幅に良ければ、主因はPolicy imitationまたはdistribution shiftである。

---

## Experiment 3: Step別Prediction Error

### 目的

Prediction errorが本当に後半で増えるか確認する。

### 計算

各Stepについて次を記録する。

```text
absolute_error =
abs(predicted_improvement - actual_improvement)
```

### 集計

```text
step 1-4
step 5-8
step 9-12
step 13+
```

### 期待結果

後半ほどMAEが増えるなら、distribution shift仮説が強まる。

---

## Experiment 4: Target Transform比較

### 条件

```text
raw
standardized
log
```

### 実行例

```bash
python scripts/train.py \
  --dataset artifacts/dataset.npz \
  --epochs 20 \
  --target-transform raw \
  --output artifacts/model-raw.pt
```

```bash
python scripts/train.py \
  --dataset artifacts/dataset.npz \
  --epochs 20 \
  --target-transform standardized \
  --output artifacts/model-standardized.pt
```

```bash
python scripts/train.py \
  --dataset artifacts/dataset.npz \
  --epochs 20 \
  --target-transform log \
  --output artifacts/model-log.pt
```

### 比較指標

- Improvement MAE
- Improvement Correlation
- Prediction range
- Immediate Stop rate
- Final Error
- Stop timing

---

## Experiment 5: Loss Weight Ablation

### 条件

```text
improvement_weight =
0.1
0.3
1.0
3.0
10.0
```

### 目的

二つのTaskのバランスを調べる。

### 期待する観察

- 小さすぎるとImprovement Headが弱くなる
- 大きすぎるとStroke Accuracyが低下する
- 中間にPareto pointがある

### 注意

合計Lossだけで最適値を選ばない。

Stroke AccuracyとImprovement Correlationを別々に見る。

---

## Experiment 6: Stop Threshold評価

### 問題

現状のCalibrationはAccuracy最大化に偏っている。

### 改善案

Thresholdごとに次を計測する。

- Stop Precision
- Stop Recall
- F1
- False Stop Rate
- Late Stop Rate
- Mean Final Error
- Mean Steps
- max_steps rate

### Threshold候補

```text
-1e-3
-5e-4
0
1e-5
1e-4
5e-4
1e-3
```

### 最終判断

Teacher-state Datasetではなく、Closed-loop評価で選ぶ。

---

## Experiment 7: DAgger再導入

### 前提

次が確認できてから実施する。

- Multi-head学習が複数Seedで安定
- Improvement predictionがTeacher statesで良好
- Step別Errorが後半で増える
- TeacherとStudentの性能差が明確

### DAgger Round

```text
Round 0:
Teacher Dataset

Round 1:
Student rollout states + Teacher labels

Round 2:
さらにStudent rollout statesを追加

Round 3:
再学習
```

### Teacher label

Student stateごとに次を保存する。

```text
best_stroke
best_improvement
```

### 比較

```text
BC only
vs
DAgger Round 1
vs
DAgger Round 2
vs
DAgger Round 3
```

### 成功基準

- 後半のImprovement MAE低下
- Student-only stateからの回復
- repeated action streak低下
- Final Error改善
- Stop timing改善

---

## Experiment 8: Action Space Ablation

DAggerの効果を確認した後に実施する。

### 比較例

```text
Grid:
4×4
8×8
16×16

Palette:
8
16
32
64

Radius:
1種類
2種類
4種類
```

### 目的

Network errorとAction representation limitを分ける。

### 注意

Action数を減らすこと自体を本質的解決とみなさない。

Action Space変更は、原因切り分けとPhysical designとの整合のために行う。

---

## Experiment 9: Observation Design

さらに後の候補。

### 現状

```text
Target RGB
Canvas RGB
```

### 候補

```text
Target
Canvas
Difference Image
Error Map
Previous Action
Step Count
```

### 仮説

Difference Imageを明示的に追加すると、Stroke locationとImprovement predictionが容易になる可能性がある。

ただし、Observationを増やす前に、DAggerでdistribution shiftを検証する。

---

## 推奨する次の実装順

```text
1. 複数Seed評価
2. Teacher vs Student比較
3. Step別Prediction Error
4. Threshold評価改善
5. DAgger再導入
6. Transform / Loss ablation
7. Action Space拡張
8. Observation Design
9. Actor-Critic
```

最優先は、DAggerをただ追加することではない。

まず、

> 後半の劣化が本当にStudent-state distribution shiftによるものか

を定量的に確認する。

そのうえでDAggerを導入すれば、改善理由を説明できる実験になる。
