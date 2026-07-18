# 11. Hypotheses

この章では、今回の結果から導ける仮説を整理する。

仮説は結論ではない。

次の実験で否定可能な形にすることが重要である。

## H1. Multi-head Networkは成立している

### 仮説

Shared CNN Encoderを用いても、Stroke classificationとImprovement regressionは互いを破壊せず、同時に学習できる。

### 根拠

```text
stroke_accuracy = 0.8451
improvement_correlation = 0.9824
```

両方のHeadが意味のある性能を示した。

### 反証条件

次のような結果が出れば、この仮説は弱まる。

- Seedを変えると一方のHeadだけがcollapseする
- Improvement weightの変更でStroke Accuracyが大きく崩れる
- 単一Headモデルより両方とも明確に悪化する

## H2. 標準化がImprovement collapseを防いだ

### 仮説

Raw improvementを直接回帰するより、standardized targetを用いた方がゼロ近傍へのcollapseを防ぎやすい。

### 根拠

前段では即Stopしたが、今回はPrediction rangeが広がり、16 Strokeを実行できた。

### 反証条件

Raw / Standardized / Logの比較で、Rawが同等以上のCorrelationとClosed-loop性能を示す。

## H3. 後半の誤差はdistribution shiftによる

### 仮説

序盤より後半でPrediction errorが増える主因は、StudentがTeacher rolloutに存在しないCanvasへ移動するためである。

### 根拠

序盤のpredicted improvementとactual improvementは近い。

後半では過大評価が増えている。

### 反証条件

Student stateをTeacherに再ラベルしても誤差が改善しない。

その場合、原因はNetwork capacity、Observation design、Action representationなど別の箇所にある。

## H4. DAggerは後半のImprovement predictionを改善する

### 仮説

Studentが訪れたCanvasをTeacherに再ラベルしてDatasetへ追加すると、後半のPrediction errorが減少する。

### 期待する変化

- Improvement MAE低下
- 後半StepでのCorrelation改善
- actual improvementが0付近のStroke減少
- Stop timing改善
- repeated action streak減少

### 反証条件

DAgger後も後半のPrediction errorとFinal Errorが改善しない。

## H5. 最終画像の粗さの一部はAction Spaceの上限である

### 仮説

Current Action Spaceでは、完全なGradient再現は不可能または非常に困難である。

### 根拠

Paletteが8色、位置が8×8、半径が2種類に制限されている。

### 反証条件

同じAction Spaceを使うGreedy Teacherが、はるかに低いFinal Errorを安定して達成する。

その場合、粗さの主因はAction SpaceではなくPolicy imitationである。

## H6. Stop thresholdはDataset Accuracyだけでは決められない

### 仮説

Teacher-state Dataset上のStop Accuracyを最大化するThresholdは、Closed-loopで最適なThresholdとは一致しない。

### 根拠

CalibrationがPrediction minimum付近の負値を推奨した。

これはStop imbalanceの影響を受けている可能性が高い。

### 反証条件

Calibrationで得たThresholdが、複数SeedのClosed-loop評価でも最良のFinal ErrorとStop timingを示す。

## H7. Improvement HeadはCriticへの橋になる

### 仮説

現在のImprovement HeadはCriticではないが、将来のActor-Critic設計を理解する橋として機能する。

### 現在

```text
教師:
Greedy one-step best improvement
```

### 将来

```text
教師:
discounted cumulative return
```

Network structureは似ていても、学習対象は異なる。

### 反証条件

将来価値を学習する際に、現在のHead設計やFeature共有が大きく不適切であることが判明する。

## 仮説の優先順位

次に優先して検証すべき順序は次である。

```text
1. H3: 後半誤差はdistribution shiftか
2. H4: DAggerで改善するか
3. H6: Threshold calibration方法
4. H5: Action Space上限
5. H2: Target transform比較
6. H1: Multi-head安定性
7. H7: Actor-Criticへの接続
```

この順序は、現在観測されている失敗に最も近い原因から調べるためのものである。
