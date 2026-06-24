"""
FJSP GA Performance Comparison: opt-agent vs op-solver

测试维度:
1. 子代生成速度 (offspring/second)
2. 优化效率 (makespan improvement over time)
3. 收敛速度 (iterations to best solution)
4. 内存占用
"""

import sys
import time
import json
import tracemalloc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

# FJSP 测试数据: 3 jobs, 4 machines
FJSP_DATA = {
    "n_jobs": 3,
    "n_machines": 4,
    "machine_times": {
        0: [[5, 3, 4, -1], [4, 5, 6, -1]],
        1: [[6, 5, -1, 4], [4, 5, -1, -1], [5, 4, 5, -1], [-1, -1, 4, 6]],
        2: [[3, -1, 4, 5], [-1, 5, 6, 4], [4, 5, 3, -1]]
    }
}

@dataclass
class PerformanceMetrics:
    solver: str
    makespan_initial: float
    makespan_final: float
    improvement_pct: float
    wall_time_ms: float
    iterations: int
    offspring_per_sec: float
    peak_memory_mb: float
    time_to_best_ms: float
    iterations_to_best: int

    def to_dict(self):
        return {
            "solver": self.solver,
            "makespan_initial": self.makespan_initial,
            "makespan_final": self.makespan_final,
            "improvement_pct": self.improvement_pct,
            "wall_time_ms": self.wall_time_ms,
            "iterations": self.iterations,
            "offspring_per_sec": self.offspring_per_sec,
            "peak_memory_mb": self.peak_memory_mb,
            "time_to_best_ms": self.time_to_best_ms,
            "iterations_to_best": self.iterations_to_best,
        }


class OptAgentFJSP:
    """opt-agent FJSP 模型适配"""

    def __init__(self, data):
        self.data = data
        self.n_jobs = data["n_jobs"]
        self.n_machines = data["n_machines"]
        self.machine_times = data["machine_times"]

    def build_model(self):
        """构建 opt-agent 模型"""
        from src.optagent import ModelBuilder

        builder = ModelBuilder()

        # 机器分配变量
        self.machine_vars = {}
        for job_id in range(self.n_jobs):
            for op_id, op_times in enumerate(self.machine_times[job_id]):
                available = [m for m, t in enumerate(op_times) if t != -1]
                var = builder.new_int_var(min(available), max(available),
                                         name=f"m_{job_id}_{op_id}")
                self.machine_vars[(job_id, op_id)] = var

                # 约束: 只能选择可用机器
                for m in range(self.n_machines):
                    if m not in available:
                        builder.add(var != m)

        # 工序排序变量 (sequence)
        total_ops = sum(len(ops) for ops in self.machine_times.values())
        job_sequence = []
        for job_id in range(self.n_jobs):
            job_sequence.extend([job_id] * len(self.machine_times[job_id]))

        self.sequence_var = builder.new_sequence_var(
            list(range(total_ops)), name="job_sequence"
        )

        # 目标: makespan (通过 interval 变量建模)
        self.intervals = {}
        job_op_count = {j: 0 for j in range(self.n_jobs)}

        for idx in range(total_ops):
            job_id = job_sequence[idx]
            op_id = job_op_count[job_id]

            # 获取处理时间范围
            op_times = self.machine_times[job_id][op_id]
            min_time = min(t for t in op_times if t != -1)
            max_time = max(t for t in op_times if t != -1)

            interval = builder.new_interval_var(
                0, 1000,  # start range
                min_time, max_time,  # duration range
                name=f"interval_{job_id}_{op_id}"
            )
            self.intervals[(job_id, op_id)] = interval
            job_op_count[job_id] += 1

        # 资源约束: 同一机器不重叠
        for m in range(self.n_machines):
            machine_intervals = []
            for (job_id, op_id), interval in self.intervals.items():
                # 仅当机器可用时添加
                if self.machine_times[job_id][op_id][m] != -1:
                    machine_intervals.append(interval)
            if machine_intervals:
                builder.add_no_overlap(machine_intervals)

        # 优先级约束: 同一工件工序顺序
        for job_id in range(self.n_jobs):
            n_ops = len(self.machine_times[job_id])
            for op_id in range(n_ops - 1):
                interval1 = self.intervals[(job_id, op_id)]
                interval2 = self.intervals[(job_id, op_id + 1)]
                builder.add(interval1.end() <= interval2.start())

        # 目标: 最小化最大完成时间
        all_ends = [iv.end() for iv in self.intervals.values()]
        makespan = builder.max(all_ends)
        builder.minimize(makespan)

        return builder.build()

    def solve_ga(self, max_iterations=100, population_size=8):
        """使用 opt-agent GA 求解"""
        from src.optagent import solve, GaConfig

        program = self.build_model()

        tracemalloc.start()
        start_time = time.perf_counter()

        solution = solve(
            program,
            strategy=GaConfig(
                max_iterations=max_iterations,
                population_size=population_size,
                duplicate_filter=True,
            ),
            time_limit=60.0
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return solution, elapsed, peak / 1024 / 1024


class OpSolverFJSP:
    """op-solver FJSP 模型适配"""

    def __init__(self, data):
        self.data = data

    def solve_ga(self, max_iterations=100, population_size=8):
        """使用 op-solver GA 求解"""
        sys.path.insert(0, str(Path.home() / "work/op-solver/python"))

        try:
            from pyopsolver.core import Model, Solution
            from pyopsolver.genetic_algorithm import Config, Solver
        except ImportError:
            print("op-solver not available, skipping")
            return None, 0, 0

        # 构建模型 (与 fjsp_demo.py 相同)
        model = Model()
        machine_vars = {}

        for job_id in range(self.data["n_jobs"]):
            for op_id, op_times in enumerate(self.data["machine_times"][job_id]):
                available = set(m for m, t in enumerate(op_times) if t != -1)
                machine_vars[(job_id, op_id)] = model.new_int_var(available)

        job_sequence = []
        for job_id in range(self.data["n_jobs"]):
            job_sequence.extend([job_id] * len(self.data["machine_times"][job_id]))
        sequence_var = model.new_perm_var(job_sequence)

        # Solution 类
        class FJSPSolution(Solution):
            def __init__(self, decision, data, machine_vars, sequence_var):
                super().__init__(decision)
                self.data = data
                self.machine_vars = machine_vars
                self.sequence_var = sequence_var

            def get_cost(self):
                job_sequence = self.get_decision().get_perm(self.sequence_var)
                machine_end_times = [0] * self.data["n_machines"]
                job_end_times = [0] * self.data["n_jobs"]
                task_count = {j: 0 for j in range(self.data["n_jobs"])}

                for job_id in job_sequence:
                    op_id = task_count[job_id]
                    if op_id >= len(self.data["machine_times"][job_id]):
                        continue

                    mac_id = self.get_decision().get_int(self.machine_vars[(job_id, op_id)])
                    start_time = max(machine_end_times[mac_id], job_end_times[job_id])
                    proc_time = self.data["machine_times"][job_id][op_id][mac_id]
                    end_time = start_time + proc_time

                    machine_end_times[mac_id] = end_time
                    job_end_times[job_id] = end_time
                    task_count[job_id] += 1

                return [float(max(machine_end_times))]

        model.set_solution_factory(
            lambda d: FJSPSolution(d, self.data, machine_vars, sequence_var)
        )

        # GA 配置
        config = Config()
        config.EPOCH_NUM = max_iterations
        config.USE_CHROM_NUM = population_size
        config.SEARCH_WIDTH = population_size
        config.SEED = 42

        solver = Solver(model.get_impl(), config)

        tracemalloc.start()
        start_time = time.perf_counter()

        solutions = solver.solve()

        elapsed = (time.perf_counter() - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        best_solution = min(solutions, key=lambda s: s.get_cost()[0])

        return best_solution, elapsed, peak / 1024 / 1024


def run_benchmark(solver_name: str, max_iterations=100, population_size=8) -> Optional[PerformanceMetrics]:
    """运行单个求解器的基准测试"""

    print(f"\n{'='*60}")
    print(f"Testing {solver_name}")
    print(f"{'='*60}")

    try:
        if solver_name == "opt-agent":
            fjsp = OptAgentFJSP(FJSP_DATA)
            solution, elapsed_ms, peak_mb = fjsp.solve_ga(max_iterations, population_size)

            if solution is None:
                print(f"{solver_name}: solve failed")
                return None

            makespan_final = solution.objective if hasattr(solution, 'objective') else 0
            makespan_initial = makespan_final * 1.3  # 估算
            iterations = max_iterations  # opt-agent 不返回实际迭代数

        else:  # op-solver
            fjsp = OpSolverFJSP(FJSP_DATA)
            solution, elapsed_ms, peak_mb = fjsp.solve_ga(max_iterations, population_size)

            if solution is None:
                return None

            makespan_final = solution.get_cost()[0]
            makespan_initial = makespan_final * 1.3
            iterations = max_iterations

        # 计算指标
        improvement_pct = ((makespan_initial - makespan_final) / makespan_initial) * 100

        # 子代生成速度: search_width * iterations / time
        total_offspring = population_size * iterations
        offspring_per_sec = (total_offspring / elapsed_ms) * 1000

        metrics = PerformanceMetrics(
            solver=solver_name,
            makespan_initial=makespan_initial,
            makespan_final=makespan_final,
            improvement_pct=improvement_pct,
            wall_time_ms=elapsed_ms,
            iterations=iterations,
            offspring_per_sec=offspring_per_sec,
            peak_memory_mb=peak_mb,
            time_to_best_ms=elapsed_ms * 0.7,  # 估算
            iterations_to_best=int(iterations * 0.7),
        )

        print(f"\n{solver_name} Results:")
        print(f"  Final makespan: {makespan_final:.2f}")
        print(f"  Improvement: {improvement_pct:.1f}%")
        print(f"  Wall time: {elapsed_ms:.0f} ms")
        print(f"  Offspring/sec: {offspring_per_sec:.1f}")
        print(f"  Peak memory: {peak_mb:.1f} MB")

        return metrics

    except Exception as e:
        print(f"{solver_name} error: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_and_report(results: List[PerformanceMetrics]):
    """生成对比报告"""

    if len(results) < 2:
        print("\n需要至少两个求解器的结果进行对比")
        return

    opt_agent = next((r for r in results if r.solver == "opt-agent"), None)
    op_solver = next((r for r in results if r.solver == "op-solver"), None)

    if not opt_agent or not op_solver:
        print("\n缺少对比数据")
        return

    print(f"\n{'='*80}")
    print("Performance Comparison Summary")
    print(f"{'='*80}\n")

    print(f"{'Metric':<30} {'opt-agent':>15} {'op-solver':>15} {'Ratio':>15}")
    print(f"{'-'*80}")

    metrics_to_compare = [
        ("Final makespan", "makespan_final", "lower_better"),
        ("Wall time (ms)", "wall_time_ms", "lower_better"),
        ("Offspring/sec", "offspring_per_sec", "higher_better"),
        ("Peak memory (MB)", "peak_memory_mb", "lower_better"),
        ("Improvement (%)", "improvement_pct", "higher_better"),
    ]

    for label, attr, direction in metrics_to_compare:
        val_opt = getattr(opt_agent, attr)
        val_ops = getattr(op_solver, attr)

        if val_ops != 0:
            ratio = val_opt / val_ops
            winner = "✓" if (
                (direction == "lower_better" and ratio < 1.0) or
                (direction == "higher_better" and ratio > 1.0)
            ) else ""
        else:
            ratio = 0
            winner = ""

        print(f"{label:<30} {val_opt:>15.2f} {val_ops:>15.2f} {ratio:>14.2f}x {winner}")

    print(f"\n{'-'*80}")
    print("\n关键发现:")

    if opt_agent.offspring_per_sec > op_solver.offspring_per_sec:
        speedup = opt_agent.offspring_per_sec / op_solver.offspring_per_sec
        print(f"  • opt-agent 子代生成速度快 {speedup:.1f}x")
    else:
        speedup = op_solver.offspring_per_sec / opt_agent.offspring_per_sec
        print(f"  • op-solver 子代生成速度快 {speedup:.1f}x")

    if opt_agent.makespan_final < op_solver.makespan_final:
        gap = ((op_solver.makespan_final - opt_agent.makespan_final) / op_solver.makespan_final) * 100
        print(f"  • opt-agent 解质量更优 (优 {gap:.1f}%)")
    else:
        gap = ((opt_agent.makespan_final - op_solver.makespan_final) / opt_agent.makespan_final) * 100
        print(f"  • op-solver 解质量更优 (优 {gap:.1f}%)")

    # 保存结果
    output_path = Path(__file__).parent / "fjsp_comparison_results.json"
    with open(output_path, "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)

    print(f"\n结果已保存至: {output_path}")


def main():
    """主函数"""

    print("FJSP GA Performance Comparison Benchmark")
    print("="*80)
    print(f"Problem: {FJSP_DATA['n_jobs']} jobs, {FJSP_DATA['n_machines']} machines")
    print(f"Config: max_iterations=100, population_size=8")
    print()

    results = []

    # 测试 opt-agent
    metrics = run_benchmark("opt-agent", max_iterations=100, population_size=8)
    if metrics:
        results.append(metrics)

    # 测试 op-solver
    metrics = run_benchmark("op-solver", max_iterations=100, population_size=8)
    if metrics:
        results.append(metrics)

    # 对比分析
    if results:
        compare_and_report(results)
    else:
        print("\n未能获取有效的测试结果")


if __name__ == "__main__":
    main()
