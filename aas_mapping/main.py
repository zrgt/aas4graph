import os
import json
from aas_mapping.parser import parse_query
from pprint import pprint
from aas_mapping.ast2cypher import converter

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    query_dir = os.path.join(project_root, "aas_mapping", "examples", "queries")
    for file_name in os.listdir(query_dir):
        if file_name.endswith(".json"):
            path = os.path.join(query_dir, file_name)
            with open(path, "r") as f:
                data = json.load(f)
            ast = parse_query(data)
            print(f"--- {file_name} ---")
            print()
            pprint(ast)
            print()
            cypher = converter(ast)
            print(cypher)
            print()
            print("------------------------------")

if __name__ == "__main__":
    main()
