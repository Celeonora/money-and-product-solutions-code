import os
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
ORG = "Shopify"
PROJECT_NUMBER = 10432
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("Please set the GITHUB_TOKEN environment variable.")

API_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

# GraphQL query to get project ID from project number
GET_PROJECT_ID_QUERY = '''
query($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      id
    }
  }
}
'''

# GraphQL query to get project items (paginated)
GET_PROJECT_ITEMS_QUERY = '''
query($projectId: ID!, $cursor: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          createdAt
          updatedAt
          content {
            ... on Issue {
              title
              number
              url
              assignees(first: 10) { nodes { login } }
              labels(first: 10) { nodes { name } }
              createdAt
              updatedAt
            }
            ... on PullRequest {
              title
              number
              url
              assignees(first: 10) { nodes { login } }
              labels(first: 10) { nodes { name } }
              createdAt
              updatedAt
            }
            ... on DraftIssue {
              title
              createdAt
              updatedAt
            }
          }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field {
                  ... on ProjectV2SingleSelectField {
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
'''

def run_query(query, variables):
    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.status_code} {response.text}")
    return response.json()

def get_project_id(org, number):
    data = run_query(GET_PROJECT_ID_QUERY, {"org": org, "number": number})
    return data["data"]["organization"]["projectV2"]["id"]

def get_all_project_items(project_id):
    items = []
    cursor = None
    while True:
        variables = {"projectId": project_id, "cursor": cursor}
        data = run_query(GET_PROJECT_ITEMS_QUERY, variables)
        nodes = data["data"]["node"]["items"]["nodes"]
        for node in nodes:
            content = node["content"] or {}
            title = content.get("title", "(No title)")
            number = content.get("number")
            url = content.get("url")
            assignees = ", ".join([a["login"] for a in content.get("assignees", {}).get("nodes", [])]) if "assignees" in content else ""
            labels = ", ".join([l["name"] for l in content.get("labels", {}).get("nodes", [])]) if "labels" in content else ""
            created_at = content.get("createdAt", node["createdAt"])
            updated_at = content.get("updatedAt", node["updatedAt"])
            # Get status from fieldValues
            status = None
            for fv in node["fieldValues"]["nodes"]:
                if fv and fv.get("field", {}).get("name", "").lower() == "status":
                    status = fv.get("name")
            items.append({
                "title": title,
                "number": number,
                "url": url,
                "assignees": assignees,
                "labels": labels,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at
            })
        page_info = data["data"]["node"]["items"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return items

def main():
    print("Fetching project ID...")
    project_id = get_project_id(ORG, PROJECT_NUMBER)
    print(f"Project ID: {project_id}")
    print("Fetching project items...")
    items = get_all_project_items(project_id)
    print(f"Fetched {len(items)} items.")
    df = pd.DataFrame(items)
    today = datetime.now().strftime("%Y-%m-%d")
    outname = f"shopify_project_{PROJECT_NUMBER}_items_{today}.csv"
    df.to_csv(outname, index=False)
    print(f"Saved data to {outname}")

if __name__ == "__main__":
    main() 