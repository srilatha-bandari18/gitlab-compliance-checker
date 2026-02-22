import streamlit as st
import pandas as pd
from gitlab_utils.productivity_utils import get_user_productivity, get_team_productivity

# Default team mapping
# Team mapping
TEAMS = {

    # From Screenshot Teams

    "Dev 3": [
        "saikrishna_b",
        "MohanaSriBhavitha",
        "Saiharshavardhan"
    ],

    "Trinity": [
        "praneethashish",
        "vai5h",
        "kanukuntagreeshma2004"
    ],

    "Sudo": [
        "vandana1735",
        "vandana_rajuldev",
        "lakshmipavani_20"
    ],

    "Trishul": [
        "Mukthanand21",
        "Shanmukh16",
        "Rushika_1105"
    ],

    "BrainStorm": [
        "satish05",
        "Sathwikareddy_Damanagari",
        "Sahasraa"
    ],

    "Core": [
        "Abhilash653",
        "swarna_4539",
        "laxmanreddypatlolla"
    ],

    "Magnum": [
        "LagichettyKushal",
        "Lakshy",
        "pavaninagireddi"
    ],

    "TrioForce": [
        "aravindswamy",
        "Suma2304",
        "koushik_18",
        "kumari123"
    ],

    "Techops": [
        "Habeebunissa",
        "jeevana_31",
        "Bhaskar_Battula"
    ],

    "Mind ops": [
        "saiteja3005",
        "Pranav_rs",
        "prav2702"
    ],

    "Synergy Six": [
        "klaxmi1908",
        "kaveri_mamidi",
        "dasari_Akshaya",
        "Ashritha_P",
        "prashanth0812",
        "dasarajuvaishnavi04",
        "ashrithakunjeti",
        "srilatha",
        "vemusripriya"
    ],

    # Custom Teams

    "Code Dev": [
        "prav2702",
        "klaxmi1908",
        "dasari_Akshaya"
    ],

    "SPK": [
        "SandhyaRani_111",
        "kaveri_mamidi",
        "Pavani_Pothuganti"
    ]
}

def render_productivity_dashboard(client):
    st.subheader("🏆 Team-wise Productivity Leaderboard")

    # 1. Selection Controls
    col1, col2 = st.columns(2)
    with col1:
        selected_team = st.selectbox("Select Team", options=list(TEAMS.keys()))

    members = TEAMS.get(selected_team, [])
    with col2:
        selected_member = st.selectbox("Select Member", options=["All Members"] + members)

    st.markdown("---")

    # 2. Team Overview Section
    st.markdown("### 👥 Team Overview")

    if selected_team:
        with st.spinner(f"Fetching productivity data for {selected_team}..."):
            team_stats = get_team_productivity(client, selected_team, members)

        if team_stats and team_stats.get("member_stats"):
            # Display Team Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Commits", team_stats["total_commits"])
            c2.metric("Total MRs Merged", team_stats["total_mrs_merged"])
            c3.metric("Total Issues Closed", team_stats["total_issues_closed"])

            # Leaderboard Table
            st.markdown("#### 🥇 Leaderboard")
            df_leaderboard = pd.DataFrame(team_stats["member_stats"])
            if not df_leaderboard.empty:
                # Rename columns for display
                df_display = df_leaderboard.copy()
                df_display = df_display.rename(columns={
                    "username": "Username",
                    "commits_count": "Commits",
                    "mrs_opened": "MRs Opened",
                    "mrs_closed": "MRs Closed",
                    "mrs_merged": "MRs Merged",
                    "issues_opened": "Issues Opened",
                    "issues_closed": "Issues Closed"
                })
                # Sort by commits
                df_display = df_display.sort_values(by="Commits", ascending=False).reset_index(drop=True)
                df_display.index += 1 # 1-based index for ranking
                st.dataframe(df_display, width="stretch")

                # Bar Chart for Commits
                st.markdown("#### 📊 Commits Comparison")
                st.bar_chart(df_display.set_index("Username")["Commits"])
            else:
                st.warning("No activity found for this team.")
        else:
            st.error("Unable to fetch data. Please try again.")

    st.markdown("---")

    # 3. Individual Member Performance Section
    if selected_member != "All Members":
        st.markdown(f"### 👤 Individual Performance: {selected_member}")

        with st.spinner(f"Fetching productivity data for {selected_member}..."):
            member_stats = get_user_productivity(client, selected_member)

        if member_stats:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Commits", member_stats["commits_count"])
            c2.metric("MRs Opened", member_stats["mrs_opened"])
            c3.metric("MRs Merged", member_stats["mrs_merged"])
            c4.metric("Issues Opened", member_stats["issues_opened"])
            c5.metric("Issues Closed", member_stats["issues_closed"])
        else:
            st.warning(f"No activity found for {selected_member}.")
    else:
        st.info("Select a member from the dropdown to see individual performance.")
