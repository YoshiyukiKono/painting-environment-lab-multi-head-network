# Experiment 3: Trajectory Analysis 設計

## 1. この文書の役割

この文書は、Phase 1におけるExperiment 3の目的、観測対象、評価方法、成果物を定義する。

Experiment 3の実験結果と考察は、次の文書に記録する。

```text
docs/experiments/04-experiment-3-trajectory-analysis.md
```

Phase 1全体における位置付けと、Phase 2への接続は、次の文書にまとめる。

```text
docs/phase-1-summary.md
```

本設計は、実装されていない可視化や指標を完了条件に含めない。現在の
`scripts/run_trajectory_analysis.py` が生成する成果物と、実際に観測できる値を基準とする。

---

## 2. 背景

Behavior Cloningで学習したStudent Policyは、教師データ上で妥当な予測を行えても、
閉ループ実行ではStudent自身のActionによって次の状態が決まる。

その結果、学習時には十分に現れなかった状態へ移動し、次のような失敗が起こり得る。

- Teacherに改善可能なActionが残っているのに停止する
- 改善を生まないActionを選び続ける
- 同じActionを繰り返して状態が進展しない
- 改善量の予測と実測がずれる
- Teacherとの差であるAction Regretが蓄積する

Experiment 3では、最終Canvasだけではなく、各StepのTrajectoryを調べることで、
失敗がどのように発生したかを分類する。

---

## 3. 目的

Experiment 3の目的は、Behavior CloningによるStudent Policyの閉ループ失敗を、
Trajectory単位で再現可能に観測することである。

特に次の問いに答える。

1. Studentは何Stepまで有効な改善を続けるか
2. Studentの予測改善量は、実際の改善量と一致しているか
3. Teacherとの差はどの時点から大きくなるか
4. Studentは改善余地を残して停止するか
5. Studentは同じActionを繰り返すか
6. 異なるSeedで同じ失敗形態が現れるか
7. 複数の異なる失敗形態を区別できるか

---

## 4. 実行構成

Experiment 3では、Student/Teacher Rolloutを重複実装しない。

```text
run_demo_oracle.py
    Student RolloutとTeacher比較を実行
                ↓
result.json
                ↓
run_trajectory_analysis.py
    Step単位の派生指標、CSV、JSON、グラフを生成
```

既存の`result.json`を再解析する場合は、次のように実行する。

```bash
python scripts/run_trajectory_analysis.py \
  --model artifacts/model.pt \
  --output-dir artifacts/experiment-03-trajectory-analysis/seed-07 \
  --seed 7 \
  --skip-rollout
```

`--skip-rollout`は、既存のRollout結果を変更せず、分析成果物だけを再生成するために使用する。

---

## 5. 観測する値

### 5.1 Error Trajectory

各Stepの`error_before`と`error_after`を観測する。

これにより、StudentがCanvas Errorを継続的に減らしているか、
途中から改善が止まっているかを確認する。

### 5.2 Predicted Improvement

Studentが選択したActionによって得られると予測した改善量である。

### 5.3 Actual Improvement

Studentが選択したActionによって実際に得られた改善量である。

### 5.4 Teacher Best Improvement

同じ状態でTeacherが選択できた最良Actionの改善量である。

Student停止時にこの値が正であれば、Studentは改善余地を残して停止したと判断する。

### 5.5 Action Regret

Teacherの最良改善量と、Studentが実際に得た改善量との差である。

```text
action_regret
    = teacher_best_improvement - actual_improvement
```

値が大きいほど、StudentのAction選択による機会損失が大きい。

### 5.6 Prediction Error

Studentの予測改善量と実際の改善量との差である。

```text
prediction_error
    = predicted_improvement - actual_improvement
```

- 正の値: 改善量を過大評価
- 負の値: 改善量を過小評価
- 0付近: 予測と実測が一致

### 5.7 Prediction Absolute Error

Prediction Errorの絶対値である。予測の方向ではなく、ずれの大きさを表す。

### 5.8 Repeated Action Count

同じ`stroke_index`が連続して選ばれた回数である。

この値はAction Loopの存在を前提とするものではない。
連続反復が観測されなければ、それも実験結果として扱う。

---

## 6. 失敗形態の判定

### 6.1 Premature Stop

次の条件を満たす場合、Premature Stopと判定する。

- `stop_reason`が`policy_stop`
- Student停止時の`teacher_best_improvement`が正
- `premature_stop`が`true`

これは、環境が改善不能になったのではなく、Studentの停止判断が早すぎたことを意味する。

### 6.2 Repeated Action Failure

次の現象が同時に見られる場合、Repeated Action Failureと判断する。

- 同じ`stroke_index`が長く連続する
- `repeated_action_count`が継続的に増加する
- `actual_improvement`が0付近になる
- `stop_reason`が`max_steps`
- Action Regretが継続して発生する

### 6.3 Action Selection Failure

同じActionの反復がなくても、Teacherとの差が継続して大きい場合は、
一般的なAction Selection Failureとして扱う。

### 6.4 Value Estimation Failure

Prediction ErrorまたはPrediction Absolute Errorが大きく、
その誤差が停止判断や無効なAction選択と対応する場合は、
改善量の推定失敗として解釈する。

---

## 7. 対象Seed

Phase 1では、対照的なTrajectoryを示す次の2Seedを中心に分析する。

```text
Seed 7
Seed 10
```

Seed 7はPremature Stopの候補として、Seed 10はRepeated Action Failureの候補として扱う。
ただし、結論は実測値に基づいて記述する。

---

## 8. 生成成果物

現在のスクリプトが生成する主要成果物は次の通りである。

```text
result.json
trajectory.csv
trajectory-analysis.json

error-trajectory.png
improvement-trajectory.png
action-regret.png
action-sequence.png
```

`run_demo_oracle.py`が生成した次の成果物も同じディレクトリに保持する。

```text
target.png
final_canvas.png
trajectory.gif
```

`trajectory.csv`には、少なくとも次のStep単位データを含める。

```text
step
decision
stroke_index
teacher_stroke_index
action_match
predicted_improvement
actual_improvement
teacher_best_improvement
action_regret
prediction_error
prediction_absolute_error
error_before
error_after
repeated_action_count
premature_stop
```

---

## 9. レビュー手順

各Seedについて、次の順序で確認する。

1. `target.png`と`final_canvas.png`を比較する
2. `trajectory.gif`でCanvasの変化を見る
3. `error-trajectory.png`で誤差の推移を見る
4. `improvement-trajectory.png`で予測、実測、Teacher最良値を比較する
5. `action-regret.png`でTeacherとの差が生じる時点を見る
6. `action-sequence.png`でActionの切替と反復を見る
7. `trajectory-analysis.json`のSummaryを確認する
8. `trajectory.csv`で転換点の前後を確認する

グラフだけで結論を出さず、JSON、CSV、Canvasを相互に確認する。

---

## 10. 完了条件

Experiment 3は、次の条件を満たした時点で完了とする。

- Seed 7とSeed 10の分析成果物が生成されている
- 各Seedの停止理由が記録されている
- Premature Stopの有無が判定されている
- Repeated Actionの有無と最長連続回数が記録されている
- Prediction ErrorとAction Regretが記録されている
- 2Seedの失敗形態を比較できる
- 実験結果が`docs/experiments/04-experiment-3-trajectory-analysis.md`に記録されている
- Phase 1全体の意味が`docs/phase-1-summary.md`に統合されている

追加グラフの枚数そのものは完了条件としない。

---

## 11. Phase 2への接続

Experiment 3は、Student Policyを改善する実験ではなく、
Phase 2で改善対象とする失敗を定義する実験である。

Phase 2では、DAggerなどを用いてStudent自身が訪れた状態を教師データへ追加し、
次の変化を検証する。

- Premature Stopが減少するか
- Repeated Action Failureが減少するか
- Action Regretが減少するか
- Prediction Errorが減少するか
- Max Steps到達前に有効なTrajectoryを完了できるか

Experiment 3の成果は、Phase 2のBaselineである。
