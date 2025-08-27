import pandas as pd

file_path = r"C:\Users\AnandYadav\final_code_web_testing_playwright\playwright\llm-automation\fs_files\automation_plan_results.md"

# Read the file
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Convert to DataFrame
from io import StringIO
df = pd.read_csv(StringIO(content), sep="|", engine="python")

# Drop extra empty columns caused by markdown table borders
df = df.dropna(axis=1, how="all")

# Strip whitespace from column names
df.columns = [c.strip() for c in df.columns]

with open(r"C:\Users\AnandYadav\final_code_web_testing_playwright\playwright\llm-automation\result.csv", "w", encoding="utf-8", newline='') as f:
    df.to_csv(f, index=False)
