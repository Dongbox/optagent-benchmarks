from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from optagent import ExternalCallbackContext, ModelBuilder

from benchmarks.cases.base import BenchmarkCase

SOURCE = "OptAgent custom"
SOURCE_KEY = "custom"
PROBLEM_TYPE = "production"
INSTANCE_TYPE = "steel_transition_sequence"
FAMILY = "sequence_transition_penalty"
MODEL_STYLE = "sequence_var_external_transition_penalty"
DATA_PATH = Path(__file__).resolve().parent / "data" / "steel_coils.json"
EPS = 1e-6


@dataclass(frozen=True)
class SteelCoilInstance:
    name: str
    coils: tuple[tuple[float, ...], ...]

    @property
    def coil_count(self) -> int:
        return len(self.coils)


class SteelSequenceCase(BenchmarkCase):
    def build_model(self, **kwargs: Any) -> ModelBuilder:
        instance = load_steel_instances()[self.instance]
        matrix = build_penalty_matrix(instance.coils)
        default_sequence = list(range(instance.coil_count))
        builder = ModelBuilder(metadata={"model_style": MODEL_STYLE})
        coil_sequence = builder.sequence_var(
            size=instance.coil_count,
            default=default_sequence,
            name="coil_sequence",
        )

        def transition_penalty(ctx: ExternalCallbackContext) -> int:
            sequence = [int(item) for item in ctx.value(coil_sequence)]
            return transition_count(sequence, matrix)

        builder.minimize(
            builder.external_call(
                transition_penalty,
                name="transition_penalty",
                pure=True,
                deterministic=True,
                cacheable=True,
                timeout_ms=100,
                depends_on=(coil_sequence,),
            ),
            name="transition_count",
        )
        self._set_build_context(
            {
                "instance": instance,
                "penalty_matrix": matrix,
                "sequence_node_id": coil_sequence.node_id,
            }
        )
        return builder

    def solution_metrics(self, solution: Any, **kwargs: Any) -> dict[str, Any]:
        context = self._build_context()
        instance = context["instance"]
        sequence = [int(item) for item in solution.variable_values[context["sequence_node_id"]]]
        objective = transition_count(sequence, context["penalty_matrix"])
        diagnostics = analyze_sequence(sequence, context["penalty_matrix"])
        return {
            "objective": float(objective),
            "model_style": MODEL_STYLE,
            "decoded_solution": {
                "kind": "sequence",
                "sequence": sequence,
            },
            "direct_weld_ratio": diagnostics["direct_weld_ratio"],
            "metadata": {
                "coils": instance.coil_count,
                "transition_count": objective,
                "direct_weld_count": diagnostics["direct_weld_count"],
                "pair_count": diagnostics["pair_count"],
                "first_break_positions": diagnostics["first_break_positions"],
            },
        }


def make_steel_case(
    *,
    instance: str,
    tier: str,
    coils: int,
    reference: dict[str, Any],
    case_module: str,
) -> SteelSequenceCase:
    compare_key = f"{SOURCE_KEY}/{PROBLEM_TYPE}/{INSTANCE_TYPE}/{instance}"
    return SteelSequenceCase(
        benchmark_id=f"custom_steel_sequence_{instance}",
        source=SOURCE,
        problem_type=PROBLEM_TYPE,
        instance_type=INSTANCE_TYPE,
        instance=instance,
        family=FAMILY,
        tier=tier,
        compare_key=compare_key,
        series_key=f"{compare_key}/{MODEL_STYLE}",
        size={"nodes": coils, "coils": coils},
        data={
            "data_path": str(DATA_PATH),
            "source_example": "opt-agent/examples/examples/steel",
        },
        reference=reference,
        problem_description=(
            f"Custom steel transition sequencing instance {instance}: order {coils} coils "
            "to minimize incompatible adjacent weld transitions."
        ),
        case_module=case_module,
        modeling_notes={
            "model_style": MODEL_STYLE,
            "objective_sense": "minimize",
            "public_api_primitives": ["sequence_var", "external_call"],
        },
    )


def load_steel_instances() -> dict[str, SteelCoilInstance]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    bundled = payload["bundled"]
    return {
        "toy": _instance("toy", payload["toy"]),
        "bundled_head40": _instance("bundled_head40", bundled[:40]),
        "bundled": _instance("bundled", bundled),
    }


def can_weld(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    (
        left_thick,
        left_thick_up,
        left_thick_down,
        left_width,
        left_width_down,
        left_width_up,
        left_temp,
        left_temp_up,
        left_temp_down,
    ) = left
    (
        right_thick,
        right_thick_up,
        right_thick_down,
        right_width,
        right_width_down,
        right_width_up,
        right_temp,
        right_temp_up,
        right_temp_down,
    ) = right
    return (
        right_thick_down - EPS <= left_thick <= right_thick_up + EPS
        and right_width_down - EPS <= left_width <= right_width_up + EPS
        and right_temp_down - EPS <= left_temp <= right_temp_up + EPS
        and left_thick_down - EPS <= right_thick <= left_thick_up + EPS
        and left_width_down - EPS <= right_width <= left_width_up + EPS
        and left_temp_down - EPS <= right_temp <= left_temp_up + EPS
    )


def build_penalty_matrix(coils: tuple[tuple[float, ...], ...]) -> list[list[int]]:
    return [
        [0 if left == right or can_weld(coils[left], coils[right]) else 1 for right in range(len(coils))]
        for left in range(len(coils))
    ]


def transition_count(sequence: list[int], penalty_matrix: list[list[int]]) -> int:
    return sum(penalty_matrix[sequence[index - 1]][sequence[index]] for index in range(1, len(sequence)))


def analyze_sequence(sequence: list[int], penalty_matrix: list[list[int]]) -> dict[str, Any]:
    penalties = [penalty_matrix[sequence[index - 1]][sequence[index]] for index in range(1, len(sequence))]
    first_break_positions = [index for index, penalty in enumerate(penalties, start=1) if penalty > 0][:10]
    pair_count = max(0, len(sequence) - 1)
    transition_total = sum(penalties)
    direct_weld_count = pair_count - transition_total
    return {
        "transition_count": transition_total,
        "direct_weld_count": direct_weld_count,
        "pair_count": pair_count,
        "direct_weld_ratio": direct_weld_count / pair_count if pair_count else 1.0,
        "first_break_positions": first_break_positions,
    }


def _instance(name: str, rows: list[list[float]]) -> SteelCoilInstance:
    return SteelCoilInstance(name=name, coils=tuple(tuple(float(value) for value in row) for row in rows))
