# ⚡ Electricity Outage Impact Prioritizer — GridRelief Local

A privacy-conscious, local-first decision-support platform for screening outage zones using critical-service dependency, water-supply dependency, heat risk, vulnerable residents, outage duration, access constraints, population exposure, and backup-power signals.

## Features
- 0–100 explainable impact-priority score
- Low / Moderate / High / Critical classification
- Zone-level factor explanations
- Restoration-priority screening queue
- Plotly analytics and local map
- CSV validation and scored export
- Synthetic data for demonstration
- 100% local processing with no external APIs

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 validate_data.py
python3 -m streamlit run app.py
```

This is decision-support only. It must not replace live utility control-room procedures, emergency protocols, grid-stability requirements, safety rules, or human judgment.
