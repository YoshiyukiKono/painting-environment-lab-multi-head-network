# Multi-head Network 実行結果

## 目的

DAgger を導入する前に、Shared CNN + Multi-head Network 自体が成立するかを検証した。

## 結果

- Step数: 16
- Stop理由: policy_stop
- Final Error: 約0.0515

## 考察

### 成功した点

- Improvement Head が学習できた。
- 予測改善量に基づいて Stop できた。
- 白紙終了ではなく、自律的に16手描画した。

### 残っている課題

- 後半では予測改善量と実改善量にずれが生じる。
- Canvas が Teacher の分布から外れると性能が低下する。
- これは Multi-head の失敗ではなく、closed-loop の分布シフトである可能性が高い。

## 次の研究

Multi-head Network は一旦成立とみなし、次段階で DAgger を導入し、
後半の分布シフトを改善できるか比較する。

## 添付

artifacts/
- target.png
- final_canvas.png
- trajectory.gif
- result.json
