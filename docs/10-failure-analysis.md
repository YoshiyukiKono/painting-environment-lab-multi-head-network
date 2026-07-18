# 10. Failure Analysis

## 1. 今回の結果

Demo の結果は次の通りだった。

```text
final_error = 0.051479
steps = 16
stop_reason = policy_stop
```

生成物:

- [`../artifacts/target.png`](../artifacts/target.png)
- [`../artifacts/final_canvas.png`](../artifacts/final_canvas.png)
- [`../artifacts/trajectory.gif`](../artifacts/trajectory.gif)
- [`../artifacts/result.json`](../artifacts/result.json)

前回の即時終了とは異なり、今回は16回の Stroke を実行し、自律的に停止した。

## 2. 成功と失敗を分けて考える

最終画像がTargetを完全に再現していないことだけを見れば、実験は失敗に見える。

しかし、このリポジトリの目的は高品質な画像生成ではない。

検証対象は次である。

```text
離散 Stroke を学べるか
連続 Improvement を学べるか
その Improvement から Stop できるか
```

この三点については、明確な成功が確認できた。

したがって、今回の結果は次のように分類する必要がある。

```text
Architecture Validation:
成功

Image Reconstruction Quality:
未完成

Closed-loop Robustness:
未完成
```

## 3. 序盤の挙動

序盤では、予測改善量と実改善量がかなり一致していた。

```text
Step 1
predicted = 0.02220
actual    = 0.02228

Step 2
predicted = 0.02109
actual    = 0.02228

Step 3
predicted = 0.01467
actual    = 0.01628
```

この一致は、Improvement Head が単なる定数を出しているのではなく、状態に応じた改善量を予測していることを示す。

また、Stroke Head が選んだ Action も実際にErrorを減少させている。

## 4. 後半の挙動

後半では、予測改善量が実改善量より楽観的になる場面が現れた。

```text
predicted = 0.00396
actual    = 0.00085
```

```text
predicted = 0.00345
actual    = 0.00085
```

このずれは、Canvas が Teacher rollout states から外れ始めた可能性を示している。

Teacher Dataset は、Teacher が正しい Stroke を選び続けた軌跡で構成される。

Student が一度でも異なる Stroke を選ぶと、その後の Canvas は Teacher Dataset に存在しない可能性が高い。

```text
Teacher State
    ↓
Student Error
    ↓
Student-only State
    ↓
Prediction Error
```

## 5. 最終画像の粗さ

最終画像では、Target の滑らかなGradientが、シアンと青の大きな色面として近似されている。

この粗さには二種類の原因がある。

### Policyに由来する原因

- Teacher Stroke と異なる Action を選ぶ
- Student-only state で予測が崩れる
- 後半の Improvement prediction が過大評価になる

### Action Spaceに由来する原因

- 位置が8×8 Grid
- 半径が2種類
- Paletteが8色
- Stroke形状が円形
- 色の混合がない

後者は、学習を改善しても完全には消えない。

したがって、最終Errorを解釈するときは、Policy error と representation limit を分離する必要がある。

## 6. Stop判断

最後の予測値は負になった。

```text
predicted_improvement = -0.00021757
```

デフォルトThresholdは `1e-4` だったため、Policyは停止した。

これは、終了判断が独立したStop classを使わずに成立したことを示す。

一方、回帰値が負になること自体は、改善量の物理的定義とは一致しない。

Teacher label は0以上だが、標準化空間で線形回帰しているため、逆変換後に負値が出ることがある。

この点には、次の改善候補がある。

- 推論時に0でclipする
- Log-scale transformを使う
- 非負制約を持つ出力層を使う
- Stop marginとして負値を許容する

ただし、非負制約を入れるとStopの境界表現が難しくなる可能性もあるため、単純な修正ではない。

## 7. Threshold calibrationの問題

Calibrationでは次の値が出た。

```text
best_stop_accuracy = 0.9686
recommended_threshold = -0.003386
```

しかし、このThresholdはPredictionの最小値とほぼ同じである。

これはStop stateが少数であり、「ほぼすべてContinue」と判定するだけで高Accuracyが得られた可能性を示す。

したがって、Stop calibrationではAccuracyだけを使うべきではない。

必要な指標:

- Stop Precision
- Stop Recall
- F1 Score
- False Stop Rate
- Late Stop Rate
- Stop Step Gap
- Closed-loop Final Error

## 8. 今回のFailureの本質

今回の残課題は、Multi-head Networkが学習できないことではない。

本質は次である。

> Teacher states 上では学習できるが、Student rollout の後半で状態分布が変わる。

これはDAggerを導入する動機として、前回よりはるかに純粋で分かりやすい。

```text
前回:
Regression collapse

今回:
Closed-loop distribution shift
```

この切り分けができたこと自体が、今回の最大の成果である。
