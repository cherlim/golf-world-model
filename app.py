import streamlit as st
import matplotlib.pyplot as plt
from simulator import simulate_shot, CLUBS

st.title("Golf World Model Demo")

club = st.selectbox("Club", list(CLUBS.keys()))
wind = st.slider("Wind (-20 to 20)", -20, 20, 0)
aim = st.slider("Aim Angle", -20, 20, 0)

shots = [simulate_shot(club, aim, wind) for _ in range(100)]

fig, ax = plt.subplots(figsize=(8,4))
ax.scatter([s[0] for s in shots], [s[1] for s in shots])
ax.scatter([320],[0], marker="*", s=200)
ax.set_xlabel("Distance")
ax.set_ylabel("Lateral")
ax.set_title("Predicted Futures (Shot Dispersion)")

st.pyplot(fig)

st.write("World Model Idea: Current State + Action -> Many Possible Futures")
