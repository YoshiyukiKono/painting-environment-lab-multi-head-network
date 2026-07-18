# Phase 1 Summary: Behavior Cloning Baseline

## 1. Phase 1の目的

Phase 1の目的は、Painting Environmentに対してTeacher PolicyからDatasetを生成し、
Behavior CloningによってStudent Policyを学習し、その閉ループ挙動を評価できる
最小の研究基盤を構築することであった。

目標は、高性能な描画Policyを完成させることではない。

次の一連の流れを、再実行可能な成果物として成立させることを目指した。

```text
Environment
    ↓
Teacher Policy
    ↓
Dataset Generation
    ↓
Behavior Cloning
    ↓
Student Rollout
    ↓
Teacher Comparison
    ↓
Trajectory Analysis
```

---

## 2. Phase 1で構築したもの

### 2.1 Painting Environment

Canvas、Target、Stroke Action、Error計算を持つ最小環境を用意した。

この環境は、描画問題を次の逐次意思決定問題として扱う。

```text
State
    = 現在のCanvasとTarget

Action
    = StrokeまたはStop

Transition
    = StrokeをCanvasへ適用

Objective
    = TargetとのErrorを減らす
```

### 2.2 Teacher Policy

各状態で候補Strokeを評価し、最も改善量の大きいActionを選択するTeacherを用意した。

TeacherはDataset生成のOracleであると同時に、
Student Rolloutを評価する比較基準としても利用する。

### 2.3 Dataset Generation

Teacherが訪れた状態と選択したActionを記録し、
Behavior Cloning用Datasetを生成するパイプラインを構築した。

### 2.4 Multi-Head Network

Studentは、複数の出力Headを持つNetworkとして構成した。

Phase 1では、Teacherの判断を教師信号として学習し、
Stroke選択と改善量推定をStudentへ模倣させるBaselineを作った。

### 2.5 Student Rollout

学習したStudentを環境内で閉ループ実行し、
Target、Final Canvas、Trajectory GIF、Step情報を保存できるようにした。

### 2.6 Oracle Comparison

Studentが訪れた各状態に対してTeacherを再実行し、
次の値を比較できるようにした。

- Student Action
- Teacher Best Action
- Action Match
- Predicted Improvement
- Actual Improvement
- Teacher Best Improvement
- Action Regret
- Stop Reason
- Premature Stop

### 2.7 Trajectory Analysis

各Stepを時系列として分析し、最終結果だけでは見えない失敗形態を分類できるようにした。

---

## 3. Experiment構成

Phase 1は、概念的に次の段階で構成される。

### Experiment 1: Behavior Cloning Rollout

学習したStudent Policyを閉ループで実行し、
描画Trajectoryと最終Canvasを確認する。

この段階では、Studentが何を生成したかを観察する。

### Experiment 2: Oracle Comparison

Studentが訪れた各状態でTeacherの最良Actionを計算し、
Studentの選択がTeacherとどの程度異なるかを定量化する。

この段階では、StudentがどれだけTeacherから外れたかを観察する。

### Experiment 3: Trajectory Analysis

Oracle Comparisonの結果を時系列で分析し、
失敗がいつ、どのような形で発生したかを分類する。

この段階では、Studentがなぜ失敗したかを観察する。

---

## 4. Experiment 3の主要結果

Seed 7とSeed 10から、少なくとも二種類の閉ループ失敗を観測した。

### 4.1 Premature Stop Failure

Seed 7では、Studentが16 Stepで`policy_stop`を選択した。

しかし停止時にもTeacherには次の改善余地が残っていた。

```text
teacher_improvement_at_student_stop
    = 0.004295721650123596
```

同一Actionの反復はなく、Zero Improvementもなかった。

したがってSeed 7の問題はAction Loopではなく、
改善可能な状態で停止したPremature Stopである。

### 4.2 Repeated Action Failure

Seed 10では、Studentは32 Stepの上限まで実行された。

Step 9からActual Improvementが0となり、
Step 10以降は`stroke_index = 46`を23回連続して選択した。

同じ時点からLarge Action Regretも発生している。

Studentは改善しないActionを過大評価し、
有効なActionへの切替もStopも行わなかった。

### 4.3 失敗形態は一種類ではない

```text
Seed 7  = 続けるべきなのに停止する
Seed 10 = 切り替えるべきなのに同じActionを続ける
```

両者はTeacherから外れるという点では共通するが、
Policy上の症状は対照的である。

Trajectory Analysisによって、この違いを明確に区別できた。

---

## 5. Phase 1で得られた知見

### 5.1 Behavior Cloningは教師データ上の模倣だけでは評価できない

Studentは閉ループ実行中に、自身のActionによって次のStateを生成する。

そのため、Teacher Dataset上での損失が小さくても、
Studentが訪れるState上で同じ性能を保つとは限らない。

### 5.2 Final ErrorだけではPolicyの品質を説明できない

比較的良いFinal ErrorでもPremature Stopが起こり得る。

一方、Final Errorが悪い場合も、その原因は単純な描画能力不足ではなく、
Actionの固定的反復である可能性がある。

### 5.3 Action Match Rateだけでは不十分である

Teacherと異なるActionでも改善を生む場合がある。

重要なのは完全一致率だけではなく、次の値である。

- Actual Improvement
- Teacher Best Improvement
- Action Regret
- Prediction Error
- Stop Decision
- Repeated Action

### 5.4 Stopは独立した学習課題である

Seed 7は、Stroke選択が完全に崩れていなくてもStop判断に失敗した。

今後はStop Actionを単なる候補Actionの一つとして扱うだけでなく、
Stopの妥当性を独立して評価する必要がある。

### 5.5 Repeated ActionはValue推定の失敗と結びつく

Seed 10では、改善しないActionに対する正のPrediction Biasが観測された。

実際の改善が0でも高い価値を予測し続けると、
同じActionが反復される。

---

## 6. Phase 1の成果物

Phase 1では、少なくとも次の種類の成果物を生成できる。

```text
Model Checkpoint
Dataset
Training Metrics

result.json
trajectory.csv
trajectory-analysis.json

target.png
final_canvas.png
trajectory.gif

error-trajectory.png
improvement-trajectory.png
action-regret.png
action-sequence.png
```

これらにより、結果の目視確認、数値比較、再解析が可能になった。

公開対象の実験成果物は`results/`へ保存し、
再生成可能だが容量の大きい中間成果物は`artifacts/`で管理する。

---

## 7. Phase 1の到達点

Phase 1の到達点は、単にBehavior Cloning Modelを学習できたことではない。

より重要なのは、次の評価ループを構築したことである。

```text
Studentを実行する
        ↓
Teacherと比較する
        ↓
Trajectory上の失敗点を見つける
        ↓
失敗形態を分類する
        ↓
次の学習方法の改善対象を定義する
```

この基盤により、以後の手法を「最終画像が何となく良くなったか」ではなく、
具体的な閉ループ失敗が減ったかによって比較できる。

---

## 8. Phase 1の制約

Phase 1には次の制約が残る。

- Teacherが訪れたStateを中心にDatasetを生成している
- Student自身が訪れたStateが学習データに十分含まれない
- 中心的なTrajectory分析は少数Seedである
- 失敗形態の発生率を統計的に評価していない
- Stop Scoreの内部比較を保存していない
- 長周期のAction Cycleを検出していない
- EnvironmentとAction Spaceは最小構成である

これらはPhase 1の欠陥というより、Phase 2の研究課題を明確にするBaseline条件である。

---

## 9. Phase 2: DAgger

Phase 2ではDAggerを導入し、Student自身が訪れたStateをDatasetへ追加する。

基本ループは次の通りである。

```text
現在のStudentをRollout
        ↓
Studentが訪れたStateを収集
        ↓
各StateにTeacher Labelを付与
        ↓
既存Datasetへ追加
        ↓
Studentを再学習
        ↓
再評価
```

Phase 2では、Phase 1と同じ評価指標を使用し、次を比較する。

- Final Error
- Premature Stop Rate
- Repeated Action Failure Rate
- Oracle Action Match Rate
- Action Regret
- Prediction MAE
- Prediction Bias
- Zero Improvement Steps
- Max Steps到達率

---

## 10. Phase 2の成功条件

DAgger導入後に期待する変化は次の通りである。

### Premature Stopへの効果

Studentが停止したくなるStateをDatasetへ取り込み、
Teacherが選ぶ有効なStrokeを学習させる。

### Repeated Action Failureへの効果

StudentがLoopへ入るStateをDatasetへ取り込み、
同じState近傍でTeacherが選ぶ別Actionを学習させる。

### Prediction Errorへの効果

Student分布上のStateを追加することで、
改善量推定の過大評価または過小評価を減らす。

### 評価上の成功

Final Errorだけでなく、Phase 1で観測された失敗形態の発生率が下がることを成功条件とする。

---

## 11. 結論

Phase 1では、Painting Environmentに対するBehavior Cloningの
実装、実行、Teacher比較、Trajectory分析を一つの研究パイプラインとして構築した。

最も重要な成果は、Student Policyの失敗を次のように具体化できたことである。

```text
Premature Stop Failure
Repeated Action Failure
```

これにより、Phase 2でDAggerを導入する理由と、
改善を判定するためのBaselineが明確になった。

Phase 1は、Behavior Cloningの完成ではない。

> Behavior Cloningが閉ループでどのように失敗するかを観測し、
> 次の学習手法を比較するための基準を作った段階である。
