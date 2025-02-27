import sys
import os
import requests
import re
import pandas as pd

# Get GitHub Token & Repository Name from Environment Variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")  # 'owner/repo'

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
print(f"PR number provided: {PR_NUMBER}")

# Load method mappings from CSV
method_df = pd.read_csv("data/Method.csv", header=None, names=["unique_identifier", "method"])  # Unique identifier → Method
testcase_df = pd.read_csv("data/Testcases.csv", header=None, names=["unique_identifier", "testcase"])  # Unique identifier → Test case
method_vs_testcase_df = pd.read_csv("data/Embedding.csv", header=None, names=["method_id", "testcase_id(s)"])  # Mappings

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
            file_path = file['filename']
            methods = extract_fully_qualified_methods(patch, file_path)
            changed_methods.extend(methods)

    return changed_methods

# Convert file path to package.class dynamically
def get_fully_qualified_class(file_path):
    file_path = re.sub(r"^src/main/java/|^src/", "", file_path)
    return file_path.replace("/", ".").replace(".java", "")

# Extract method names from Git diff
def extract_fully_qualified_methods(patch, file_path):
    package_class_name = get_fully_qualified_class(file_path)
    
    method_pattern = re.compile(r"\b(public|private|protected|static|\s)*\s*[\w<>]+\s+(\w+)\s*\(")
    
    inside_method = None
    method_changes = {}  # {method_name: has_changes}
    brace_count = 0  # Tracks the number of `{}` braces

    for line in patch.split("\n"):
        if line.startswith("+++ ") or line.startswith("--- "):  # Ignore file metadata
            continue

        # Detect method header
        match = method_pattern.search(line)
        if match:
            inside_method = match.group(2)  # Extract method name
            method_changes[inside_method] = False  # Initially mark as unchanged
            brace_count = 0  # Reset brace count when entering a method

        # Track changes inside a method
        if inside_method and (line.startswith("+") or line.startswith("-")):
            # Ensure the change is inside the method (by checking brace count)
            if brace_count > 0:
                method_changes[inside_method] = True  # Mark as changed

        # Track opening/closing braces `{}` to ensure we're inside a method
        brace_count += line.count("{") - line.count("}")

        # Exit method when braces close
        if inside_method and brace_count == 0:
            inside_method = None

    # Construct fully qualified method names
    fully_qualified_methods = []
    for method, changed in method_changes.items():
        if changed:
            fq_method = f"{package_class_name}.{method}()"
            fully_qualified_methods.append(fq_method)

    return fully_qualified_methods

# Get corresponding test cases
def get_related_test_cases(changed_methods):
    method_to_tests = {}

    for method in changed_methods:
        # Find unique identifier of method
        method_row = method_df[method_df['method'] == method]
        if method_row.empty:
            print(f"⚠️ Warning: No matching method found for `{method}` in `method.csv`")
            continue

        method_id = method_row.iloc[0]['unique_identifier']

        # Find test cases for method_id in methodvstestcase.csv
        test_row = method_vs_testcase_df[method_vs_testcase_df['method_id'] == method_id]
        if test_row.empty:
            print(f"⚠️ Warning: No test cases found for `{method}` (ID: {method_id}) in `methodvstestcase.csv`")
            continue

        testcase_ids = test_row.iloc[0]['testcase_id(s)'].split('_')

        # Fetch actual test case names
        test_cases = testcase_df[testcase_df['unique_identifier'].isin(testcase_ids)]['testcase'].tolist()
        method_to_tests[method] = test_cases

    return method_to_tests

# Process PR
changed_methods = get_pr_changes(REPO_NAME, PR_NUMBER)

if changed_methods:
    print("\n### 🔍 Changed Methods & Associated Test Cases:")
    method_test_cases = get_related_test_cases(changed_methods)

    for method, testcases in method_test_cases.items():
        print(f"🔹 `{method}` → 🧪 Test Cases: {', '.join(testcases) if testcases else 'None found'}")
else:
    print("✅ No changed methods found.")
