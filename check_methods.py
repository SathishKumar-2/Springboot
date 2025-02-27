import sys
import os
import requests
import re
from github import Github

# Get GitHub Token & Repository Name from Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")  # Automatically gets 'owner/repo'

if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN is not set!")
    sys.exit(1)

if not REPO_NAME:
    print("❌ Error: REPO_NAME is not set!")
    sys.exit(1)

# Get PR number dynamically from command-line argument
if len(sys.argv) < 2:
    print("❌ Error: PR number not provided!")
    sys.exit(1)

PR_NUMBER = sys.argv[1]

# Fetch PR changes from GitHub
def get_pr_changes(repo_name, pr_number):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("❌ Error fetching PR data:", response.json())
        sys.exit(1)

    files = response.json()
    changed_methods = []

    for file in files:
        if file['filename'].endswith(".java"):  # Only Java files
            patch = file.get('patch', '')
            methods = extract_methods_from_patch(patch)
            changed_methods.extend(methods)

    return changed_methods

# Extract method names from Git diff
def extract_methods_from_patch(patch):
    method_pattern = re.compile(r"\+\s*(public|private|protected|static|\s)*\s*[\w<>]+\s+(\w+)\s*\(")
    return [match.group(2) for match in method_pattern.finditer(patch)]

# Process PR
changed_methods = get_pr_changes(REPO_NAME, PR_NUMBER)

if changed_methods:
    print("### 🔍 Changed Methods in PR:")
    for method in changed_methods:
        print(f"🔹 `{method}`")
else:
    print("✅ No changed methods found.")