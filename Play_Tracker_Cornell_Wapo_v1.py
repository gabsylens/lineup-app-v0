import streamlit as st
import pandas as pd

st.set_page_config(page_title="Lineup Plays", layout="centered")
st.title("Lineup → Common Plays")

DATA_FILE = "Play_Tracker_Cornell_Wapo.csv"
TEAM_SIZE_DEFAULT = 6

# ---------- Load data ----------
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    st.error("plays.csv not found in the repository (must be in the same folder as app.py).")
    st.stop()

if "Play" not in df.columns:
    st.error("CSV must contain a column named 'Play'.")
    st.stop()

players = [c for c in df.columns if c != "Play"]
if len(players) < 1:
    st.error("CSV must include at least one player column.")
    st.stop()

# Coerce to 0/1
skills = (
    df[players]
    .apply(pd.to_numeric, errors="coerce")
    .fillna(0)
    .astype(int)
)
skills = (skills > 0).astype(int)
plays = df["Play"].astype(str)

# Helper: players who know a given play
def players_who_know(play_name: str) -> list[str]:
    mask = plays == play_name
    if not mask.any():
        return []
    row = skills.loc[mask].iloc[0]
    return [p for p in players if int(row[p]) == 1]

# ---------- Team selection ----------
st.subheader("1) Pick your lineup")
team_size = st.number_input(
    "Team size",
    min_value=1,
    max_value=min(20, len(players)),
    value=min(TEAM_SIZE_DEFAULT, len(players)),
    step=1,
)

selected_players = st.multiselect(
    f"Select exactly {team_size} players:",
    options=players,
)

if len(selected_players) != int(team_size):
    st.warning(f"Select exactly {int(team_size)} players. Currently selected: {len(selected_players)}")
    st.stop()

subset = skills[selected_players]
known_counts = subset.sum(axis=1)

common_plays = df.loc[known_counts == int(team_size), "Play"].astype(str).tolist()

st.subheader("Plays everyone in the lineup knows")
if common_plays:
    st.write(f"{len(common_plays)} plays")
    st.dataframe(pd.DataFrame({"Play": common_plays}), use_container_width=True)
else:
    st.write("No plays are known by all selected players.")

st.divider()

# ---------- Play → who knows it + substitution help ----------
st.subheader("2) Pick a play → see who can run it (and sub options)")

# Default dropdown: if there are common plays, default to first one; else first play in file
default_play = (common_plays[0] if len(common_plays) > 0 else plays.iloc[0])
chosen_play = st.selectbox("Choose a play:", options=plays.tolist(), index=plays.tolist().index(default_play))

know_play = players_who_know(chosen_play)
know_play_set = set(know_play)
selected_set = set(selected_players)

in_lineup_and_know = sorted(selected_set.intersection(know_play_set))
in_lineup_and_dont = sorted(selected_set.difference(know_play_set))
not_in_lineup_but_know = sorted(know_play_set.difference(selected_set))

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Players who know this play**")
    if know_play:
        st.write(know_play)
    else:
        st.write("No one is marked as knowing this play.")

with c2:
    st.markdown("**Sub options (know play, not in lineup)**")
    if not_in_lineup_but_know:
        st.write(not_in_lineup_but_know)
    else:
        st.write("No additional players know this play (outside the current lineup).")

st.markdown("**Lineup coverage for this play**")
cc1, cc2 = st.columns(2)

with cc1:
    st.markdown("✅ In lineup & know it")
    st.write(in_lineup_and_know if in_lineup_and_know else "None")

with cc2:
    st.markdown("❌ In lineup & DON'T know it")
    st.write(in_lineup_and_dont if in_lineup_and_dont else "None")

# Optional: quick suggestion text
if in_lineup_and_dont and not_in_lineup_but_know:
    st.info(
        "Sub suggestion: swap someone from 'In lineup & DON'T know it' with someone from "
        "'Sub options' to keep this play available."
    )
elif in_lineup_and_dont and not not_in_lineup_but_know:
    st.warning("Some lineup players don't know this play, and nobody outside the lineup is marked as knowing it.")
elif not in_lineup_and_dont:
    st.success("All selected lineup players know this play.")
