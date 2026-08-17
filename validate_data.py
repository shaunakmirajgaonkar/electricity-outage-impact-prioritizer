
from pathlib import Path
import pandas as pd

REQUIRED = [
    "zone_id","zone_name","latitude","longitude","hospital_dependency","water_supply_dependency",
    "heat_risk","vulnerable_resident_index","critical_facility_dependency","outage_duration_hours",
    "medical_facility_count","water_facility_count","population_exposed","building_density",
    "road_access_constraint","backup_power_coverage","recent_outage_count"
]
path=Path(__file__).parent/"data"/"outage_zone_registry.csv"
df=pd.read_csv(path)
missing=[c for c in REQUIRED if c not in df.columns]
if missing: raise SystemExit("Missing columns: "+", ".join(missing))
if df.empty: raise SystemExit("Dataset is empty")
print(f"Records: {len(df)}")
print("Status: OK")
