import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Lineup Plays",
    layout="centered"
)

st.title("Lineup Plays")

DATA_FILE = "Play_Tracker_Cornell_Wapo.csv"
TEAM_SIZE_DEFAULT = 6

# ---------- Load Data ----------
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    st.error("plays.csv not found in repository.")
    st.stop()

if "Play" not in df.columns:
    st.error("CSV must contain a column named 'Play'.")
    st.stop()

players = [c for c in df.columns if c != "Play"]

skills = (
    df[players]
    .apply(pd.to_numeric, errors="coerce")
    .fillna(0)
    .astype(int)
)
skills = (skills > 0).astype(int)
plays = df["Play"].astype(str).tolist()

def players_who_know(play_name):
    mask = df["Play"].astype(str) == str(play_name)
    if not mask.any():
        return []
    row = skills.loc[mask].iloc[0]
    return [p for p in players if int(row[p]) == 1]

# ---------- Lineup Selection ----------
st.subheader("Select Lineup")

team_size = st.number_input(
    "Team size",
    min_value=1,
    max_value=min(20, len(players)),
    value=min(TEAM_SIZE_DEFAULT, len(players)),
    step=1,
)

selected_players = st.multiselect(
    f"Select exactly {int(team_size)} players",
    options=players,
)

if len(selected_players) != int(team_size):
    st.warning(f"Select exactly {int(team_size)} players.")
    st.stop()

selected_set = set(selected_players)

st.divider()

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["Available Plays", "Play & Sub Options"])

# ---------- Tab 1 ----------
with tab1:
    subset = skills[selected_players]
    known_counts = subset.sum(axis=1)
    common_mask = known_counts == int(team_size)
    common_plays = df.loc[common_mask, "Play"].astype(str).tolist()

    st.metric("Common Plays", len(common_plays))

    if common_plays:
        search = st.text_input("Search plays", "")
        filtered = [p for p in common_plays if search.lower() in p.lower()] if search else common_plays
        st.dataframe(
            pd.DataFrame({"Play": filtered}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No plays known by all selected players.")

# ---------- Tab 2 ----------
with tab2:
    chosen_play = st.selectbox("Choose a play", plays)

    know_play = players_who_know(chosen_play)
    know_set = set(know_play)

    in_lineup_and_know = sorted(selected_set.intersection(know_set))
    in_lineup_and_dont = sorted(selected_set.difference(know_set))
    subs = sorted(know_set.difference(selected_set))

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Who Know It", len(know_play))
    c2.metric("In Lineup & Know", len(in_lineup_and_know))
    c3.metric("Sub Options", len(subs))

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        st.markdown("**In lineup & know it**")
        st.write(in_lineup_and_know if in_lineup_and_know else "None")

        st.markdown("**In lineup & DON'T know it**")
        st.write(in_lineup_and_dont if in_lineup_and_dont else "None")

    with colB:
        st.markdown("**Available subs (know play, not in lineup)**")
        st.write(subs if subs else "None")

    if in_lineup_and_dont and subs:
        st.success("Swap someone who doesn’t know it with a sub option to keep this play available.")
    elif in_lineup_and_dont and not subs:
        st.warning("Some lineup players don't know this play and there are no subs available.")
    else:
        st.success("All lineup players know this play.")
