# OptAgent Benchmarks

本目录是 OptAgent 的 benchmark 包，包含 benchmark case 声明、本地轻量运行入口，以及 presentation/dashboard 数据工具。建议从本目录运行命令：

```bash
cd /path/to/opt-agent/benchmarks
```

安装 OptAgent 后，可以直接通过 `python -m benchmarks...` 调用 benchmark 模块。

## `cases/` 模块

`cases/` 是 benchmark case 的声明层，负责定义每个可运行实例的元数据、问题类型、规模信息、建模方式和结果解码逻辑。这里不存放 dashboard 结果，只存放 `benchmarks.run`、suite runner 和 dashboard 能共同理解的 case 定义。1

`cases/` 的结构说明见 [cases/README.md](cases/README.md)。

## 数据来源

公开数据集、自定义数据和本地缓存都会放在 `cases/` 下对应的来源目录中，例如 `cases/tsplib/`、`cases/jsplib/`、`cases/miplib2017/`、`cases/psplib/`、`cases/qaplib/` 和 `cases/custom/`。每个来源目录都会提供自己的 `README.md`，用于说明该来源下有哪些 case，以及每个 case 对应的问题描述、数据含义和使用方式。

自定义钢卷序列示例的来源说明见 [cases/custom/README.md](cases/custom/README.md)。

## `run.py`

`run.py` 是本地单 case 运行入口。它会从 `cases/` 发现 benchmark case，构建对应的 OptAgent model，用一个或多个 strategy 求解，并把 JSON result rows 输出到 stdout。

列出当前可用 case：

```bash
python -m benchmarks.run --list-cases
```

运行一个不下载数据的 TSP smoke case：

```bash
python -m benchmarks.run \
  --case tsplib_berlin52 \
  --strategy ga \
  --no-download \
  --max-iterations 1 \
  --population-size 4 \
  --time-limit-s 0.1
```

用较小 GA 预算运行 QAP smoke case：

```bash
python -m benchmarks.run \
  --case qaplib_nug12 \
  --strategy ga \
  --no-download \
  --max-iterations 2 \
  --population-size 4 \
  --time-limit-s 1.0
```

运行自定义钢卷过渡排序 case：

```bash
python -m benchmarks.run \
  --case custom_steel_sequence_toy \
  --strategy ga \
  --max-iterations 2 \
  --population-size 4 \
  --time-limit-s 0.5
```

对比 TSP 的不同建模风格：

```bash
python -m benchmarks.run \
  --case tsplib_berlin52 \
  --strategy ga \
  --model-style sequence_var_external_call \
  --model-style sequence_var_sequence_transition_sum \
  --no-download \
  --max-iterations 2 \
  --population-size 4 \
  --time-limit-s 1.0
```

运行一个 MIP exact baseline：

```bash
python -m benchmarks.run \
  --case miplib2017_50v-10 \
  --strategy optx \
  --no-download \
  --time-limit-s 1.0
```

## 常用参数

- `--case <benchmark_id>`：选择单个 case；可重复传入多个 case。
- `--family <family>`：选择某个 family 下的 case。
- `--tier <smoke|calibration|full>`：按评测层级筛选 case。
- `--strategy <name>`：选择求解策略；可重复传入多个 strategy。
- `--model-style <style>`：为支持多建模风格的 family 指定 model style。
- `--no-download`：禁止下载数据；本地缺少 raw data 时直接失败。
- `--max-iterations`、`--time-limit-s`、`--population-size`、`--trace-limit`：本地运行预算参数。

## 程序化调用

也可以在 Python 代码中直接调用 `run_case()`：

```python
from benchmarks.run import LocalRunBudget, run_case

rows = run_case(
    "tsplib_berlin52",
    strategies=("ga",),
    allow_download=False,
    budget=LocalRunBudget(max_iterations=1, population_size=4, time_limit_s=0.1),
)
```

## 生成运行产物

如果需要 run directory、JSONL/CSV、telemetry、report 或 dashboard 发布输入，请使用 `presentation.suite`：

```bash
python -m benchmarks.presentation.suite \
  --family sequence_blackbox_tsp \
  --tier smoke \
  --strategy ga \
  --timestamp local-smoke
```

修改 `presentation/results/` 或 `presentation/aggregates/` 后，用下面的命令校验 dashboard 数据是否仍然同步：

```bash
python -m benchmarks.presentation.generate_dashboard_data --check
```

## 注意事项

- 部分 strategy 依赖 OptAgent native search。如果当前环境没有启用 native search，运行可能会产出类似 `native search unsupported` 的 error row。
- 长期 dashboard facts 存放在 `presentation/results/`；不要手工编辑生成的 index 或 aggregate JSON。
- 新增 case 时，solution 解码应放在 `solution_metrics()` 中；`sequence_head` 这类展示摘要由 `presentation/` 从 `decoded_solution` 派生。
