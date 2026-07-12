# Custom Cases

`custom/` contains benchmark-owned domain instances that are not mirrors of a
public benchmark collection.

The current steel transition-sequencing family orders coils while minimizing
penalties for adjacent coils that cannot be welded directly. It exercises
sequence variables and external transition-cost modeling at toy, reduced, and
bundled-data scales.

Key implementation files:

- `steel_transition_sequence/_domain.py`
- `steel_transition_sequence/toy.py`
- `steel_transition_sequence/bundled.py`
- `steel_transition_sequence/data/steel_coils.json`

Use `benchmarks.run --list-cases` for current IDs, tiers, sizes, and references.
Custom references require the same provenance and independent-verification
discipline as public-source cases.
