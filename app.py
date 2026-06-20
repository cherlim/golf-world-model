import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

from simulator import CLUBS, simulate_shot


st.title("Golf World Model Demo — Version 0.4")

st.write(
    "This demo shows a simple world model: current state + action → predicted futures → distance-to-pin evaluation → decision recommendation."
)

with open(Path("course.json"), "r") as f:
    course = json.load(f)

wind = st.slider("Wind (-20 to 20)", -20, 20, 0)
aim = st.slider("Aim Angle", -20, 20, 0)
num_shots = st.slider("Number of simulated futures per club", 50, 500, 200)


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def classify_shot(x, y):
    point = [x, y]

    green_center = course["green"]["center"]
    green_radius = course["green"]["radius"]
    if distance(point, green_center) <= green_radius:
        return "Green"

    for bunker in course["bunkers"]:
        if distance(point, bunker["center"]) <= bunker["radius"]:
            return "Bunker"

    water = course["water"]
    if water["x_min"] <= x <= water["x_max"] and water["y_min"] <= y <= water["y_max"]:
        return "Water"

    fairway = course["fairway"]
    if (
        fairway["x_min"] <= x <= fairway["x_max"]
        and fairway["y_min"] <= y <= fairway["y_max"]
    ):
        return "Fairway"

    return "Rough"


def evaluate_club(club):
    shots = [simulate_shot(club, aim, wind) for _ in range(num_shots)]
    outcomes = [classify_shot(x, y) for x, y in shots]

    pin = course["green"]["center"]
    distances_to_pin = [distance([x, y], pin) for x, y in shots]
    avg_distance_to_pin = sum(distances_to_pin) / len(distances_to_pin)

    green = outcomes.count("Green") / num_shots
    fairway = outcomes.count("Fairway") / num_shots
    rough = outcomes.count("Rough") / num_shots
    bunker = outcomes.count("Bunker") / num_shots
    water = outcomes.count("Water") / num_shots
    hazard = bunker + water

    # Version 0.4 utility score:
    # Reward being close to the pin.
    # Reward green/fairway.
    # Penalize hazards strongly.
    score = (
        120
        - avg_distance_to_pin
        + green * 80
        + fairway * 25
        - rough * 10
        - bunker * 50
        - water * 100
    )

    return {
        "club": club,
        "shots": shots,
        "green": green,
        "fairway": fairway,
        "rough": rough,
        "bunker": bunker,
        "water": water,
        "hazard": hazard,
        "avg_distance_to_pin": avg_distance_to_pin,
        "score": score,
    }


results = [evaluate_club(club) for club in CLUBS.keys()]
best = max(results, key=lambda r: r["score"])

st.subheader("AI Recommendation")

st.success(f"Recommended club: {best['club']}")

st.write(
    f"""
The world model simulated **{num_shots} possible futures** for each club.

It now recommends **{best['club']}** by considering:
- probability of reaching the green
- probability of staying on the fairway
- hazard risk
- average distance to the pin
"""
)

st.subheader("Action Comparison")

table_data = []
for r in results:
    table_data.append(
        {
            "Club": r["club"],
            "Green": f"{r['green']:.1%}",
            "Fairway": f"{r['fairway']:.1%}",
            "Rough": f"{r['rough']:.1%}",
            "Bunker": f"{r['bunker']:.1%}",
            "Water": f"{r['water']:.1%}",
            "Hazard": f"{r['hazard']:.1%}",
            "Avg Dist to Pin": round(r["avg_distance_to_pin"], 1),
            "Score": round(r["score"], 1),
        }
    )

st.table(table_data)

selected_club = st.selectbox(
    "Choose a club to visualize",
    list(CLUBS.keys()),
    index=list(CLUBS.keys()).index(best["club"]),
)

selected_result = next(r for r in results if r["club"] == selected_club)
shots = selected_result["shots"]

fig, ax = plt.subplots(figsize=(10, 5))

fairway = course["fairway"]
ax.add_patch(
    patches.Rectangle(
        (fairway["x_min"], fairway["y_min"]),
        fairway["x_max"] - fairway["x_min"],
        fairway["y_max"] - fairway["y_min"],
        alpha=0.2,
    )
)
ax.text(120, 0, "Fairway", ha="center", va="center")

water = course["water"]
ax.add_patch(
    patches.Rectangle(
        (water["x_min"], water["y_min"]),
        water["x_max"] - water["x_min"],
        water["y_max"] - water["y_min"],
        alpha=0.4,
    )
)
ax.text(205, -38, "Water", ha="center", va="center")

green = course["green"]
ax.add_patch(
    patches.Circle(
        green["center"],
        green["radius"],
        alpha=0.4,
    )
)
ax.text(green["center"][0], green["center"][1], "Green", ha="center", va="center")

for bunker in course["bunkers"]:
    ax.add_patch(
        patches.Circle(
            bunker["center"],
            bunker["radius"],
            alpha=0.4,
        )
    )
    ax.text(
        bunker["center"][0],
        bunker["center"][1],
        "Bunker",
        ha="center",
        va="center",
        fontsize=8,
    )

xs = [s[0] for s in shots]
ys = [s[1] for s in shots]
ax.scatter(xs, ys, s=20, alpha=0.7)

pin = course["green"]["center"]
ax.scatter([pin[0]], [pin[1]], marker="*", s=250)
ax.text(pin[0] + 3, pin[1] + 3, "Pin")

ax.set_xlim(0, 360)
ax.set_ylim(-80, 80)
ax.set_xlabel("Distance")
ax.set_ylabel("Lateral Position")
ax.set_title(f"Predicted Futures for {selected_club}")
ax.grid(True)

st.pyplot(fig)

st.subheader("World Model Interpretation")

st.write(
    """
Version 0.4 improves the reward model.

The AI is no longer choosing the safest club only. It now asks:

**Which action produces future states that are both safe and close to the target?**

This gives us a clearer world-model pattern:

**state → possible actions → predicted futures → reward evaluation → decision**
"""
)