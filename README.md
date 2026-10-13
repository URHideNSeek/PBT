# PBT — Pigeon Bot Trade Engine

Streamlit aircraft + unattended perched sensor sizing app. Explore parameters before selecting parts.

## Run (Python 3.11+)
```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Edit grouped sidebar parameters; inspect mission energy and closure checks; save named designs to the trade matrix; sweep parameters; export CSV or JSON. Comparison scenarios are session-local. Import individual scenario JSON to restore it. Bundle JSON is an archive of individual records.

Defaults are analysis assumptions: strictly under 20 lb aircraft, under 16-inch solar surface and under 12-inch assembled props; 95% initial SOC; separate analysis SOC floor and Wh reserve. One steady wind vector governs both reciprocal legs. No headwind-on-both-legs case or parts-sourcing model.

## Model and limits

See the Model & assumptions tab and model.py. Cruise power is reference-calibrated and scales with mass, prop diameter and drag. Hover uses momentum theory. Battery capacity is coupled to installed mass; thermal/aging derating is explicit. Solar is a normalized daylight profile with capacity clipping. Activity energy is spread uniformly and loads are incremental. Reserve is counted once.

PASS means preliminary mathematical closure under assumptions, not verified aircraft performance. Detailed packaging/CG, folding clearance, perch strength, motor/ESC constraints, battery sag, sensor effectiveness, RF link margins and transient thermal behavior remain unmodeled. No noise or RPM results are invented. These models need test calibration before design release.

No database, authentication or public deployment is included. Run locally or in an access-controlled hosting environment.

## Tests
```bash
python -m unittest discover -s tests -v
```
Tests cover mass, reciprocal and crosswind behavior, infeasible routes, energy/reserve accounting, battery mass coupling, geometry boundaries, nighttime solar, invalid inputs, and Streamlit editing/saving.

## Quick launch and private hosting

See [DEPLOYMENT.md](DEPLOYMENT.md) for Windows / macOS launch scripts and private-server container setup.
