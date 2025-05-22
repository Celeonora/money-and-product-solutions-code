import streamlit as st
import pandas as pd
import glob
import os
from collections import Counter
from datetime import datetime, timedelta

st.title("Money and Product Solutions Github Activity Dashboard")

# Find the latest CSV file
csv_files = sorted(glob.glob("shopify_project_10432_items_*.csv"), reverse=True)

if csv_files:
    default_csv = csv_files[0]
    st.info(f"Loaded data from: {default_csv}")
    df = pd.read_csv(default_csv, parse_dates=["created_at", "updated_at"])
else:
    df = None
    st.warning("No project CSV file found. Please upload one below.")

# uploaded = st.file_uploader("Or upload a project CSV file", type=["csv"])
if df is not None:
    st.header("Team Overview")
    # --- Date range filter ---
    min_date = df["created_at"].min().date()
    max_date = df["created_at"].max().date()
    start_date, end_date = st.date_input(
        "Filter by creation date:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    mask = (df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)
    filtered_df = df[mask].copy()
    # Ensure both created_at and updated_at are timezone-naive
    filtered_df["created_at"] = pd.to_datetime(filtered_df["created_at"]).dt.tz_localize(None)
    filtered_df["updated_at"] = pd.to_datetime(filtered_df["updated_at"]).dt.tz_localize(None)

    st.markdown(f"**Showing {len(filtered_df)} items created between {start_date} and {end_date}.**")

    # --- 1. Project/Issue Completion Rate ---
    st.subheader("Completion Rate")
    done_statuses = ["Done", "Closed"]
    total_items = len(filtered_df)
    completed_items = filtered_df[filtered_df["status"].isin(done_statuses)]
    # Ensure both created_at and updated_at are timezone-naive for completed_items as well
    completed_items.loc[:, "created_at"] = pd.to_datetime(completed_items["created_at"]).dt.tz_localize(None)
    completed_items.loc[:, "updated_at"] = pd.to_datetime(completed_items["updated_at"]).dt.tz_localize(None)
    completion_rate = len(completed_items) / total_items * 100 if total_items > 0 else 0
    st.metric("Completion Rate (%)", f"{completion_rate:.1f}")

    # --- 2. Average Time to Completion ---
    st.subheader("Average Time to Completion (Done/Closed)")
    if not completed_items.empty:
        completed_items = completed_items.copy()
        completed_items["completion_days"] = (completed_items["updated_at"] - completed_items["created_at"]).dt.days
        avg_completion = completed_items["completion_days"].mean()
        st.metric("Average Days to Completion", f"{avg_completion:.1f}")
    else:
        st.info("No completed items in the selected date range.")

    # --- 3. Items Created vs. Closed Over Time ---
    st.header("Trends")
    st.subheader("Items Created vs. Closed Over Time (per Month)")
    filtered_df["created_month"] = filtered_df["created_at"].dt.to_period("M").astype(str)
    created_per_month = filtered_df["created_month"].value_counts().sort_index()
    closed_df = filtered_df[filtered_df["status"].isin(done_statuses)].copy()
    closed_df["closed_month"] = closed_df["updated_at"].dt.to_period("M").astype(str)
    closed_per_month = closed_df["closed_month"].value_counts().sort_index()
    trend_df = pd.DataFrame({
        "Created": created_per_month,
        "Closed": closed_per_month
    }).fillna(0)
    st.line_chart(trend_df)
    st.dataframe(trend_df.reset_index().rename(columns={"index": "Month"}))

    # --- 4. Open vs. Closed by Assignee ---
    st.header("Workload Distribution")
    st.subheader("Open vs. Closed Items by Assignee")
    open_df = filtered_df[~filtered_df["status"].isin(done_statuses)]
    assignee_status = []
    for _, row in filtered_df.iterrows():
        assignees = [a.strip() for a in str(row["assignees"]).split(",") if a.strip()]
        for a in assignees:
            assignee_status.append({
                "Assignee": a,
                "Status": "Closed" if row["status"] in done_statuses else "Open"
            })
    if assignee_status:
        assignee_status_df = pd.DataFrame(assignee_status)
        pivot = pd.pivot_table(assignee_status_df, index="Assignee", columns="Status", aggfunc=len, fill_value=0)
        st.dataframe(pivot)
        st.bar_chart(pivot)
    else:
        st.info("No assignee data available.")

    # --- 5. Most Common Labels ---
    st.subheader("Most Common Labels")
    all_labels = []
    for labels in filtered_df["labels"].fillna(""):
        all_labels.extend([l.strip() for l in str(labels).split(",") if l.strip()])
    if all_labels:
        label_counts = pd.Series(Counter(all_labels)).sort_values(ascending=False)
        st.bar_chart(label_counts.head(10))
        st.dataframe(label_counts.rename_axis('Label').reset_index(name='Count'))
    else:
        st.info("No label data available.")

    # --- 6. Flagged Items (missing label/assignee) ---
    st.header("Actionable Lists")
    st.subheader("Flagged Items: Missing Label or Assignee")
    flagged = filtered_df[(filtered_df['labels'].isna() | (filtered_df['labels'].str.strip() == "")) |
                          (filtered_df['assignees'].isna() | (filtered_df['assignees'].str.strip() == ""))]
    if not flagged.empty:
        flagged_table = flagged[['title', 'status', 'url']]
        st.dataframe(flagged_table)
    else:
        st.info("No flagged items found.")

    # --- 7. Stale Items (not updated in 30+ days, still open) ---
    st.subheader("Stale Items (Open, Not Updated in 30+ Days)")
    now = pd.Timestamp.now().replace(tzinfo=None)
    stale = filtered_df[(~filtered_df["status"].isin(done_statuses)) & ((now - filtered_df["updated_at"]).dt.days > 30)]
    if not stale.empty:
        st.dataframe(stale[['title', 'status', 'url', 'updated_at']])
    else:
        st.info("No stale items found.")

    # --- 8. Recently Closed Items (last 30 days) ---
    st.subheader("Recently Closed Items (Last 30 Days)")
    recently_closed = completed_items[(now - completed_items["updated_at"]).dt.days <= 30]
    if not recently_closed.empty:
        st.dataframe(recently_closed[['title', 'status', 'url', 'updated_at']])
    else:
        st.info("No recently closed items found.")

    # --- 9. Items With Multiple Assignees ---
    st.subheader("Items With Multiple Assignees")
    multi_assignees = filtered_df[filtered_df["assignees"].apply(lambda x: len([a for a in str(x).split(",") if a.strip()]) > 1)]
    if not multi_assignees.empty:
        st.dataframe(multi_assignees[['title', 'status', 'url', 'assignees']])
    else:
        st.info("No items with multiple assignees found.")

    st.success("Dashboard loaded!")
else:
    st.info("Please upload a project CSV file to view the dashboard.")
