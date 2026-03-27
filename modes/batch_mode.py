import streamlit as st
import pandas as pd
import io
import datetime
from gitlab_utils import batch

DEFAULT_ICFAI_USERS = """saikrishna_b
MohanaSriBhavitha
praneethashish
kanukuntagreeshma2004
vandana1735
vandana_rajuldev
Mukthanand21
Shanmukh16
Sathwikareddy_Damanagari
Sahasraa
laxmanreddypatlolla
Abhilash653
LagichettyKushal
Lakshy
Suma2304
koushik_18
kumari123
Habeebunissa
Bhaskar_Battula
Pranav_rs
Pavani_Pothuganti
prav2702"""

DEFAULT_RCTS_USERS = """vai5h
Saiharshavardhan
Rushika_1105
swarna_4539
satish05
aravindswamy
pavaninagireddi
jeevana_31
saiteja3005
SandhyaRani_111
klaxmi1908
Kaveri_Mamidi
dasari_Askhaya
Ashritha_P"""

def render_batch_mode_ui(client, report_type):
    st.subheader(f"🚀 Batch Analytics - {report_type}")

    default_value = DEFAULT_ICFAI_USERS if report_type == "ICFAI" else DEFAULT_RCTS_USERS

    user_input = st.text_area(
        "Enter Usernames (one per line)",
        height=300,
        value=default_value,
        placeholder="user1\nuser2\n..."
    )

    if st.button("Run Batch Analysis"):
        usernames = [line.strip() for line in user_input.splitlines() if line.strip()]
        if not usernames:
            st.warning("Please enter at least one username.")
            return

        st.info(f"Processing {len(usernames)} users...")

        with st.spinner("Fetching data in parallel..."):
            results = batch.process_batch_users(client, usernames)

        st.success("Batch processing complete!")
        
        # Debug info
        st.info(f"📊 Processed {len(results)} users - {sum(1 for r in results if r.get('status')=='Success')} successful, {sum(1 for r in results if r.get('status')=='Error')} errors, {sum(1 for r in results if r.get('status')=='Not Found')} not found")

        # Prepare Data based on Report Type
        report_data = []

        for res in results:
            u = res.get("username")
            status = res.get("status")
            err = res.get("error", "")

            data = res.get("data", {})
            projects = data.get("projects", {})

            # Stats Access - with defaults
            c_stats = data.get("commit_stats", {})
            m_stats = data.get("mr_stats", {})
            i_stats = data.get("issue_stats", {})
            
            # Ensure all keys exist with defaults
            c_total = c_stats.get("total", 0)
            c_morning = c_stats.get("morning_commits", 0)
            c_afternoon = c_stats.get("afternoon_commits", 0)
            
            m_total = m_stats.get("total", 0)
            m_merged = m_stats.get("merged", 0)
            m_opened = m_stats.get("opened", 0)
            m_closed = m_stats.get("closed", 0)
            
            i_total = i_stats.get("total", 0)
            i_opened = i_stats.get("opened", 0)
            i_closed = i_stats.get("closed", 0)

            p_personal = len(projects.get("personal", []))
            p_contributed = len(projects.get("contributed", []))
            g_count = len(data.get("groups", []))

            row = {}
            row["Username"] = u
            row["Status"] = status

            # Add Generation Timestamp
            now_ist = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
            row["Report Date"] = now_ist.strftime("%Y-%m-%d")
            row["Report Time"] = now_ist.strftime("%I:%M %p")

            if status == "Success":
                if report_type == "ICFAI":
                    # ICFAI Columns
                    row["Personal Projects"] = p_personal
                    row["Contributed Projects"] = p_contributed
                    row["Total Commits"] = c_total
                    row["Morning Count"] = c_morning
                    row["Afternoon Count"] = c_afternoon
                    row["MR Open"] = m_opened
                    row["MR Closed"] = m_closed
                    row["MR Merged"] = m_merged
                    row["Issues Open"] = i_opened
                    row["Issues Closed"] = i_closed
                    row["Groups Count"] = g_count

                elif report_type == "RCTS":
                    # RCTS Columns
                    row["Total Projects"] = p_personal + p_contributed
                    row["Total Commits"] = c_total
                    row["MR Total"] = m_total
                    row["MR Merged"] = m_merged
                    row["MR Pending"] = m_opened
                    row["Issues Total"] = i_total
                    row["Groups"] = g_count
                    row["Morning Active"] = "Yes" if c_morning > 0 else "No"
                    row["Afternoon Active"] = "Yes" if c_afternoon > 0 else "No"
            else:
                 row["Error"] = err if err else "Unknown error"

            report_data.append(row)

        # Display Summary
        st.write(f"### 📊 Batch Summary ({report_type})")
        
        if not report_data:
            st.warning("No data was returned. Please check the usernames and try again.")
        else:
            df_report = pd.DataFrame(report_data)
            st.dataframe(df_report, width="stretch")

        # Export
        try:
            output = io.BytesIO()
            now_ist = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
            today = now_ist.strftime("%Y-%m-%d")
            filename = f"{report_type}_Report_{today}.xlsx"

            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Sheet 1: Report
                df_report.to_excel(writer, index=False, sheet_name='Report')

                # Sheet 2: Raw Errors (if any)
                errors = [r for r in report_data if r.get("Status") == "Error"]
                if errors:
                    pd.DataFrame(errors).to_excel(writer, index=False, sheet_name='Errors')

            st.download_button(
                label=f"Download {report_type} Report",
                data=output.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Error creating Excel: {e}")
