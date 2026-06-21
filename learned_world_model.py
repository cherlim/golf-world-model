import json
import pickle
import numpy as np


def load_learned_world_model():
    with open("world_model.pkl", "rb") as f:
        model = pickle.load(f)

    with open("club_mapping.json", "r") as f:
        club_mapping = json.load(f)

    return model, club_mapping


def predict_learned_shot(ball_x, ball_y, pin_x, pin_y, club, aim, wind):
    model, club_mapping = load_learned_world_model()

    if club not in club_mapping:
        raise ValueError(f"Unknown club: {club}")

    X = np.array([[
        ball_x,
        ball_y,
        pin_x,
        pin_y,
        club_mapping[club],
        aim,
        wind,
    ]])

    prediction = model.predict(X)[0]

    return {
        "landing_x": float(prediction[0]),
        "landing_y": float(prediction[1]),
        "spread_x": float(prediction[2]),
        "spread_y": float(prediction[3]),
    }