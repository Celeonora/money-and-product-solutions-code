import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import getpass
import os
from collections import Counter

# --- CONFIGURATION ---
REPO = "Shopify/Money-and-Product-Solutions"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Try to get from environment variable

if not GITHUB_TOKEN:
    print("Please enter your GitHub Personal Access Token (input is hidden):")
    GITHUB_TOKEN = getpass.getpass()

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
PER_PAGE = 100

def fetch_issues(repo, state="all"):
    print("Fetching issues from GitHub...")
    issues = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {"state": state, "per_page": PER_PAGE, "page": page}
        resp = requests.get(url, headers=HEADERS, params=params)
        data = resp.json()
        if not data or 'message' in data:
            break
        # Exclude pull requests
        issues.extend([i for i in data if "pull_request" not in i])
        if len(data) < PER_PAGE:
            break
        page += 1
    print(f"Fetched {len(issues)} issues.")
    return issues

def process_issues(issues):
    df = pd.DataFrame([{
        "number": i["number"],
        "title": i["title"],
        "state": i["state"],
        "labels": [l["name"] for l in i["labels"]],
        "assignee": i["assignee"]["login"] if i["assignee"] else None,
        "user": i["user"]["login"],
        "created_at": i["created_at"],
        "closed_at": i["closed_at"],
        "comments": i["comments"]
    } for i in issues])
    if df.empty:
        print("No issues found.")
        return df
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)
    df["closed_at"] = pd.to_datetime(df["closed_at"]).dt.tz_localize(None)
    return df

def save_report(df):
    today = datetime.now().strftime("%Y-%m-%d")
    report_name = f"issue_report_{today}.csv"
    df.to_csv(report_name, index=False)
    print(f"Saved raw issue data to {report_name}")

def plot_and_save(fig, name):
    fig.savefig(name, bbox_inches='tight')
    print(f"Saved plot: {name}")

def main():
    issues = fetch_issues(REPO)
    df = process_issues(issues)
    if df.empty:
        return

    save_report(df)

    # --- 1. Issue statistics ---
    print("\n--- Issue Statistics ---")
    print("Total issues:", len(df))
    print("Open issues:", (df["state"] == "open").sum())
    print("Closed issues:", (df["state"] == "closed").sum())
    print("Issues with no labels:", (df["labels"].apply(len) == 0).sum())
    print("Issues with no assignee:", df["assignee"].isna().sum())

    # --- 2. Trends ---
    print("\n--- Trends ---")
    all_labels = [label for labels in df["labels"] for label in labels]
    label_counts = pd.Series(all_labels).value_counts()
    print("Top 5 labels:\n", label_counts.head(5))
    print("Top 5 assignees:\n", df["assignee"].value_counts().head(5))
    print("Top 5 creators:\n", df["user"].value_counts().head(5))

    # --- 3. Activity over time ---
    print("\n--- Activity Over Time ---")
    df.set_index("created_at", inplace=True)
    created_per_month = df.resample("M").size()
    fig1, ax1 = plt.subplots()
    created_per_month.plot(ax=ax1, title="Issues Created per Month")
    plot_and_save(fig1, "issues_created_per_month.png")
    df.reset_index(inplace=True)

    if df["closed_at"].notna().any():
        df_closed = df.dropna(subset=["closed_at"]).copy()
        df_closed.set_index("closed_at", inplace=True)
        closed_per_month = df_closed.resample("M").size()
        fig2, ax2 = plt.subplots()
        closed_per_month.plot(ax=ax2, color="green", title="Issues Closed per Month")
        plot_and_save(fig2, "issues_closed_per_month.png")
        df_closed.reset_index(inplace=True)

    # --- 4. Contributor analysis ---
    print("\n--- Contributor Analysis ---")
    print("Most issues opened by:\n", df["user"].value_counts().head(5))
    print("Most issues closed by (assignee):\n", df["assignee"].value_counts().head(5))

    # --- 5. Issue resolution time ---
    print("\n--- Issue Resolution Time ---")
    df["resolution_time"] = (df["closed_at"] - df["created_at"]).dt.days
    closed_issues = df[df["state"] == "closed"]
    print("Average days to close:", closed_issues["resolution_time"].mean())
    print("Median days to close:", closed_issues["resolution_time"].median())
    print("Longest to close:\n", closed_issues.nlargest(3, "resolution_time")[["number", "title", "resolution_time"]])
    print("Quickest to close:\n", closed_issues.nsmallest(3, "resolution_time")[["number", "title", "resolution_time"]])

    # --- 6. Untriaged/unassigned issues ---
    print("\n--- Untriaged/Unassigned Issues ---")
    print("Issues with no labels:", df[df["labels"].apply(len) == 0][["number", "title"]])
    print("Issues with no assignee:", df[df["assignee"].isna()][["number", "title"]])

    # --- 7. Bug vs. feature requests ---
    print("\n--- Bug vs. Feature Requests ---")
    print("Bug issues:", df[df["labels"].apply(lambda x: "bug" in x)][["number", "title"]])
    print("Feature requests:", df[df["labels"].apply(lambda x: "feature" in x or "enhancement" in x)][["number", "title"]])

    # --- 8. Reopened issues ---
    # GitHub API v3 does not directly provide "reopened" status, so we skip this for now.

    # --- 9. Comment activity ---
    print("\n--- Most Discussed Issues ---")
    print(df.sort_values("comments", ascending=False)[["number", "title", "comments"]].head(5))

    # --- 10. Stale issues ---
    print("\n--- Stale Issues (open > 90 days) ---")
    now = pd.Timestamp.now().tz_localize(None)
    stale = df[(df["state"] == "open") & ((now - df["created_at"]).dt.days > 90)]
    print(stale[["number", "title", "created_at"]])

    # --- 11. PR/Issue linkage ---
    print("\n--- PR/Issue Linkage ---")
    print("This script does not fetch PR linkage directly, but you can check issues closed by PRs on GitHub.")

    # --- 12. Label coverage ---
    print("\n--- Label Coverage ---")
    print("Percentage of issues with labels:", 100 * (df["labels"].apply(len) > 0).mean())

    print("\nAnalysis complete! See CSV and PNG files in this folder.")

    # Load your CSV
    df = pd.read_csv('issue_report_2025-05-20.csv', parse_dates=['created_at', 'closed_at'])

    # Filter for 2025 issues
    df_2025 = df[df['created_at'].dt.year == 2025]

    # Key stats
    total_2025 = len(df_2025)
    open_2025 = (df_2025['state'] == 'open').sum()
    closed_2025 = (df_2025['state'] == 'closed').sum()
    nolabel_2025 = (df_2025['labels'].apply(lambda x: len(eval(x)) == 0)).sum()
    nolabel_pct = round(100 * nolabel_2025 / total_2025, 1) if total_2025 else 0

    # Top contributors
    top_creators = df_2025['user'].value_counts().head(3).to_dict()
    top_assignees = df_2025['assignee'].value_counts().head(3).to_dict()

    # Top labels
    all_labels = [l for sublist in df_2025['labels'].apply(eval) for l in sublist]
    top_labels = Counter(all_labels).most_common(3)

    print(f"2025 Issues: {total_2025} (Open: {open_2025}, Closed: {closed_2025})")
    print(f"With no labels: {nolabel_2025} ({nolabel_pct}%)")
    print("Top creators:", top_creators)
    print("Top assignees:", top_assignees)
    print("Top labels:", top_labels)

    # Trends chart: Issues created per month in 2025
    df_2025.set_index('created_at', inplace=True)
    created_per_month = df_2025.resample('M').size()
    fig, ax = plt.subplots()
    created_per_month.plot(ax=ax, title="2025 Issues Created per Month")
    plt.savefig('2025_issues_created_per_month.png')
    print("Saved: 2025_issues_created_per_month.png")
    plt.close()

    # If you want, also plot closed per month
    if df_2025['closed_at'].notna().any():
        df_closed = df_2025.dropna(subset=['closed_at']).copy()
        df_closed.set_index('closed_at', inplace=True)
        closed_per_month = df_closed.resample('M').size()
        fig2, ax2 = plt.subplots()
        closed_per_month.plot(ax=ax2, color="green", title="2025 Issues Closed per Month")
        plt.savefig('2025_issues_closed_per_month.png')
        print("Saved: 2025_issues_closed_per_month.png")
        plt.close()

if __name__ == "__main__":
    main()
