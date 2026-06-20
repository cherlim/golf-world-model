import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

from simulator import CLUBS, simulate_shot


st.title("Golf World Model Demo")

st.write(
    "This demo shows a simple world model: current state + action → many possible future outcomes."
)

# Load course
with open(Path("course.json"), "r") as f:
    course = json.load(f)

club = st.selectbox("Club", list(CLUBS.keys()))
wind = st.slider("Wind (-20 to 20)", -20, 20, 0)
aim = st.slider("Aim Angle", -20, 20, 0)
num_shots = st.slider("Number of simulated futures", 50, 500, 200)


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def classify_shot(x, y):
    point = [x, y]

    # Green
    green_center = course["green"]["center"]
    green_radius = course["green"]["radius"]
    if distance(point, green_center) <= green_radius:
        return "Green"

    # Bunkers
    for bunker in course["bunkers"]:
        if distance(point, bunker["center"]) <= bunker["radius"]:
            return "Bunker"

    # Water
    water = course["water"]
    if (
        water["x_min"] <= x <= water["x_max"]
        and water["y_min"] <= y <= water["y_max"]
    ):
        return "Water"

    # Fairway
    fairway = course["fairway"]
    if (
        fairway["x_min"] <= x <= fairway["x_max"]
        and fairway["y_min"] <= y <= fairway["y_max"]
    ):
        return "Fairway"

    return "Rough"


# Simulate many futures
shots = [simulate_shot(club, aim, wind) for _ in range(num_shots)]
outcomes = [classify_shot(x, y) for x, y in shots]

# Count outcomes
outcome_counts = {}
for outcome in outcomes:
    outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

st.subheader("Predicted Outcome Probabilities")

for outcome in ["Green", "Fairway", "Rough", "Bunker", "Water"]:
    count = outcome_counts.get(outcome, 0)
    probability = count / num_shots
    st.write(f"{outcome}: {probability:.1%}")

# Plot course
fig, ax = plt.subplots(figsize=(10, 5))

# Fairway
fairway = course["fairway"]
fairway_patch = patches.Rectangle(
    (fairway["x_min"], fairway["y_min"]),
    fairway["x_max"] - fairway["x_min"],
    fairway["y_max"] - fairway["y_min"],
    alpha=0.2,
)
ax.add_patch(fairway_patch)
ax.text(120, 0, "Fairway", ha="center", va="center")

# Water
water = course["water"]
water_patch = patches.Rectangle(
    (water["x_min"], water["y_min"]),
    water["x_max"] - water["x_min"],
    water["y_max"] - water["y_min"],
    alpha=0.4,
)
ax.add_patch(water_patch)
ax.text(205, -38, "Water", ha="center", va="center")

# Green
green = course["green"]
green_patch = patches.Circle(
    green["center"],
    green["radius"],
    alpha=0.4,
)
ax.add_patch(green_patch)
ax.text(green["center"][0], green["center"][1], "Green", ha="center", va="center")

# Bunkers
for bunker in course["bunkers"]:
    bunker_patch = patches.Circle(
        bunker["center"],
        bunker["radius"],
        alpha=0.4,
    )
    ax.add_patch(bunker_patch)
    ax.text(
        bunker["center"][0],
        bunker["center"][1],
        "Bunker",
        ha="center",
        va="center",
        fontsize=8,
    )

# Shot futures
xs = [s[0] for s in shots]
ys = [s[1] for s in shots]
ax.scatter(xs, ys, s=20, alpha=0.7)

# Pin / target
ax.scatter([320], [0], marker="*", s=250)
ax.text(323, 3, "Pin")

ax.set_xlim(0, 360)
ax.set_ylim(-80, 80)
ax.set_xlabel("Distance")
ax.set_ylabel("Lateral Position")
ax.set_title("Predicted Futures on Course Map")
ax.grid(True)

st.pyplot(fig)

st.subheader("World Model Interpretation")

st.write(
    f"""
The model is asking:

**If I use {club}, aim {aim}°, with wind {wind}, what futures are likely?**

It then estimates whether those futures land on the green, fairway, rough, bunker, or water.

This is the key world-model idea:

**state + action → predicted future outcomes**
"""
)
