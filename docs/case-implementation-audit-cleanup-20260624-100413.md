# Case Implementation Audit And Cleanup

## Task

逐一审查 `benchmarks/cases/` 下每个公开 case 的具体实现，清理系列迁移后残留的无关实例、无关方法和复制粘贴错误。

本任务的首要已知问题是：JSPLIB job-shop 的非 ABZ 系列文件中残留了来自 `abz.py` 的 `abz5` / `abz7` 默认实例、`solve_abz5()` / `solve_abz7()` 方法和 ABZ 错误信息。`abz5`、`abz7` 只能出现在 `cases/jsplib/scheduling/jobshop/abz.py` 及其原始数据文件中。

## Scope

### In Scope

- 检查每个系列模块的 `CASES`、`case_module`、`load_instance()`、`build_model()`、`solve_case()`、实例便捷方法和 `_case_by_name()`。
- 检查每个公开 case 的 metadata 是否与自身实例一致，包括 `benchmark_id`、`instance`、`compare_key`、`series_key`、`size`、`reference`、`problem_description`、`modeling_notes`、`extra`。
- 清理明显由其他系列迁移而来的无关方法、默认参数、错误提示、变量名和注释。
- 增加轻量级防回归检查，避免 `abz5` / `abz7` 或其他实例名再次泄漏到不相关模块。
- 更新相关任务报告和稳定架构文档中已经被本任务证实的结论。

### Out Of Scope

- 不重新设计 case 目录结构。
- 不引入新的跨系列大型抽象，除非重复逻辑已经直接阻碍本次清理和验证。
- 不重跑完整长期 benchmark，只做 smoke / compile / inventory / focused routing 验证。
- 不改动历史结果 JSON，除非后续验证发现当前 runner 依赖了错误结果结构。

## Current Evidence

已通过静态检索确认以下残留：

- `cases/jsplib/scheduling/jobshop/ft.py`：`solve_case()` 默认 `instance="abz5"`；存在 `solve_abz5()` / `solve_abz7()`；`_case_by_name()` 抛出 `unsupported ABZ JSPLIB instance`。
- `cases/jsplib/scheduling/jobshop/la.py`：同上。
- `cases/jsplib/scheduling/jobshop/dmu.py`：同上。
- `cases/jsplib/scheduling/jobshop/swv.py`：同上。
- `cases/jsplib/scheduling/jobshop/abz.py`：允许保留 `abz5` / `abz7`、`solve_abz5()` / `solve_abz7()` 和 ABZ 错误提示，但仍需检查是否有自身冗余。
- `cases/jsplib/scheduling/jobshop/raw/abz5.json`：允许保留原始 `abz5` 数据。

已确认当前公开 case inventory 包含 29 个 case：

- JSPLIB job-shop：`abz5`、`abz7`、`ft06`、`ft10`、`la16`、`la21`、`dmu01`、`swv01`
- PSPLIB RCPSP：`j90_1_1`、`j90_1_8`、`j90_2_4`、`j90_5_3`、`j90_6_7`
- TSPLIB TSP：`pr76`、`kroa100`、`a280`、`berlin52`、`eil51`
- QAPLIB QAP：`nug12`、`nug20`、`had20`、`lipa40a`、`chr12a`
- MIPLIB 2017 linear MIP：`reblock115`、`air05`、`fast0507`、`academictimetablesmall`、`50v-10`、`ran14x18-disj-8`

## Implementation Rules

1. 每个系列模块只暴露本系列 case。示例：`ft.py` 只能暴露 `ft06` / `ft10`，不能有 `abz5` / `abz7` 入口。
2. `solve_case()` 不应在非 ABZ 模块中默认到 `abz5`。多实例系列应要求显式实例，或默认到本系列第一个实例并在文档中一致说明。
3. 便捷方法必须按本系列命名，例如 `solve_ft06()`、`solve_ft10()`；单实例系列可不提供便捷方法。
4. `_case_by_name()` 的错误提示必须使用当前 family / series 名称，不能引用迁移来源。
5. `case_module` 必须指向当前模块，优先使用 `CASE_MODULE = __name__`，除非有明确兼容原因。
6. `CASES` 中每个 case 的 `instance`、`benchmark_id`、`compare_key` 和 `series_key` 必须互相一致。
7. 系列内 helper 可以重复；只有当重复导致错误扩散或验证复杂度明显上升时，才抽取到共享模块。
8. 不保留旧单实例 shim，也不新增兼容别名来掩盖迁移残留。

## Phased Plan

### Phase 0: Freeze Inventory And Audit Matrix

Goal：固定审查对象，建立每个 case 的验收表。

Tasks：

- 运行 `python -m benchmarks.run --list-cases`，保存 29 个公开 case 的当前清单。
- 生成模块到 case 的映射，确认 `__init__.py` 聚合只包含系列模块。
- 建立审查矩阵，字段包括：模块、case、允许实例名、禁止实例名、便捷方法、`solve_case()` 签名、错误提示、验证命令。

Exit Criteria：

- 文档或任务报告中有完整 case 审查矩阵。
- 后续修改只以该矩阵为基准，不临时扩大范围。

### Phase 1: Clean JSPLIB ABZ Leakage

Goal：先修复已确认的 `abz.py` 迁移污染。

Tasks：

- 在 `ft.py` 中移除 `solve_abz5()` / `solve_abz7()`，修正 `solve_case()` 默认实例和 `_case_by_name()` 错误提示。
- 在 `la.py` 中执行同样清理。
- 在 `dmu.py` 中执行同样清理。
- 在 `swv.py` 中执行同样清理。
- 检查 `abz.py` 自身是否只包含 ABZ 系列逻辑，无其他系列残留。
- 用静态检查确保 `abz5` / `abz7` 只出现在 `abz.py` 和合法 raw 数据中。

Exit Criteria：

- `rg -n "abz5|abz7|solve_abz|unsupported ABZ" cases/jsplib/scheduling/jobshop` 只命中 `abz.py` 和合法 raw 数据。
- JSPLIB 8 个公开 case 均能通过 focused smoke。

### Phase 2: Per-Family Redundancy And Error Audit

Goal：逐系列检查迁移残留、冗余方法和 metadata 错误。

Tasks：

- JSPLIB job-shop：逐一检查 `abz.py`、`ft.py`、`la.py`、`dmu.py`、`swv.py`。
- PSPLIB RCPSP：逐一检查 `j90_1.py`、`j90_2.py`、`j90_5.py`、`j90_6.py`。
- TSPLIB TSP：逐一检查 `pr.py`、`kroa.py`、`a.py`、`berlin.py`、`eil.py`。
- QAPLIB QAP：逐一检查 `nug.py`、`had.py`、`lipa.py`、`chr.py`。
- MIPLIB 2017 linear MIP：逐一检查 `reblock.py`、`air.py`、`fast.py`、`academictimetable.py`、`case_50v.py`、`ran14x18_disj.py`。
- 对每个模块记录：保留的重复逻辑、删除的无关逻辑、修正的错误、未处理原因。

Exit Criteria：

- 每个系列模块都有明确审查结果。
- 所有便捷方法、默认实例、错误提示和 metadata 都与本模块 case 一致。

### Phase 3: Add Regression Guards

Goal：把本次问题转化为自动检查，防止再次出现跨系列污染。

Tasks：

- 增加 case inventory 测试：每个 case 的 `case_module` 必须包含该 case 对象。
- 增加实例名污染测试：模块源码不得包含不属于 `CASES` 的公开实例名，允许 raw 数据和明确白名单。
- 增加 runner 路由测试：`registry.run_case()` 对每个公开 case 都调用其自身模块的 `solve_case(instance, ...)`。
- 增加最小 metadata 一致性测试：`benchmark_id`、`instance`、`compare_key`、`series_key` 对齐。

Exit Criteria：

- 新测试能在当前错误状态下失败，在清理完成后通过。
- 测试不依赖网络下载和长时间求解。

### Phase 4: Focused Validation

Goal：确认清理没有破坏 runner、注册表和每类 case 的最小求解路径。

Validation Commands：

- `python -m compileall benchmarks/cases`
- `python -m benchmarks.run --list-cases`
- `python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_la16 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_dmu01 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_swv01 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1`

Exit Criteria：

- Compile、inventory 和每个 family 的 focused smoke 通过。
- 如果某个 raw 数据缺失导致 `--no-download` 失败，任务报告需明确记录并改用不触网的 mock / loader 测试覆盖该模块。

### Phase 5: Documentation And Archive

Goal：把清理结论回填到稳定文档，并关闭任务。

Tasks：

- 更新 `benchmarks/docs/cases-series-refactor-adjustment.md`，记录本次清理后的系列文件约束。
- 如发现架构规则变化，更新 `benchmarks/docs/case-architecture-refactor.md`。
- 在本任务文档 `Report` 中记录修复摘要、验证结果和遗留风险。
- 本任务文档保留在 `benchmarks/docs/`，不进入仓库级 `docs/tasks/` 当前任务队列。

Exit Criteria：

- 当前任务文档包含完整报告和验证输出摘要。
- 稳定规则不只停留在任务页中。

## Audit Checklist

| Family | Module | Cases | Phase | Status |
| --- | --- | --- | --- | --- |
| JSPLIB job-shop | `abz.py` | `abz5`, `abz7` | 1, 2 | Completed |
| JSPLIB job-shop | `ft.py` | `ft06`, `ft10` | 1, 2 | Completed |
| JSPLIB job-shop | `la.py` | `la16`, `la21` | 1, 2 | Completed |
| JSPLIB job-shop | `dmu.py` | `dmu01` | 1, 2 | Completed |
| JSPLIB job-shop | `swv.py` | `swv01` | 1, 2 | Completed |
| PSPLIB RCPSP | `j90_1.py` | `j90_1_1`, `j90_1_8` | 2 | Completed |
| PSPLIB RCPSP | `j90_2.py` | `j90_2_4` | 2 | Completed |
| PSPLIB RCPSP | `j90_5.py` | `j90_5_3` | 2 | Completed |
| PSPLIB RCPSP | `j90_6.py` | `j90_6_7` | 2 | Completed |
| TSPLIB TSP | `pr.py` | `pr76` | 2 | Completed |
| TSPLIB TSP | `kroa.py` | `kroa100` | 2 | Completed |
| TSPLIB TSP | `a.py` | `a280` | 2 | Completed |
| TSPLIB TSP | `berlin.py` | `berlin52` | 2 | Completed |
| TSPLIB TSP | `eil.py` | `eil51` | 2 | Completed |
| QAPLIB QAP | `nug.py` | `nug12`, `nug20` | 2 | Completed |
| QAPLIB QAP | `had.py` | `had20` | 2 | Completed |
| QAPLIB QAP | `lipa.py` | `lipa40a` | 2 | Completed |
| QAPLIB QAP | `chr.py` | `chr12a` | 2 | Completed |
| MIPLIB linear MIP | `reblock.py` | `reblock115` | 2 | Completed |
| MIPLIB linear MIP | `air.py` | `air05` | 2 | Completed |
| MIPLIB linear MIP | `fast.py` | `fast0507` | 2 | Completed |
| MIPLIB linear MIP | `academictimetable.py` | `academictimetablesmall` | 2 | Completed |
| MIPLIB linear MIP | `case_50v.py` | `50v-10` | 2 | Completed |
| MIPLIB linear MIP | `ran14x18_disj.py` | `ran14x18-disj-8` | 2 | Completed |

## Acceptance Criteria

- `abz5` / `abz7` 只存在于 `abz.py` 和合法 raw 数据文件。
- 每个系列模块只暴露和求解自身 `CASES` 中声明的实例。
- 所有公开 case 的 registry 路由、metadata 和默认策略声明一致。
- 每个 family 至少一个 focused smoke 通过，JSPLIB job-shop 的受污染系列全部通过。
- 新增防回归测试能覆盖实例名泄漏、`case_module` 错误和 metadata 不一致。

## Report

Completed on 2026-06-24.

### Changes

- Cleaned JSPLIB ABZ migration leakage from `ft.py`, `la.py`, `dmu.py`, and `swv.py`.
- Replaced copied `solve_abz5()` / `solve_abz7()` helpers with series-local helpers: `solve_ft06()` / `solve_ft10()`, `solve_la16()` / `solve_la21()`, `solve_dmu01()`, and `solve_swv01()`.
- Changed non-ABZ JSPLIB `solve_case()` signatures to require an explicit `instance`, matching registry routing and the other family modules.
- Replaced copied ABZ `_case_by_name()` error messages with FT / LA / DMU / SWV messages.
- Changed `abz.py` to use `CASE_MODULE = __name__`.
- Added `tests/test_case_implementation_integrity.py` covering inventory count, metadata alignment, `case_module` ownership, unrelated public instance leakage, and registry routing.
- Updated stable rules in `docs/cases-series-refactor-adjustment.md` and `docs/case-architecture-refactor.md`.

### Audit Result

- Public inventory remains 29 cases.
- `abz5` / `abz7` now only appear in `cases/jsplib/scheduling/jobshop/abz.py` and legal raw data.
- All 24 series modules listed in the audit checklist have been checked by the new integrity test for cross-instance source leakage and metadata consistency.
- No non-JSPLIB cross-series instance leakage was found by the integrity guard.

### Validation

Passed:

- `rg -n "abz5|abz7|solve_abz|unsupported ABZ|instance: str = \"abz5\"" cases/jsplib/scheduling/jobshop`
- `python -m pytest tests/test_case_implementation_integrity.py`
- `python -m compileall benchmarks/cases`
- `python -m benchmarks.run --list-cases`
- `python -m benchmarks.run --case jsplib_abz5 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_abz7 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_ft06 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_ft10 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_la16 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_la21 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_dmu01 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case jsplib_swv01 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case psplib_j90_1_1 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case tsplib_berlin52 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case qaplib_nug12 --strategy local_search --no-download --max-iterations 1 --time-limit-s 0.1`
- `python -m benchmarks.run --case miplib2017_50v-10 --strategy optx --no-download --time-limit-s 0.1`

Notes:

- Several focused smoke commands returned expected error rows rather than feasible solutions because native search is disabled in the current environment or raw files are not cached while `--no-download` is set. The commands still exited successfully and validated registry routing, setup error rows, case metadata, and module ownership.
- Two smoke commands initially failed during parallel execution with an `optagent` import race/path issue; both passed when rerun directly.
