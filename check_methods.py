import sys
import os
import requests
import re
from github import Github

# Get GitHub Token & Repository Name from Environment Variable
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
print("PR number provided!"+PR_NUMBER)

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
            methods = extract_fully_qualified_methods(patch, file['filename'])
            changed_methods.extend(methods)

    return changed_methods

# Extract method names from Git diff
def extract_fully_qualified_methods(patch, file_path):
    package_pattern = re.compile(r"^\s*package\s+([\w\.]+);")  # Extracts package name
    class_pattern = re.compile(r"\bclass\s+(\w+)")  # Extracts class name
    method_pattern = re.compile(r"\b(public|private|protected|static|\s)*\s*[\w<>]+\s+(\w+)\s*\(")

    package_name = None
    class_name = None
    inside_method = None
    method_changes = {}  # {method_name: has_changes}

    # Track package & class name
    for line in patch.split("\n"):
        if package_name is None:
            package_match = package_pattern.search(line)
            if package_match:
                package_name = package_match.group(1)

        if class_name is None:
            class_match = class_pattern.search(line)
            if class_match:
                class_name = class_match.group(1)

    # Track method changes
    for line in patch.split("\n"):
        if line.startswith("+") or line.startswith("-"):  # Detect changed lines
            match = method_pattern.search(line)
            if match:
                inside_method = match.group(2)  # Extract method name
                method_changes[inside_method] = False  # Initialize as unchanged
            elif inside_method:
                method_changes[inside_method] = True  # Mark method as changed

        if inside_method and line.strip() == "}":  # Exit method
            inside_method = None

    # Construct fully qualified method names
    fully_qualified_methods = []
    for method, changed in method_changes.items():
        if changed and package_name and class_name:
            fq_method = f"{package_name}.{class_name}.{method}()"
            fully_qualified_methods.append(fq_method)

    return fully_qualified_methods


# Process PR
changed_methods = get_pr_changes(REPO_NAME, PR_NUMBER)

if changed_methods:
    print("### 🔍 Changed Methods in PR:")
    for method in changed_methods:
        print(f"🔹 `{method}`")
else:
    print("✅ No changed methods found.")