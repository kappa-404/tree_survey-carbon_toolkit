import argparse
import csv
import os

import folium  # type: ignore
from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore

# default carbon/wood density values (Mg/m3) - used if a species isn't
# in the survey-specific table below, or no lookup is supplied
DEFAULT_WOOD_DENSITY = {
    "Oak": 0.75,
    "English Oak": 0.75,
    "Sessile Oak": 0.75,
    "Scots Pine": 0.55,
    "Beech": 0.72,
    "Silver Birch": 0.60,
    "Hazel": 0.60,
    "Field Maple": 0.67,
    "Ash": 0.67,
    "Wild Cherry": 0.63,
    "Hornbeam": 0.78,
    "Yew": 0.67,
    "Holly": 0.78,
}
FALLBACK_DENSITY = 0.60  # used for any species not in the table above


def load_trees(csv_path):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def estimate_carbon_kg(tree, density_table):
    dbh = float(tree["diameter"])
    height = float(tree["height"])
    density = density_table.get(tree["species"], FALLBACK_DENSITY)
    biomass = 0.25 * (dbh ** 2 * height) * density
    return biomass * 0.5


def print_report(trees, survey_name, density_table):
    print(f"=== {survey_name.upper()} TREE SURVEY REPORT ===")
    print("total trees surveyed: " + str(len(trees)))
    print("")

    # species breakdown
    print("--- SPECIES BREAKDOWN ---")
    species_count = {}
    for tree in trees:
        species = tree["species"]
        species_count[species] = species_count.get(species, 0) + 1
    for species, count in species_count.items():
        label = "tree" if count == 1 else "trees"
        print(f"{species}: {count} {label}")

    # averages
    print("")
    print("--- SURVEY AVERAGES ---")
    total_height = sum(float(t["height"]) for t in trees)
    total_dbh = sum(float(t["diameter"]) for t in trees)
    avg_height = total_height / len(trees)
    avg_dbh = total_dbh / len(trees)
    print("average height: " + str(round(avg_height, 2)) + "m")
    print("average diameter: " + str(round(avg_dbh, 2)) + "cm")

    # health percentages
    good = sum(1 for t in trees if t["condition"] == "good")
    fair = sum(1 for t in trees if t["condition"] == "fair")
    poor = sum(1 for t in trees if t["condition"] == "poor")
    print("good condition: " + str(round(good / len(trees) * 100)) + "%")
    print("fair condition: " + str(round(fair / len(trees) * 100)) + "%")
    print("poor condition: " + str(round(poor / len(trees) * 100)) + "%")
    print("")

    # flag poor condition trees
    print("--- TREES IN POOR CONDITION ---")
    for tree in trees:
        if tree["condition"] == "poor":
            print(tree["species"] + " - height: " + tree["height"] + "m, diameter: " + tree["diameter"] + "cm")

    # carbon stock estimate
    print("")
    print("--- CARBON STOCK ESTIMATE ---")
    total_carbon = 0
    for tree in trees:
        carbon = estimate_carbon_kg(tree, density_table)
        total_carbon += carbon
        print(tree["species"] + ": " + str(round(carbon, 2)) + " kg carbon")

    print("")
    print("total carbon stock: " + str(round(total_carbon, 2)) + " kg")
    print("equivalent to: " + str(round(total_carbon / 1000, 3)) + " tonnes")

    return total_carbon


def make_map(trees, output_path):
    # centre the map on the average position of the surveyed trees,
    # rather than a fixed location, so this works for any site
    lats = [float(t["latitude"]) for t in trees]
    lons = [float(t["longitude"]) for t in trees]
    centre = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=centre, zoom_start=17, tiles="Esri.WorldImagery")

    colour_map = {"good": "green", "fair": "orange", "poor": "red"}

    for i, tree in enumerate(trees):
        tree_num = "T" + str(i + 1)
        condition = tree["condition"]
        colour = colour_map.get(condition, "blue")
        popup = (
            "<b>" + tree_num + " - " + tree["species"] + "</b><br>"
            "Height: " + tree["height"] + "m<br>"
            "DBH: " + tree["diameter"] + "cm<br>"
            "Condition: " + condition
        )
        folium.Marker(
            location=[float(tree["latitude"]), float(tree["longitude"])],
            popup=folium.Popup(popup, max_width=200),
            icon=folium.Icon(color=colour),
        ).add_to(m)

    m.save(output_path)
    print("")
    print(f"map saved to {output_path}")


def make_pdf(trees, survey_name, density_table, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 60, f"{survey_name} Tree Survey Report")
    c.line(50, height - 95, width - 50, height - 95)

    # summary
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 125, "Survey Summary")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 145, "Total trees surveyed: " + str(len(trees)))

    good = sum(1 for t in trees if t["condition"] == "good")
    fair = sum(1 for t in trees if t["condition"] == "fair")
    poor = sum(1 for t in trees if t["condition"] == "poor")

    c.drawString(50, height - 165, "Good condition: " + str(round(good / len(trees) * 100)) + "%")
    c.drawString(50, height - 182, "Fair condition: " + str(round(fair / len(trees) * 100)) + "%")
    c.drawString(50, height - 199, "Poor condition: " + str(round(poor / len(trees) * 100)) + "%")

    total_height = sum(float(t["height"]) for t in trees)
    total_dbh = sum(float(t["diameter"]) for t in trees)
    c.drawString(50, height - 219, "Average height: " + str(round(total_height / len(trees), 2)) + "m")
    c.drawString(50, height - 236, "Average DBH: " + str(round(total_dbh / len(trees), 2)) + "cm")

    total_carbon = sum(estimate_carbon_kg(t, density_table) for t in trees)
    c.drawString(50, height - 256, "Total carbon stock: " + str(round(total_carbon / 1000, 3)) + " tonnes")

    c.line(50, height - 270, width - 50, height - 270)

    # tree table
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 295, "Tree Data")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 315, "Tree")
    c.drawString(100, height - 315, "Species")
    c.drawString(250, height - 315, "Height")
    c.drawString(310, height - 315, "DBH")
    c.drawString(370, height - 315, "Condition")
    c.line(50, height - 320, width - 50, height - 320)

    c.setFont("Helvetica", 11)
    y = height - 335
    for i, tree in enumerate(trees):
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 50
        c.drawString(50, y, "T" + str(i + 1))
        c.drawString(100, y, tree["species"])
        c.drawString(250, y, tree["height"] + "m")
        c.drawString(310, y, tree["diameter"] + "cm")
        c.drawString(370, y, tree["condition"])
        y -= 17

    # carbon table
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 60, "Carbon Stock Estimates")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 85, "Tree")
    c.drawString(100, height - 85, "Species")
    c.drawString(280, height - 85, "Carbon (kg)")
    c.drawString(390, height - 85, "Carbon (tonnes)")
    c.line(50, height - 90, width - 50, height - 90)

    c.setFont("Helvetica", 11)
    y = height - 108
    for i, tree in enumerate(trees):
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 50
        carbon = estimate_carbon_kg(tree, density_table)
        c.drawString(50, y, "T" + str(i + 1))
        c.drawString(100, y, tree["species"])
        c.drawString(280, y, str(round(carbon, 2)))
        c.drawString(390, y, str(round(carbon / 1000, 4)))
        y -= 17

    c.drawString(50, y - 10, "TOTAL CARBON STOCK: " + str(round(total_carbon / 1000, 3)) + " tonnes")

    c.save()
    print(f"PDF saved to {output_path}")


def load_density_table(path):
    """Optional CSV with columns 'species,density' to override/extend the defaults."""
    table = dict(DEFAULT_WOOD_DENSITY)
    if path:
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                table[row["species"]] = float(row["density"])
    return table


def main():
    parser = argparse.ArgumentParser(
        description="Analyse a tree survey CSV: species breakdown, condition stats, "
        "carbon stock estimate, an interactive map, and a PDF report."
    )
    parser.add_argument("csv_file", help="Path to the survey CSV (columns: species, height, diameter, condition, latitude, longitude)")
    parser.add_argument("--name", default=None, help="Name of the survey/site, used in report titles (default: derived from the CSV filename)")
    parser.add_argument("--density-table", default=None, help="Optional CSV of species,density to override the built-in wood density lookup")
    parser.add_argument("--outdir", default=".", help="Directory to write the map and PDF into (default: current directory)")
    args = parser.parse_args()

    survey_name = args.name or os.path.splitext(os.path.basename(args.csv_file))[0].replace("_", " ").title()
    density_table = load_density_table(args.density_table)

    trees = load_trees(args.csv_file)
    if not trees:
        print("No trees found in CSV - nothing to report.")
        return

    print_report(trees, survey_name, density_table)

    os.makedirs(args.outdir, exist_ok=True)
    slug = survey_name.lower().replace(" ", "_")
    make_map(trees, os.path.join(args.outdir, f"{slug}_map.html"))
    make_pdf(trees, survey_name, density_table, os.path.join(args.outdir, f"{slug}_report.pdf"))


if __name__ == "__main__":
    main()

# run with: python3 tree_analyser.py path/to/survey.csv
# optional: --name "My Wood" --density-table densities.csv --outdir out/
