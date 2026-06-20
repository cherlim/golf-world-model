import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

from simulator import CLUBS, simulate_shot


st.title("Golf World Model Demo — Version 0.6")

st.write(
    "This version adds golf-specific constraints, so the world model cannot choose unrealistic plans such as PW followed by Driver."
)

with open(Path("course.json"), "r") as f:
    course = json.load(f)

wind = st.slider("Wind (-20 to 20)", -20, 20, 0)
aim = st.slider("Aim Angle for First Shot", -20, 20, 0)
num_shots = st.slider("Number of simulated futures per club", 50, 300, 150)


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


def simulate_from_position(start_x, start_y, club, aim_deg, wind):
    dx, dy = simulate_shot(club, aim_deg, wind)
    return start_x + dx, start_y + dy


def evaluate_one_shot_from_position(start_x, start_y, club):
    pin = course["green"]["center"]

    shots = [
        simulate_from_position(start_x, start_y, club, 0, wind)
        for _ in range(num_shots)
    ]

    outcomes = [classify_shot(x, y) for x, y in shots]
    distances_to_pin = [distance([x, y], pin) for x, y in shots]
    avg_distance_to_pin = sum(distances_to_pin) / len(distances_to_pin)

    green = outcomes.count("Green") / num_shots
    bunker = outcomes.count("Bunker") / num_shots
    water = outcomes.count("Water") / num_shots
    hazard = bunker + water

    score = (
        150
        - avg_distance_to_pin
        + green * 100
        - bunker * 60
        - water * 120
    )

    return {
        "club": club,
        "shots": shots,
        "green": green,
        "bunker": bunker,
        "water": water,
        "hazard": hazard,
        "avg_distance_to_pin": avg_distance_to_pin,
        "score": score,
    }


def allowed_second_clubs(start_x, start_y):
    distance_to_pin = distance([start_x, start_y], course["green"]["center"])

    allowed = []

    for club in CLUBS.keys():
        # Driver is only allowed from the tee / very long starting position
        if club == "Driver":
            continue

        # PW is mainly for shorter approach shots
        if club == "PW" and distance_to_pin > 130:
            continue

        # 9 Iron is not suitable for very long remaining distance
        if club == "9 Iron" and distance_to_pin > 170:
            continue

        allowed.append(club)

    return allowed


def find_best_second_shot(start_x, start_y):
    clubs = allowed_second_clubs(start_x, start_y)

    second_results = [
        evaluate_one_shot_from_position(start_x, start_y, club)
        for club in clubs
    ]

    return max(second_results, key=lambda r: r["score"])


def evaluate_two_shot_plan(first_club):
    first_shots = [
        simulate_from_position(0, 0, first_club, aim, wind)
        for _ in range(num_shots)
    ]

    first_outcomes = [classify_shot(x, y) for x, y in first_shots]
    first_water = first_outcomes.count("Water") / num_shots
    first_bunker = first_outcomes.count("Bunker") / num_shots
    first_hazard = first_water + first_bunker

    second_club_choices = []
    final_distances = []
    final_green_probs = []
    final_hazard_probs = []

    for x, y in first_shots:
        # If first shot is in water, apply a strong penalty by keeping distance high.
        if classify_shot(x, y) == "Water":
            second_club_choices.append("Penalty")
            final_distances.append(999)
            final_green_probs.append(0)
            final_hazard_probs.append(1)
            continue

        best_second = find_best_second_shot(x, y)
        second_club_choices.append(best_second["club"])
        final_distances.append(best_second["avg_distance_to_pin"])
        final_green_probs.append(best_second["green"])
        final_hazard_probs.append(best_second["hazard"])

    avg_final_distance = sum(final_distances) / len(final_distances)
    avg_final_green = sum(final_green_probs) / len(final_green_probs)
    avg_final_hazard = sum(final_hazard_probs) / len(final_hazard_probs)

    most_common_second = max(
        set(second_club_choices),
        key=second_club_choices.count,
    )

    score = (
        200
        - avg_final_distance
        + avg_final_green * 120
        - first_hazard * 100
        - avg_final_hazard * 80
    )

    return {
        "first_club": first_club,
        "best_second_club": most_common_second,
        "first_hazard": first_hazard,
        "avg_final_distance": avg_final_distance,
        "avg_final_green": avg_final_green,
        "avg_final_hazard": avg_final_hazard,
        "score": score,
        "first_shots": first_shots,
    }


plans = [evaluate_two_shot_plan(club) for club in CLUBS.keys()]
best_plan = max(plans, key=lambda p: p["score"])

st.subheader("AI Two-Shot Recommendation")

st.success(
    f"Recommended plan: {best_plan['first_club']} → {best_plan['best_second_club']}"
)

st.write(
    f"""
The world model simulated **{num_shots} first-shot futures** for each club.

For each future position, it then searched for the best second shot.

This means the model is no longer asking only:

**What happens after one shot?**

It is asking:

**What happens after this shot, and what can I do next?**
"""
)

st.subheader("Two-Shot Plan Comparison")

table_data = []
for p in plans:
    table_data.append(
        {
            "First Club": p["first_club"],
            "Best Second Club": p["best_second_club"],
            "First Shot Hazard": f"{p['first_hazard']:.1%}",
            "Final Green Prob": f"{p['avg_final_green']:.1%}",
            "Final Hazard Prob": f"{p['avg_final_hazard']:.1%}",
            "Avg Final Dist to Pin": round(p["avg_final_distance"], 1),
            "Score": round(p["score"], 1),
        }
    )

st.table(table_data)

selected_first_club = st.selectbox(
    "Choose first club to visualize",
    list(CLUBS.keys()),
    index=list(CLUBS.keys()).index(best_plan["first_club"]),
)

selected_plan = next(p for p in plans if p["first_club"] == selected_first_club)
shots = selected_plan["first_shots"]

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
ax.set_title(f"First-Shot Futures for {selected_first_club}")
ax.grid(True)

st.pyplot(fig)

st.subheader("World Model Interpretation")

st.write(
    """
Version 0.5 demonstrates multi-step planning.

The model now follows this pattern:

**current state → first action → predicted future state → second action → final predicted outcome**

This is closer to LeCun's world-model idea because the system is not merely reacting to the current situation. It is imagining future states and planning through them.
"""
)