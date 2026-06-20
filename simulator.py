import math, random

CLUBS = {
    "Driver": 220,
    "5 Iron": 170,
    "7 Iron": 150,
    "9 Iron": 120,
    "PW": 100
}

def simulate_shot(club, aim_deg=0, wind=0):
    distance = CLUBS[club] + random.gauss(0, 10)
    angle = math.radians(aim_deg + random.gauss(0, 3))
    x = distance * math.cos(angle)
    y = distance * math.sin(angle) + wind * 0.5
    return x, y
