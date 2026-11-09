import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(
    page_title="Volve Well Review",
    layout="wide"
)

# Load Data

df = pd.read_csv(
    "volvedatacsv.csv",
    encoding="latin1"
)

df["DATEPRD"] = pd.to_datetime(
    df["DATEPRD"],
    format="%d-%b-%y"
)

# Numeric conversion

for col in [
    "BORE_OIL_VOL",
    "BORE_WAT_VOL",
    "BORE_GAS_VOL",
    "AVG_DOWNHOLE_PRESSURE"
]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# Unit conversions

SM3_TO_BBL = 6.2898
SM3_TO_SCF = 35.3147
BAR_TO_PSI = 14.5038

df["OIL_BOPD"] = (
    df["BORE_OIL_VOL"] *
    SM3_TO_BBL
)

df["WATER_BWPD"] = (
    df["BORE_WAT_VOL"] *
    SM3_TO_BBL
)

df["GAS_MMSCFD"] = (
    df["BORE_GAS_VOL"]
    * SM3_TO_SCF
    / 1_000_000
)

df["DHP_PSI"] = (
    df["AVG_DOWNHOLE_PRESSURE"]
    * BAR_TO_PSI
)

df["WC"] = (
    df["BORE_WAT_VOL"]
    /
    (
        df["BORE_OIL_VOL"]
        + df["BORE_WAT_VOL"]
    )
) * 100

df["GOR"] = (
    df["BORE_GAS_VOL"]
    * SM3_TO_SCF
    /
    (
        df["BORE_OIL_VOL"]
        * SM3_TO_BBL
    )
)

# Sidebar

well_list = sorted(
    df["NPD_WELL_BORE_NAME"]
    .dropna()
    .unique()
)

selected_well = st.sidebar.selectbox(
    "Select Well",
    well_list
)

well = df[
    df["NPD_WELL_BORE_NAME"]
    == selected_well
].copy()

well = well.sort_values(
    "DATEPRD"
)

st.title(
    f"Well Review Dashboard: {selected_well}"
)

# KPI Dashboard

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Peak Oil",
    f"{well['OIL_BOPD'].max():,.0f} BOPD"
)

col2.metric(
    "Peak Water",
    f"{well['WATER_BWPD'].max():,.0f} BWPD"
)

col3.metric(
    "Peak Gas",
    f"{well['GAS_MMSCFD'].max():.2f} MMSCFD"
)

col4.metric(
    "Current WC",
    f"{well['WC'].iloc[-1]:.1f}%"
)

# Plot 1

fig, ax1 = plt.subplots(figsize=(12,5))

ax1.plot(
    well["DATEPRD"],
    well["OIL_BOPD"],
    color="green"
)

ax1.set_ylabel(
    "Oil Rate (BOPD)"
)

ax2 = ax1.twinx()

ax2.plot(
    well["DATEPRD"],
    well["DHP_PSI"],
    color="black",
    linestyle="--"
)

ax2.set_ylabel(
    "Pressure (psi)"
)

st.pyplot(fig)
