"""Build dashboard_data.json from volvedatacsv.csv.

Run:  python build_dashboard_data.py
No page loads the JSON yet; the pages read the CSV directly.
"""
import json

import pandas as pd

SM3_TO_BBL = 6.2898
SM3_TO_SCF = 35.3147

# 1. Load the raw data. The CSV writes volumes as "1,166", so thousands="," is required:
#    without it those values become NaN and every volume of 1,000 Sm3 or more is lost.
df = pd.read_csv("volvedatacsv.csv", encoding="latin1", thousands=",")

df.columns = df.columns.str.strip()
df = df.dropna(subset=["NPD_WELL_BORE_NAME"])
df["DATEPRD"] = pd.to_datetime(df["DATEPRD"], format="%d-%b-%y")

# Producers only: injector rows carry injected water, not production
df = df[df["FLOW_KIND"].str.strip().str.lower() == "production"].copy()
for col in ["BORE_OIL_VOL", "BORE_WAT_VOL", "BORE_GAS_VOL"]:
    df[col] = df[col].fillna(0)
df["PRODUCING"] = (df["BORE_OIL_VOL"] + df["BORE_WAT_VOL"]) > 0

# 2. Latest date on which any producer flowed (the file's final dates are shut-in rows).
#    Sorting the raw "07-Apr-14" strings would sort by day of month, not by date.
latest_date = df.loc[df["PRODUCING"], "DATEPRD"].max()
latest_df = df[(df["DATEPRD"] == latest_date) & df["PRODUCING"]]

# 3. Field KPIs
field_oil = latest_df["BORE_OIL_VOL"].sum() * SM3_TO_BBL
field_water = latest_df["BORE_WAT_VOL"].sum() * SM3_TO_BBL
field_gas = latest_df["BORE_GAS_VOL"].sum() * SM3_TO_SCF / 1_000_000

field_kpis = {
    "latestDate": latest_date.strftime("%Y-%m-%d"),
    "fieldOil": f"{field_oil:,.0f} BOPD",
    "fieldWater": f"{field_water:,.0f} BWPD",
    "fieldGas": f"{field_gas:,.2f} MMSCFD",
}

# 4. Full history for each well's charts
wells_historical = {}
wells_list = sorted(df["NPD_WELL_BORE_NAME"].unique())

for well in wells_list:
    well_df = df[df["NPD_WELL_BORE_NAME"] == well].sort_values("DATEPRD")
    oil = (well_df["BORE_OIL_VOL"] * SM3_TO_BBL).tolist()
    water = (well_df["BORE_WAT_VOL"] * SM3_TO_BBL).tolist()
    gas = (well_df["BORE_GAS_VOL"] * SM3_TO_SCF / 1_000_000).tolist()

    # "Current" = last day the well flowed, not the last row
    flowing = well_df[well_df["PRODUCING"]]
    last = flowing.iloc[-1] if len(flowing) else None

    wells_historical[well] = {
        "dates": well_df["DATEPRD"].dt.strftime("%Y-%m-%d").tolist(),
        "oil": oil,
        "water": water,
        "gas": gas,
        "peakOil": f"{max(oil):,.0f} BOPD",
        "peakWater": f"{max(water):,.0f} BWPD",
        "peakGas": f"{max(gas):,.2f} MMSCFD",
        "currentDate": last["DATEPRD"].strftime("%Y-%m-%d") if last is not None else None,
        "currentOil": f"{last['BORE_OIL_VOL'] * SM3_TO_BBL:,.0f} BOPD" if last is not None else "0 BOPD",
        "currentWater": f"{last['BORE_WAT_VOL'] * SM3_TO_BBL:,.0f} BWPD" if last is not None else "0 BWPD",
        "currentGas": f"{last['BORE_GAS_VOL'] * SM3_TO_SCF / 1_000_000:,.2f} MMSCFD" if last is not None else "0 MMSCFD",
    }

# 5. Screening snapshot on the latest producing day. Each well's oil and water rates are
#    compared with the field average for that day (health index > 1 = above average).
#      low oil, high water -> water shut-off candidate (water is displacing oil)
#      low oil, low water  -> stimulation candidate (low total liquid: productivity problem)
#      otherwise           -> good performance
wells_snapshot = []
avg_oil = latest_df["BORE_OIL_VOL"].mean()
avg_water = latest_df["BORE_WAT_VOL"].mean()

for _, row in latest_df.iterrows():
    oil_hi = row["BORE_OIL_VOL"] / avg_oil if avg_oil > 0 else 0
    wat_hi = row["BORE_WAT_VOL"] / avg_water if avg_water > 0 else 0

    status, color, priority, p_class = "Good Performance", "green", "Low", "priority-low"
    if oil_hi < 1.0 and wat_hi > 1.0:
        status, color = "Water Shut-Off Candidate", "blue"
        priority, p_class = ("High", "priority-high") if (wat_hi - oil_hi) > 1.0 else ("Medium", "priority-medium")
    elif oil_hi < 1.0 and wat_hi <= 1.0:
        status, color, priority, p_class = "Stimulation Candidate", "red", "Medium", "priority-medium"

    wells_snapshot.append({
        "name": str(row["NPD_WELL_BORE_NAME"]).strip(),
        "oilHI": round(oil_hi, 3),
        "waterHI": round(wat_hi, 3),
        "status": status,
        "color": color,
        "priority": priority,
        "priorityClass": p_class,
        "score": round(wat_hi - oil_hi, 3),
    })

wells_snapshot = sorted(wells_snapshot, key=lambda x: x["score"], reverse=True)

output_data = {
    "fieldKPIs": field_kpis,
    "wellsList": wells_list,
    "wellsHistorical": wells_historical,
    "screeningSnapshot": wells_snapshot,
}

with open("dashboard_data.json", "w") as f:
    json.dump(output_data, f, indent=4)

print(f"Successfully generated dashboard_data.json (latest producing day {field_kpis['latestDate']})")
