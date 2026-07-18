# 09. Design Review

## 1. この実験で検証した設計

今回の実験では、Painting Policy を一つの分類問題として扱わず、次の二つの出力へ分けた。

```text
Observation
    │
    ▼
Shared CNN Encoder
    │
    ├──────────────► Stroke Head
    │                離散分類
    │
    └──────────────► Improvement Head
                     連続回帰
```

### Stroke Head

Stroke Head は有限個の Stroke 候補から一つを選ぶ。

現在の Action Space は、概念的には次の直積で構成される。

```text
位置 × 半径 × 色
```

この離散化は、将来の Physical Robot との対応を意識したものである。

たとえば、実機では次のような有限操作へ対応できる。

- 移動可能な位置
- 使用可能なノズル径またはブラシ径
- 準備された有限 Palette
- 実行可能な筆圧や描画モード

したがって、Stroke を離散値として維持することは、単なる学習上の簡略化ではなく、物理操作との対応を保つための設計でもある。

### Improvement Head

Improvement Head は、Greedy Teacher が計算した `best_improvement` を連続値として予測する。

終了判断は独立した Stop class ではなく、次の規則から導く。

```text
predicted_improvement <= stop_threshold
    → Stop
```

これにより、Stroke と Stop を同じ分類空間へ押し込める必要がなくなる。

## 2. なぜ二つの Head を使うのか

Stroke 選択と終了判断は、性質が異なる。

```text
Stroke:
どの操作を実行するか

Stop:
追加操作に価値があるか
```

前者は選択問題、後者は評価問題である。

この違いを明示的に分離するため、二つの Head を使用した。

ただし、ネットワーク全体が二つ存在するわけではない。

```text
Target + Canvas
      │
      ▼
Shared CNN
      │
      ▼
Shared Feature
   ┌──┴──┐
   ▼     ▼
Stroke  Improvement
```

入力画像の特徴抽出は共通化され、その後の判断だけが分岐する。

## 3. 今回の設計で改善した点

前段の実験では、Improvement Head がほぼゼロへ collapse し、最初の状態で即座に Stop した。

今回のリポジトリでは、その問題に対して次を導入した。

### Improvement target の標準化

```text
normalized =
(improvement - mean) / std
```

教師値のスケールを整えることで、ゼロ付近への collapse を抑えた。

### SmoothL1Loss

極端な誤差に引きずられにくい回帰 Loss として `SmoothL1Loss` を採用した。

### 個別診断

合計 Loss だけではなく、次を個別に確認した。

- Stroke Accuracy
- Improvement MAE
- Improvement Correlation
- Teacher Improvement Mean
- Predicted Improvement Mean
- Predicted Improvement Range

その結果、次の値が得られた。

```text
stroke_accuracy             0.8451
improvement_mae             0.00153
improvement_correlation     0.9824
teacher_improvement_mean    0.01055
predicted_improvement_mean  0.01037
```

この結果から、二つの Head は少なくとも Teacher rollout states 上では同時に学習できたと判断できる。

## 4. 設計上の制約

今回の設計には、次の制約が残る。

### Greedy Teacher 依存

Improvement Head が学習するのは、Greedy Teacher の one-step improvement である。

これは将来の累積価値ではない。

```text
現在:
Immediate Improvement

将来の Actor-Critic:
Expected Return
```

したがって、この Head をそのまま Critic と呼ぶことはできない。

### 固定 Action Space

Stroke Head が選べるのは、あらかじめ定義した有限候補だけである。

Action Space に存在しない Stroke は、どれだけ学習しても生成できない。

### Teacher states 中心の Dataset

Dataset は Greedy Teacher rollout から作られている。

Student が一度誤った後に到達する Canvas は、Dataset に十分含まれていない。

## 5. 現時点の設計判断

この実験の範囲では、次の判断が妥当である。

```text
Shared CNN + Two Heads
    → 成立

Discrete Stroke
    → 維持

Continuous Improvement
    → 成立

Improvement-derived Stop
    → 成立

DAgger
    → 次段階
```

Multi-head Network 自体は、一旦成立したとみなせる。

次に調べるべき問題は、Network architecture ではなく、Student rollout による distribution shift である。
