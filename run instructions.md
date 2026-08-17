# Run Instructions

```bash
cd electricity_outage_impact_prioritizer
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 validate_data.py
python3 -m streamlit run app.py
```
