import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Function to add months to a date
def add_months(date, months):
    new_month = date.month + months
    new_year = date.year + new_month // 12
    new_month = new_month % 12
    if new_month == 0:
        new_month = 12
        new_year -= 1

    last_day_of_new_month = (datetime(new_year, new_month % 12 + 1, 1) - timedelta(days=1)).day
    day = min(date.day, last_day_of_new_month)

    return datetime(new_year, new_month, day)

# Function to format date as yyyy-mm-dd
def format_date(date):
    return date.strftime("%Y-%m-%d")

# Streamlit Interface
st.title("CRA Filing Deadline Calculator for First Nations")

# Input fields
filing_code = st.selectbox("Select Filing Code", ["PSB", "Code 1A", "Code 8"])
filer_status = st.selectbox("Filer Status", ["Filer", "Non-Filer"])
frequency = st.selectbox("Select Filing Frequency", ["Monthly", "Quarterly", "Annually"])

fiscal_start = st.date_input("Select Fiscal Year Start Date", value=datetime(2025, 4, 1), min_value=datetime(2015, 1, 1), max_value=datetime(2100, 12, 31))
start_year = st.selectbox("Select Starting Year", [i for i in range(2015, 2101)])
today_date = st.date_input("Select Today's Date", value=datetime.today())

# Button to calculate the deadlines
if st.button("Calculate Deadlines"):
    fiscal_start_date = datetime(fiscal_start.year, fiscal_start.month, fiscal_start.day)
    current_start = fiscal_start_date.replace(year=start_year)

    # Determine periods based on filer status
    if filer_status == "Non-Filer":
        # Only one period for non-filers: full fiscal year
        periods = [{
            "start": current_start,
            "end": current_start.replace(year=current_start.year + 1) - timedelta(days=1)
        }]
    else:
        # Filer: split by frequency
        period_count = {"Monthly": 12, "Quarterly": 4, "Annually": 1}[frequency]
        periods = []
        for _ in range(period_count):
            start = current_start
            if frequency == "Monthly":
                end = add_months(start, 1) - timedelta(days=1)
            elif frequency == "Quarterly":
                end = add_months(start, 3) - timedelta(days=1)
            else:  # Annually
                end = start.replace(year=start.year + 1) - timedelta(days=1)
            periods.append({"start": start, "end": end})
            current_start = end + timedelta(days=1)

    # Calculate deadlines
    result = []
    for period in periods:
        start = period["start"]
        end = period["end"]

        # Base deadline is 4 years from claim period end
        base_deadline = end.replace(year=end.year + 4)

        # Apply grace period for filers
        if filer_status == "Filer":
            grace_months = {"Monthly": 1, "Quarterly": 1, "Annually": 3}[frequency]
            final_deadline = add_months(base_deadline, grace_months)
        else:
            final_deadline = base_deadline

        # Convert today's date to datetime to ensure consistent type for comparison
        today_datetime = datetime(today_date.year, today_date.month, today_date.day)
        latest_allowed_date = max(today_datetime, final_deadline)

        result.append({
            "Period Start": format_date(start),
            "Period End": format_date(end),
            "Filing Deadline": format_date(final_deadline),
            "Latest Allowed Filing Date": format_date(latest_allowed_date)
        })

    # Display results
    st.write("### Filing Periods and Deadlines")
    st.write(f"**Filing Code:** {filing_code}")
    st.write(f"**Filer Status:** {filer_status}")
    st.write(f"**Filing Frequency:** {frequency}")
    st.write(f"**Today's Date:** {today_date.strftime('%Y-%m-%d')}")

    df = pd.DataFrame(result)
    st.write(df)

    # CSV download
    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False),
        file_name="filing_deadlines.csv",
        mime="text/csv"
    )
