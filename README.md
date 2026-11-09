# Volve well-by-well review

Static dashboards for the Volve field daily production data, published with GitHub Pages.

| Page | What it shows |
|---|---|
| `index.html` | Oil, water and gas rates per well, with peak, current and field KPIs |
| `water_analysis.html` | Water rate, water cut and a Chan (1995) WOR diagnostic plot |
| `stimulation_screening.html` | Oil rate against downhole pressure, with a simple screening flag |

All three pages read `volvedatacsv.csv` in the browser (PapaParse + Plotly). Shared parsing lives in
`common.js` and shared styling in `style.css`.

## Data notes

- Volumes in the CSV are written with thousands separators (`"1,166"`). They must be parsed with the
  commas removed, otherwise every value of 1,000 Sm3/d or more is read as zero.
- Rows with `FLOW_KIND = injection` are excluded: they hold injected water, not production.
- The last dates in the file are shut-in rows, so "current" values use the last day each well flowed
  and field totals use the last day any producer flowed (17 Sep 2016).
- A downhole pressure of 0 bar means the gauge was not reporting and is treated as missing.

## Other files

- `build_dashboard_data.py` regenerates `dashboard_data.json` (run `python build_dashboard_data.py`).
- `Module1 (1).ipynb` is the exploratory notebook; its outputs were cleared after the parsing fix and
  should be re-run.
- `Volve production data.xlsx` is the original spreadsheet the CSV was exported from.

Data: Volve field production data, released by Equinor under its open data licence.
