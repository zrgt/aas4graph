import os
import json
import unittest
from pathlib import Path
from aas_mapping.aas_neo4j_adapter.querification.aasql_to_ast import parse_aasql_query

class TestQuerriesToAstExamples(unittest.TestCase):
    def test_examples_parse_to_expected_ast(self):
        query_dir = "aas_mapping/examples/queries"
        solution_dir = "aas_mapping/examples/ast"
        for file_name in os.listdir(query_dir):
            if file_name.endswith(".json"):
                query_path = os.path.join(query_dir, file_name)
                solution_path = os.path.join(solution_dir, file_name.replace(".json", ".repr"))
                if Path(solution_path).is_file():
                    with open(query_path) as f:
                        query = json.load(f)
                    with open(solution_path) as f:
                        solution_repr = f.read()
                    result = parse_aasql_query(query)
                    self.assertEqual(solution_repr, repr(result), f"Error at {file_name}")



if __name__ == '__main__':
    unittest.main()
