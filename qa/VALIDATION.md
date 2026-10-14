# Engine validation - 2026-10-14

## Result

120,281 sizing cases completed with zero unexpected failures. 31 unit, regression and Streamlit interaction tests passed. Incompatible configurations are controlled rejections, not test failures.

## Coverage

| Stage | Cases | Accepted | Controlled rejections |
| --- | ---: | ---: | ---: |
| single-input grid | 66,310 | 65,253 | 1,057 |
| 2-input representative combinations | 2,079 | 1,778 | 301 |
| 3-input representative combinations | 41,580 | 32,945 | 8,635 |
| 7-control endpoint corners | 128 | 64 | 64 |
| 22-input seeded configurations | 10,000 | 2,717 | 7,283 |
| detailed model boundaries | 184 | 180 | 4 |

Single-input coverage includes every slider tick, declared bounded numeric increment, and representative values for unbounded fields. Pairs and triples include every subset of the 22 mission/advanced controls at minimum/default/maximum representative levels. Full designs include all 128 endpoint corners of the seven primary controls and 10,000 seeded configurations. The original detailed model is checked at each field minimum/default/maximum.

Streamlit tests exercise every mission input at boundaries/defaults, customer-control pair/triple interactions, combined configurations, saving/replacing scenarios, and every detailed-model field at boundaries/defaults. Tests verify no unhandled application exception; physical infeasibility errors are expected.

## Corrected defects

- Unlimited average solar credit previously overstated mission margin after the battery reached capacity. Margin now accounts for spilled harvest.
- Later harvest could mask insufficient pre-solar insertion energy. Insertion is independently checked.
- Recharge estimates were presented after crossing the station minimum energy threshold. Uninterrupted mission readiness is now withheld for those cases.
- Communications durations greater than 24 hours/day were accepted. These schedules now fail validation.
- Results-table numeric/text values were mixed; display values now share a consistent string type.

## Scope limits

- Single-input grid covers every slider tick and integer increment for bounded numeric inputs; bounded numeric controls use their declared increments; typed off-grid decimals and unbounded fields cannot be exhausted.
- Pairs/triples cover all parameter subsets at minimum/default/maximum representative levels, not every Cartesian tick.
- Full configurations cover seven-control endpoint corners and 10,000 seeded 22-input configurations.
- This checks model mathematics and software behavior; physical models remain preliminary.

Not every Cartesian pair/triple/full-grid combination was executed. Arbitrary typed decimal inputs and unbounded inputs cannot be exhaustively enumerated. No physical flight/sensing validation is implied. Average weather still does not model a sequence of bad days.

## Reproduce

```bash
python -m unittest discover -s tests -v
python qa/validate_engine.py
```
