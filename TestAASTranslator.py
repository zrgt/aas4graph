import unittest
from translator import AASQueryTranslator 

class TestAASTranslator(unittest.TestCase):

    def test_contains_string(self):
        aas_query = {
    "$condition": {
      "$contains": [
        { "$field": "$sme.Description#value" },
        { "$strVal": "high-quality" }
      ]
    }
  }

        expected_cypher = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Description"})
WHERE sme0.value CONTAINS 'high-quality'
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_cypher.strip())

    def test_ne_filter(self):
        aas_query = {
        "$condition": {
          "$ne": [
            { "$field": "$sme.Material#value" },
            { "$strVal": "Plastic" }
          ]
        }
      }

        expected_cypher = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Material"})
WHERE sme0.value <> 'Plastic'
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_cypher.strip())

    def test_ge_filter(self):
        aas_query = {
    "$condition": {
      "$ge": [
        { "$field": "$sme.Weight#value" },
        { "$numVal": 100 }
      ]
    }
  }

        expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Weight"})
WHERE sme0.value >= 100
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_output.strip())

    def test_gt_filter(self):
        aas_query = {
    "$condition": {
      "$gt": [
        { "$field": "$sme.Temperature#value" },
        { "$numVal": 50 }
      ]
    }
  }
    
        expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Temperature"})
WHERE sme0.value > 50
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_output.strip())

    def test_regex_pattern(self):
        aas_query = {
    "$condition": {
      "$regex": [
        { "$field": "$sme.SerialNumber#value" },
        { "$strVal": "SN[0-9]{4}" }
      ]
    }
  }
    
        expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "SerialNumber"})
WHERE sme0.value =~ 'SN[0-9]{4}'
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_output.strip())

    def test_starts_with(self):
        aas_query = {
    "$condition": {
        "$starts-with": [
          { "$field": "$sme.ProductCode#value" },
          { "$strVal": "ABC-" }
        ]
      }
    }
    
        expected_output = """MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "ProductCode"})
WHERE sme0.value STARTS WITH 'ABC-'
RETURN sm0"""

        translator = AASQueryTranslator(aas_query)
        cypher = translator.translate().strip()

        self.assertEqual(cypher, expected_output.strip())



if __name__ == '__main__':
    unittest.main()
