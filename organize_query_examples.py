import os
import shutil

# Set this to your query folder location
QUERY_DIR = os.path.join("aas_mapping", "examples", "queries")

# List of valid levels (including 00 now)
LEVELS = {"00", "01", "02", "03", "04", "09", "10", "20"}

def organize_queries_by_level(query_dir):
    for file in os.listdir(query_dir):
        if file.endswith(".json") or file.endswith(".cypher"):
            parts = file.split("_")
            if not parts:
                continue
            level = parts[0]
            if level in LEVELS:
                level_dir = os.path.join(query_dir, level)
                os.makedirs(level_dir, exist_ok=True)

                src = os.path.join(query_dir, file)
                dst = os.path.join(level_dir, file)
                print(f"Moving: {file} → {level}/")
                shutil.move(src, dst)

if __name__ == "__main__":
    organize_queries_by_level(QUERY_DIR)
    print("Done organizing queries into levels:", ", ".join(sorted(LEVELS)))
