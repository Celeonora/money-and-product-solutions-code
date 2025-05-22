import streamlit as st
import pandas as pd
import datetime
import os

st.title("GitHub Repo Revamp — Team Feedback Survey")
st.write("Please rate how useful you think each of the following suggestions would be for our team's GitHub repo and workflow. 1 = Not useful at all, 5 = Amazingly useful.")

suggestions = [
    ("Organize the repository with clear, purpose-driven folders",
     "Using folders like data/ for raw data files, dev/ for scripts and development tools, dist/ for generated outputs or reports, and docs/ for internal guides and onboarding materials. This helps everyone quickly find what they need and keeps the repo tidy."),
    ("Write and maintain clear contribution guidelines",
     "Add a CONTRIBUTING.md file that explains how to open issues, submit pull requests, follow code style, and communicate changes. This makes it easier for new and existing team members to contribute effectively and reduces confusion."),
    ("Track changes and improvements with a changelog and regular releases",
     "Use a CHANGELOG.md to document what's new, improved, or fixed in each update to our scripts, dashboards, or processes. For major changes, create GitHub releases so everyone knows what's changed and when."),
    ("Create a docs/ folder for internal guides and onboarding",
     "Store all team-specific documentation, onboarding checklists, process explanations, and FAQs in a dedicated docs/ folder. This makes it easy for new team members to get up to speed and for everyone to find answers quickly."),
    ("Use a data/ folder to store raw input files",
     "Keep all raw data files (such as downloaded CSVs, unprocessed reports, or source datasets) in a dedicated data/ folder. This keeps data organized and separate from scripts or outputs, making it easier to track data sources and avoid confusion."),
    ("Use a dist/ folder for generated outputs and reports",
     "Save all generated files (like cleaned datasets, final reports, or exported charts) in a dist/ folder. This helps everyone know where to find the latest results and keeps outputs separate from raw data and code."),
    ("Add a CHANGELOG.md and use GitHub releases for major updates",
     "Whenever we make significant changes to our scripts, dashboards, or processes, document them in a CHANGELOG.md and create a GitHub release. This provides a clear history of what's changed and helps with troubleshooting or onboarding.")
]

responses = {}

with st.form("survey_form"):
    st.subheader("Rate each suggestion:")
    for idx, (title, desc) in enumerate(suggestions):
        st.markdown(f"**{idx+1}. {title}**\n_{desc}_")
        responses[f"rating_{idx}"] = st.radio(
            f"How useful is this?", [1, 2, 3, 4, 5], key=f"rating_{idx}", horizontal=True
        )
    comments = st.text_area("Optional: Any comments or suggestions?")
    name = st.text_input("Your name (optional)")
    submitted = st.form_submit_button("Submit")

if submitted:
    # Prepare data
    now = datetime.datetime.now().isoformat()
    data = {
        "timestamp": now,
        "name": name,
        **{f"suggestion_{i+1}_rating": responses[f"rating_{i}"] for i in range(len(suggestions))},
        "comments": comments
    }
    df = pd.DataFrame([data])
    file_exists = os.path.isfile("survey_responses.csv")
    if file_exists:
        df.to_csv("survey_responses.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("survey_responses.csv", mode="w", header=True, index=False)
    st.success("Thank you for your feedback! Your response has been recorded.") 