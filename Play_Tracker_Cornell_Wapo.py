import streamlit as st
import pandas as pd

st.title("Lineup → Common Plays")

st.write("Upload a CSV where rows are plays and columns are players. Cells should be 1/0 (or TRUE/FALSE).")
# Example format:
# Play,Alex,Bri,Cam
# Stack,1,1,0
# Flood,1,1,1

uploaded = st.file_uploader("Play_Tracker_Cornell_Wapo", type=["csv"])

min_common = st.slider("Minimum players who must know the play", 1, 6, 6)
team_size = st.number_input("Team size", min_value=1, max_value=20, value=6, step=1)

if uploaded is None:
    st.info("Upload a CSV to start.")
    st.stop()

df = pd.read_csv(uploaded)

if "Play" not in df.columns:
    st.error("CSV must have a column named 'Play'.")
    st.stop()

players = [c for c in df.columns if c != "Play"]
if len(players) == 0:
    st.error("CSV must have at least one player column.")
    st.stop()

# Coerce to numeric 0/1
skills = df[players].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
skills = (skills > 0).astype(int)  # treat any positive as 'knows'

selected = st.multiselect(
    "Select players",
    options=players,
    default=players[: min(int(team_size), len(players))],
)

if len(selected) != int(team_size):
    st.warning(f"Pick exactly {int(team_size)} players. Currently selected: {len(selected)}")
    st.stop()

subset = skills[selected]
known_counts = subset.sum(axis=1)

common_plays = df.loc[known_counts >= min_common, "Play"].tolist()

st.subheader("Plays you can run")
st.write(f"{len(common_plays)} plays meet the requirement (≥ {min_common} of {team_size} players).")

st.dataframe(pd.DataFrame({"Play": common_plays}), use_container_width=True)

# Optional: show “near misses”
st.subheader("Almost there")
near = df.loc[(known_counts == min_common - 1), ["Play"]].copy()
near["Players who know it"] = known_counts[known_counts == (min_common - 1)].values
st.dataframe(near, use_container_width=True)