# AAS Query Language

- $match - The $match operator signals that the following clauses (a) contain at least 1 list of elements with [] syntax, and that (b) all conditions shall be evaluated on the same element of this list. (https://admin-shell-io.github.io/aas-specs-antora/IDTA-01002/v3.1/query-language.html#_match_of_elements_in_lists)

# AAS Query Language to Cypher Query

AAS Query (Written in AAS Query Language) -> Cypher Query
Cypher Query -> Neo4j -> Neo4J Result
Neo4J Result -> AAS Query Result

## Examples

### Single comparison
```json
{
  "$condition": {
    "$eq": [
      { "$field": "$aas#idShort" },
      {
        "$field":
            "$aas#assetInformation.assetType"
      }
    ]
  }
}
```

```cypher
MATCH (aas:AssetAdministrationShell)-[:assetInformation]->(assetInformation)  
WHERE aas.idShort = assetInformation.assetType
RETURN aas, asset
```

### HandoverDocumentation with VDI 2770 Class 03-01 Commissioning and language NL (as expected with SubmodelElementList)

```json
{
  "$condition": {
    "$match": [
      { "$eq": [
          { "$field": "$sme.Documents[].DocumentClassification.Class#value" },
          { "$strVal": "03-01" }
        ]
      },
      { "$eq": [
          { "$field": "$sme.Documents[].DocumentVersion.SMLLanguages[]#language" },
          { "$strVal": "nl" }
        ]
      }
    ]
  }
}
```

```cypher
MATCH (docs:SubmodelElement)-[:value]->(doc:SubmodelElement)-[:value]->(doc_clas:SubmodelElement)-[:value]->(class:SubmodelElement),
      (docs)-[:value]->(doc_ver:SubmodelElement)-[:value]->(langs:SubmodelElement)-[:value]->(lang:SubmodelElement)
WHERE docs.idShort = "Documents" 
  AND doc_clas.idShort = "DocumentClassification" 
  AND class.idShort = "Class" 
  AND class.value = "03-01"
  AND doc_ver.idShort = "DocumentVersion"
  AND lang.idShort = "SMLLanguages"
  AND lang.language = "nl"
RETURN sm
```

OR

```cypher
MATCH (sme)-[:ids_Documents]->(docs:SubmodelElement)-[:value]->(doc:SubmodelElement)-[:ids_DocumentClassification]->(doc_clas:SubmodelElement)-[:ids_Class]->(class:SubmodelElement),
      (docs)-[:ids_DocumentVersion]->(doc_ver:SubmodelElement)-[:ids_SMLLanguages]->(langs:SubmodelElement)-[:value]->(lang:SubmodelElement)
WHERE class.value = "03-01"
  AND lang.language = "nl"
RETURN docs
```

OR

```cypher
MATCH (docs:SE)-[:value]->(doc:SE)-[:ids_DocumentClassification]->(doc_clas:SE)-[:ids_Class]->(class:SE),
      (docs)-[:ids_DocumentVersion]->(doc_ver:SE)-[:ids_SMLLanguages]->(langs:SE)-[:value]->(lang:SE)
WHERE docs.idShort = "Documents" 
  AND class.value = "03-01"
  AND lang.language = "nl"
RETURN docs
```


### TechnicalData with motor starter (ECLASS ClassId = 27-37-09-05) and width less than 100 mm

```json
{
  "$condition": {
    "$and": [
      { "$match": [
          { "$eq": [
              { "$field": "$sm#idShort" },
              { "$strVal": "TechnicalData" }
            ]
          },
          { "$eq": [
              {
                "$field":
                "$sme.ProductClassifications.ProductClassificationItem.ProductClassId#value"
              },
              { "$strVal": "27-37-09-05" }
            ]
          }
        ]
      },
      { "$match": [
          {
            "$eq": [
              { "$field": "$sm#idShort" },
              { "$strVal": "TechnicalData" }
            ]
          },
          {
            "$eq": [
              { "$field": "$sme#semanticId" },
              { "$strVal": "0173-1#02-BAF016#006" }
            ]
          },
          {
            "$lt": [
              { "$field": "$sme#value" },
              { "$numVal": 100 }
            ]
          }
        ]
      }
    ]
  }
}
```

```cypher
MATCH (sm:Submodel)-[:submodelElement]->(prod_class:SubmodelElement)-[:value]->(prod_class_item:SubmodelElement)-[:value]->(prod_class_id:SubmodelElement),
      (sm)-[:submodelElement]->(sme:SubmodelElement)
WHERE sm.idShort = "TechnicalData" 
  AND prod_class.idShort = "ProductClassifications" 
  AND prod_class_item.idShort = "ProductClassificationItem" 
  AND prod_class_id.idShort = "ProductClassId" 
  AND prod_class_id.value = "27-37-09-05"
  AND sme.semanticId = "0173-1#02-BAF016#006"
  AND sme.value < 100
RETURN sm
```

OR

```cypher
MATCH (sm:SM)-[:ids_ProductClassifications]->(prod_class:SE)-[:ids_ProductClassificationItem]->(prod_class_item:SE)-[:ids_ProductClassId]->(prod_class_id:SE),
      (sm)-[:value]->(sme:SE)
WHERE sm.idShort = "TechnicalData" 
  AND prod_class_id.value = "27-37-09-05"
  AND sme.semanticId = "0173-1#02-BAF016#006"
  AND sme.value < 100
RETURN sm
```

