# JSPLIB

This source contains job-shop scheduling instances from the
[ScheduleOpt JSPLIB archive](https://scheduleopt.github.io/benchmarks/jsplib/).
Instance JSON and best-known solutions originate from the linked ScheduleOpt
benchmark repository.

## Data And Model

Each job is an ordered operation chain. Every operation has a fixed machine and
duration. The model enforces job precedence and machine no-overlap constraints,
then minimizes makespan.

Independent verification reconstructs operation intervals, checks precedence
and machine capacity, and recomputes makespan without trusting solver summary
fields.

Use `benchmarks.run --list-cases` for current IDs, tiers, sizes, and references.
Downloaded source data belongs under the source's `raw/` directory.
