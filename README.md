# Tree Survey Analyser
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

A Python tool for analysing woodland tree survey data. Feed it a CSV of tree measurements and it generates a species breakdown, condition statistics, a carbon stock estimate, an interactive map, and a formatted PDF report.


## What it does

- **Species breakdown** — counts of each species present in the survey
- **Survey averages** — mean height and diameter across all trees
- **Condition statistics** — percentage of trees in good/fair/poor health, with poor-condition trees flagged individually
- **Carbon stock estimate** — per-tree and total carbon estimates using a simplified allometric biomass equation and species-specific wood density
- **Interactive map** — an HTML map (satellite imagery) with a coloured pin per tree, showing species, height, diameter, and condition on click, auto-centred on the surveyed area
- **PDF report** — a multi-page summary report with tree data and carbon estimate tables

## Installation

```bash
pip install folium reportlab
```

## Quick start

A small synthetic sample dataset is included so you can try the tool immediately without needing your own survey data. Its coordinates are placeholder values clustered near [Null Island](https://en.wikipedia.org/wiki/Null_Island) (0°, 0°) rather than a real location:

```bash
python3 tree_analyser.py sample_survey.csv
```

## Usage

```bash
python3 tree_analyser.py survey.csv
```

Optional arguments:

| Flag | Description |
|---|---|
| `--name "My Wood"` | Name of the survey/site, used in report titles and output filenames (default: derived from the CSV filename) |
| `--density-table densities.csv` | Optional CSV of `species,density` pairs to override or extend the built-in wood density lookup |
| `--outdir out/` | Directory to write the map and PDF into (default: current directory) |

Example:

```bash
python3 tree_analyser.py oakhurst_survey.csv --name "Oakhurst Wood" --outdir reports/
```

This prints a text report to the terminal and writes `oakhurst_wood_map.html` and `oakhurst_wood_report.pdf` to the `reports/` directory.

## Expected CSV format

The input CSV must contain the following columns:

| Column | Description |
|---|---|
| `species` | Tree species name |
| `height` | Height in metres |
| `diameter` | Diameter at breast height (DBH) in cm |
| `condition` | One of `good`, `fair`, or `poor` |
| `latitude` | Decimal latitude |
| `longitude` | Decimal longitude |

## Carbon estimation method

For each tree, above-ground biomass is estimated as:

```
biomass = 0.25 × diameter² × height × wood_density
carbon  = biomass × 0.5
```

This is a simplified allometric equation commonly used to estimate biomass from easily field-measured variables (diameter and height). Carbon content is assumed to be 50% of dry biomass, a standard rule of thumb in carbon accounting. Wood density values are species-specific specific-gravity figures; species not in the built-in table fall back to a generic value of 0.60, or you can supply your own via `--density-table`.

## Notes

This is a self-directed project built for learning and personal woodland survey work — the carbon estimation method is a simplified approximation, not a substitute for formal forestry carbon accounting methodologies.
