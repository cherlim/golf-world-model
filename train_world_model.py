import json
import pickle
import random
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error


CLUBS = {
    "Driver": {"carry": 220, "spread_x": 18, "spread_y": 12},
    "3 Wood": {"carry": 200, "spread_x": 15, "spread_y": 10},
    "Hybrid": {"carry": 175, "spread_x": 12, "spread_y": 8},
    "5 Iron": {"carry": 155, "spread_x": 10, "spread_y": 7},
    "7 Iron": {"carry": 135, "spread_x": 8, "spread_y": 6},
    "9 Iron": {"carry": 115, "spread_x": 7, "spread_y": 5},
    "PW": {"carry": 90, "spread_x": 6, "spread_y": 4},
    "SW": {"carry": 60, "spread_x": 5, "spread_y": 4},
    "Putter": {"carry": 20, "spread_x": 2, "spread_y": 2},
}

CLUB_TO_ID = {club: i for i, club in enumerate(CLUBS.keys())}


def simulate_mean_shot(ball_x, ball_y, pin_x, pin_y, club, aim, wind):
    club_data = CLUBS[club]

    carry = club_data["carry"] + wind

    angle_rad = np.deg2rad(aim)

    landing_x = ball_x + carry * np.cos(angle_rad)
    landing_y = ball_y + carry * np.sin(angle_rad)

    return landing_x, landing_y, club_data["spread_x"], club_data["spread_y"]


def generate_dataset(n_samples=30000):
    X = []
    y = []

    for _ in range(n_samples):
        ball_x = 0
        ball_y = 0

        pin_x = 250
        pin_y = 0

        club = random.choice(list(CLUBS.keys()))
        aim = random.uniform(-20, 20)
        wind = random.uniform(-20, 20)

        landing_x, landing_y, spread_x, spread_y = simulate_mean_shot(
            ball_x, ball_y, pin_x, pin_y, club, aim, wind
        )

        X.append([
            ball_x,
            ball_y,
            pin_x,
            pin_y,
            CLUB_TO_ID[club],
            aim,
            wind,
        ])

        y.append([
            landing_x,
            landing_y,
            spread_x,
            spread_y,
        ])

    return np.array(X), np.array(y)


def main():
    print("Generating simulator data...")
    X, y = generate_dataset(n_samples=30000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("Training learned world model...")
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print("Training complete.")
    print(f"MAE: {mae:.3f}")
    print(f"RMSE: {rmse:.3f}")

    with open("world_model.pkl", "wb") as f:
        pickle.dump(model, f)

    with open("club_mapping.json", "w") as f:
        json.dump(CLUB_TO_ID, f, indent=2)

    print("Saved world_model.pkl")
    print("Saved club_mapping.json")


if __name__ == "__main__":
    main()