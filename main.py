import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Utility functions
def add_months(date, months):
    new_month = date.month + months
    new_year = date.year + (new_month - 1) // 12
    new_month = (new_month - 1) % 12 + 1
    day = min(date.day, (datetime(new_year, new_month % 12 + 1, 1) - timedelta(days=1)).day)
    return datetime(new_year, new_month, day)

def format_date(date):
    return date.strftime("%Y-%m-%d")

def get_deadline_filer(end_date, frequency, is_dec_31_individual=False):
    if frequency == "Monthly" or frequency == "Quarterly":
        return end_date + timedelta(days=30)
    if frequency == "Annually":
        if is_dec_31_individual:
            return datetime(end_date.year + 1, 6, 15)
        else:
            return end_date + timedelta(days=90)

def get_deadline_non_filer(claim_start, claim_end):
    if claim_start.month == 4:
        return datetime(claim_end.year + 4, 9, 30)
    elif claim_start.month == 10:
        return datetime(claim_end.year + 4, 3, 31)
    elif claim_start.month == 1:
        return datetime(claim_end.year + 4, 6, 30)
    elif claim_start.month == 7:
        return datetime(claim_end.year + 4, 12, 31)
    return claim_end + timedelta(days=1460)

# Streamlit App UI
st.title("CRA Filing Deadline Calculator")

filer_type = st.selectbox("Filer Type", ["Filer", "Non-Filer"])
filing_code = st.selectbox("Filing Code", ["PSB", "Code 1A", "Code 8"])
frequency = st.selectbox("Filing Frequency", ["Monthly", "Quarterly", "Annually"])
fiscal_year_end = st.date_input("Fiscal Year End", value=datetime(2025, 3, 31))
today_date = st.date_input("Today's Date", value=datetime.today())
is_dec_31_individual = st.checkbox("Are you an individual with Dec 31 fiscal year end & business income?", value=False)

if st.button("Calculate Deadlines"):
    periods = []

    if filer_type == "Filer":
        period_count = {"Monthly": 12, "Quarterly": 4, "Annually": 1}[frequency]
        current_start = fiscal_year_end.replace(year=fiscal_year_end.year - 1) + timedelta(days=1)

        for i in range(period_count):
            start = current_start
            if frequency == "Monthly":
                end = add_months(start, 1) - timedelta(days=1)
            elif frequency == "Quarterly":
                end = add_months(start, 3) - timedelta(days=1)
            else:
                end = fiscal_year_end

            deadline = get_deadline_filer(end, frequency, is_dec_31_individual)
            latest_allowed_date = max(deadline, today_date)

            periods.append({
                "Period Start": format_date(start),
                "Period End": format_date(end),
                "Filing Deadline": format_date(deadline),
                "Latest Allowed Filing Date": format_date(latest_allowed_date)
            })

            current_start = end + timedelta(days=1)

    elif filer_type == "Non-Filer":
        fy_end_month = fiscal_year_end.month
        fy_end_year = fiscal_year_end.year

        if fy_end_month == 3:  # March 31
            periods = [
                {
                    "Claim Period": "April 1 to September 30",
                    "Claim Start": datetime(fy_end_year, 4, 1),
                    "Claim End": datetime(fy_end_year, 9, 30)
                },
                {
                    "Claim Period": "October 1 to March 31",
                    "Claim Start": datetime(fy_end_year, 10, 1),
                    "Claim End": datetime(fy_end_year + 1, 3, 31)
                }
            ]
        elif fy_end_month == 12:  # December 31
            periods = [
                {
                    "Claim Period": "January 1 to June 30",
                    "Claim Start": datetime(fy_end_year + 1, 1, 1),
                    "Claim End": datetime(fy_end_year + 1, 6, 30)
                },
                {
                    "Claim Period": "July 1 to December 31",
                    "Claim Start": datetime(fy_end_year + 1, 7, 1),
                    "Claim End": datetime(fy_end_year + 1, 12, 31)
                }
            ]
        else:
            st.error("Currently, only March 31 or December 31 fiscal year-ends are supported for Non-Filers.")
            st.stop()

        for p in periods:
            deadline = get_deadline_non_filer(p["Claim Start"], p["Claim End"])
            p["Filing Deadline"] = format_date(deadline)
            p["Latest Allowed Filing Date"] = format_date(max(deadline, today_date))
            p["Claim Start"] = format_date(p["Claim Start"])
            p["Claim End"] = format_date(p["Claim End"])

    # Display results
    st.subheader("Results")
    st.write(f"**Filer Type:** {filer_type}")
    st.write(f"**Filing Code:** {filing_code}")
    st.write(f"**Filing Frequency:** {frequency}")
    st.write(f"**Fiscal Year End:** {fiscal_year_end.strftime('%Y-%m-%d')}")
    st.write(f"**Today's Date:** {today_date.strftime('%Y-%m-%d')}")

    df = pd.DataFrame(periods)
    st.write(df)

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False),
        file_name="cra_filing_deadlines.csv",
        mime="text/csv"
    )
