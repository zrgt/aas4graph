import unittest
import os
import json
import sys
from translator import AASQueryTranslator

# Set the base directory and where queries live
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_QUERY_DIR = os.path.join(BASE_DIR, "aas_mapping", "examples", "queries")

print("Looking for test queries in:", TEST_QUERY_DIR)


class TestAASTranslator(unittest.TestCase):
    LEVEL = None  # Class-level variable for optional filtering

    def test_all_queries(self):
        pairs = self.find_query_pairs(TEST_QUERY_DIR, self.LEVEL)

        for name, json_path, cypher_path in pairs:
            with self.subTest(name=name):
                with open(json_path, "r", encoding="utf-8") as jf:
                    aas_query = json.load(jf)
                with open(cypher_path, "r", encoding="utf-8") as cf:
                    expected_cypher = cf.read().strip()

                translator = AASQueryTranslator(aas_query)
                result = translator.translate().strip()

                self.assertEqual(result, expected_cypher)

    def find_query_pairs(self, root_directory, level_filter=None):
        query_pairs = []
        for subdir, _, files in os.walk(root_directory):
            if level_filter and not subdir.endswith(level_filter):
                continue
            json_files = [f for f in files if f.endswith(".json")]
            for jf in json_files:
                base = jf[:-5]
                cypher_file = base + ".cypher"
                json_path = os.path.join(subdir, jf)
                cypher_path = os.path.join(subdir, cypher_file)
                if os.path.exists(cypher_path):
                    test_name = os.path.relpath(json_path, root_directory).replace("\\", "/")
                    query_pairs.append((test_name, json_path, cypher_path))
        return query_pairs


if __name__ == "__main__":
    # Support running a specific level: python TestAASTranslator.py 01
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        TestAASTranslator.LEVEL = sys.argv[1]
        sys.argv.pop(1)  # Remove the custom argument so unittest doesn't get confused

    unittest.main()

#         # ================================
# # Manual translation tests
# # ================================

# # Define all your hardcoded queries
#   queries = {
#     "01_starts_with": {
#   "$condition": {
#     "$starts-with": [
#           { "$field": "$sme.EmailAddress#value" },
#           { "$strVal": "email@" }    
#     ]
#   }
# },
#     "02_regex_serial_number": {
#   "$condition": {
#     "$regex": [
#       { "$field": "$sme.SerialNumber#value" },
#       { "$strVal": "^[0-9]{8}$" }
#     ]
#   }
# },
#     "03_contains": {
#   "$condition": {
#     "$contains": [
#       { "$field": "$sme.URIOfTheProduct#value" },
#       { "$strVal": "domain-abc" }
#     ]
#   }
# },
#     "04_ge_year_of_construction": {
#   "$condition": {
#     "$ge": [
#       { "$field": "$sme.YearOfConstruction#value" },
#       { "$numVal": 2020 }
#     ]
#   }
# },
#     "05_ne_country_of_origin": {
#   "$condition": {
#     "$ne": [
#       { "$field": "$sme.CountryOfOrigin#value" },
#       { "$strVal": "US" }
#     ]
#   }
# }
# }

# # Translate and print each one
# for name, aas_query in queries.items():
#     print("\n---")
#     print(f"Translating query: {name}")
#     translator = AASQueryTranslator(aas_query)
#     cypher_output = translator.translate()
#     print("Generated Cypher:")
#     print(cypher_output)
#     print("---\n")






# import unittest
# from translator import AASQueryTranslator 

# class TestAASTranslator(unittest.TestCase):

#     def test_contains_string(self):
#         aas_query = {
#     "$condition": {
#       "$contains": [
#         { "$field": "$sme.Description#value" },
#         { "$strVal": "high-quality" }
#       ]
#     }
#   }

#         expected_cypher = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Description"})
# WHERE sme0.value CONTAINS 'high-quality'
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_cypher.strip())

#     def test_ne_filter(self):
#         aas_query = {
#         "$condition": {
#           "$ne": [
#             { "$field": "$sme.Material#value" },
#             { "$strVal": "Plastic" }
#           ]
#         }
#       }

#         expected_cypher = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Material"})
# WHERE sme0.value <> 'Plastic'
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_cypher.strip())

#     def test_ge_filter(self):
#         aas_query = {
#     "$condition": {
#       "$ge": [
#         { "$field": "$sme.Weight#value" },
#         { "$numVal": 100 }
#       ]
#     }
#   }

#         expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Weight"})
# WHERE sme0.value >= 100
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_output.strip())

#     def test_gt_filter(self):
#         aas_query = {
#     "$condition": {
#       "$gt": [
#         { "$field": "$sme.Temperature#value" },
#         { "$numVal": 50 }
#       ]
#     }
#   }
    
#         expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Temperature"})
# WHERE sme0.value > 50
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_output.strip())

#     def test_regex_pattern(self):
#         aas_query = {
#     "$condition": {
#       "$regex": [
#         { "$field": "$sme.SerialNumber#value" },
#         { "$strVal": "SN[0-9]{4}" }
#       ]
#     }
#   }
    
#         expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "SerialNumber"})
# WHERE sme0.value =~ 'SN[0-9]{4}'
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_output.strip())

#     def test_starts_with(self):
#         aas_query = {
#     "$condition": {
#         "$starts-with": [
#           { "$field": "$sme.ProductCode#value" },
#           { "$strVal": "ABC-" }
#         ]
#       }
#     }
    
#         expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "ProductCode"})
# WHERE sme0.value STARTS WITH 'ABC-'
# RETURN sm0"""

#         translator = AASQueryTranslator(aas_query)
#         cypher = translator.translate().strip()

#         self.assertEqual(cypher, expected_output.strip())



# if __name__ == '__main__':
#     unittest.main()
