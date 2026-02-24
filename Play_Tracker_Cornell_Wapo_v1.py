import streamlit as st
import pandas as pd

# ---------- Page config + light CSS polish ----------
st.set_page_config(
    page_title="Lineup Plays",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
      /* tighten mobile spacing a bit */
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      /* nicer section headers */
      h1, h2, h3 { letter-spacing: -0.02em; }
      /* hide streamlit footer + hamburger/help */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      /* make dataframes less huge */
      .stDataFrame { border-radius: 12px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Lineup Plays")

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
plays = df["Play"].astype(str).tolist()

def players_who_know(play_name: str) -> list[str]:
    mask = df["Play"].astype(str) == str(play_name)
    if not mask.any():
        return []
    row = skills.loc[mask].iloc[0]
    return [p for p in players if int(row[p]) == 1]

# ---------- Sidebar controls ----------
with st.sidebar:
    st.header("Setup")
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
        default=players[: min(int(team_size), len(players))],
    )

    st.divider()
    st.caption("Tip: save this page to your home screen for one-tap access.")

# Must have exactly team_size
if len(selected_players) != int(team_size):
    st.warning(f"Select exactly {int(team_size)} players (currently {len(selected_players)}).")
    st.stop()

selected_set = set(selected_players)

# ---------- Tabs ----------
tab1, tab2 = st.tabs(["Lineup plays", "Play lookup / subs"])

# ---------- Tab 1: plays everyone knows ----------
with tab1:
    st.subheader("Plays available with this lineup")

    subset = skills[selected_players]
    known_counts = subset.sum(axis=1)
    common_mask = known_counts == int(team_size)
    common_plays = df.loc[common_mask, "Play"].astype(str).tolist()

    c1, c2, c3 = st.columns(3)
    c1.metric("Players selected", f"{len(selected_players)}")
    c2.metric("Common plays", f"{len(common_plays)}")
    c3.metric("Total plays", f"{len(df)}")

    st.divider()

    if common_plays:
        # Search/filter
        q = st.text_input("Search common plays", "")
        filtered = [p for p in common_plays if q.lower() in p.lower()] if q else common_plays

        st.dataframe(pd.DataFrame({"Play": filtered}), use_container_width=True, hide_index=True)
    else:
        st.info("No plays are known by all selected players.")

# ---------- Tab 2: pick a play and see subs ----------
with tab2:
    st.subheader("Pick a play → see who knows it")

    # Default: first common play if available
    subset = skills[selected_players]
    known_counts = subset.sum(axis=1)
    common_plays = df.loc[known_counts == int(team_size), "Play"].astype(str).tolist()
    default_play = common_plays[0] if common_plays else plays[0]

    chosen_play = st.selectbox("Play", options=plays, index=plays.index(default_play))

    know_play = players_who_know(chosen_play)
    know_set = set(know_play)

    in_lineup_and_know = sorted(selected_set.intersection(know_set))
    in_lineup_and_dont = sorted(selected_set.difference(know_set))
    not_in_lineup_but_know = sorted(know_set.difference(selected_set))

    m1, m2, m3 = st.columns(3)
    m1.metric("Know it (total)", f"{len(know_play)}")
    m2.metric("In lineup & know", f"{len(in_lineup_and_know)}")
    m3.metric("Subs available", f"{len(not_in_lineup_but_know)}")

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        st.markdown("**✅ In lineup & know it**")
        st.write(in_lineup_and_know if in_lineup_and_know else "None")

        st.markdown("**❌ In lineup & don’t know it**")
        st.write(in_lineup_and_dont if in_lineup_and_dont else "None")

    with colB:
        st.markdown("**🟦 Not in lineup but know it (sub options)**")
        st.write(not_in_lineup_but_know if not_in_lineup_but_know else "None")

        if in_lineup_and_dont and not_in_lineup_but_know:
            st.success("Swap someone who doesn’t know it with a sub option to keep this play available.")
        elif in_lineup_and_dont and not not_in_lineup_but_know:
            st.warning("Some lineup players don’t know it, and there are no subs marked as knowing it.")
        else:
            st.success("All selected lineup players know this play.")
