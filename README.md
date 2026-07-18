# painting-environment-lab-multi-head-network

Greedy Teacher の出力を使って、**一つの Shared CNN と二つの Head**を持つ Painting Policy を検証する教育用リポジトリです。

この段階では DAgger を使いません。

目的は、まず次の構造そのものが成立するかを切り分けることです。

```text
Observation
    │
    ▼
Shared CNN Encoder
    │
    ├──────────────► Stroke Head
    │                discrete classification
    │
    └──────────────► Improvement Head
                     continuous regression
```

## なぜ DAgger を外すのか

前段の実験では、Policy が最初の状態で即座に `Stop` を選びました。

```text
steps = 0
stop_reason = policy_stop
predicted_improvement ≈ 0
```

この状態では、Student rollout による状態分布の拡張以前に、Improvement Head 自体が正しく学習できていません。

したがって、このリポジトリでは次を順番に確認します。

1. Stroke Head は Greedy Stroke を学習できるか
2. Improvement Head は Greedy best improvement を学習できるか
3. 二つの Loss は Shared Encoder 上で両立するか
4. Improvement prediction を Stop に使えるか
5. Stop threshold は妥当か

DAgger は、これらが成立した後の次段階です。

## Repository Goal

このリポジトリの問いは一つです。

> Discrete Stroke classification と Continuous Improvement regression を、一つの Shared CNN で同時に学習できるか？

## Scope

含むもの:

- Greedy Teacher
- Teacher rollout dataset
- Shared CNN Encoder
- Stroke Head
- Improvement Head
- Multi-task loss
- Improvement normalization
- Log-scale regression option
- Weighted loss
- Separate-head diagnostics
- Stop threshold calibration
- Closed-loop rollout
- Ablation experiments

含まないもの:

- DAgger
- PPO
- Actor-Critic
- Replay Buffer
- Online RL
- Continuous Stroke action

## Key Improvement Ideas

### 1. Improvement normalization

生の `best_improvement` は値域が小さく、0付近に偏りやすいため、そのまま MSE を使うと collapse しやすくなります。

そこで、教師値を Dataset 全体の統計で標準化します。

```text
normalized =
(improvement - mean) / std
```

推論時に元のスケールへ戻します。

### 2. Log-scale target

改善量は桁が大きく異なることがあります。

```text
0.1
0.01
0.001
0.0001
```

そこで次も比較します。

```text
log_target = log1p(improvement / scale)
```

### 3. Stop classification auxiliary head is not used

Stop を独立した第三 Head にはしません。

このリポジトリでは、終了判断は Improvement prediction から導きます。

```text
predicted_improvement <= threshold
    → Stop
```

### 4. Separate diagnostics

学習中は、合計 Loss だけではなく次を個別に記録します。

```text
stroke_loss
stroke_accuracy
improvement_loss
improvement_mae
improvement_correlation
stop_precision
stop_recall
```

### 5. Warm-up training

最初から二つの Loss を同時に最適化すると、片方が Shared Encoder を支配する可能性があります。

そのため次の学習順も比較できます。

```text
Phase 1: Stroke Head only
Phase 2: Improvement Head only
Phase 3: Joint training
```

### 6. Threshold calibration

`1e-4` を固定値として盲目的に使いません。

Validation Dataset 上で複数候補を比較します。

```text
1e-2
1e-3
1e-4
1e-5
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Build Dataset

```bash
python scripts/build_dataset.py \
  --episodes 300 \
  --output artifacts/dataset.npz
```

### Train

```bash
python scripts/train.py \
  --dataset artifacts/dataset.npz \
  --epochs 20 \
  --target-transform standardized \
  --output artifacts/model.pt
```

### Diagnose

```bash
python scripts/diagnose.py \
  --dataset artifacts/dataset.npz \
  --model artifacts/model.pt
```

### Calibrate Stop Threshold

```bash
python scripts/calibrate_threshold.py \
  --dataset artifacts/dataset.npz \
  --model artifacts/model.pt
```

### Run Demo

```bash
python scripts/run_demo.py \
  --model artifacts/model.pt \
  --output-dir artifacts/demo
```

## Repository Structure

```text
.
├── README.md
├── pyproject.toml
├── src/painting_multi_head/
│   ├── action_space.py
│   ├── environment.py
│   ├── teacher.py
│   ├── model.py
│   ├── dataset.py
│   ├── transforms.py
│   ├── training.py
│   ├── diagnostics.py
│   ├── targets.py
│   ├── renderer.py
│   ├── palette.py
│   └── metrics.py
├── scripts/
│   ├── build_dataset.py
│   ├── train.py
│   ├── diagnose.py
│   ├── calibrate_threshold.py
│   └── run_demo.py
├── docs/
│   ├── 01-why-remove-dagger.md
│   ├── 02-one-network-two-heads.md
│   ├── 03-improvement-collapse.md
│   ├── 04-target-transforms.md
│   ├── 05-loss-balancing.md
│   ├── 06-threshold-calibration.md
│   └── 07-next-step-dagger.md
└── tests/
```

## Expected Learning Sequence

```text
Single-head Stroke classifier
    ↓
Single-head Improvement regressor
    ↓
Shared Encoder + Two Heads
    ↓
Loss balancing
    ↓
Threshold calibration
    ↓
Closed-loop rollout
    ↓
DAgger
```

この順番にすることで、DAgger を入れる前に Multi-head Network 自体の問題を切り分けられます。

## License

MIT
