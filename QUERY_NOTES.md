# AAS Query Language

- $match - The $match operator signals that the following clauses (a) contain at least 1 list of elements with [] syntax, and that (b) all conditions shall be evaluated on the same element of this list. (https://admin-shell-io.github.io/aas-specs-antora/IDTA-01002/v3.1/query-language.html#_match_of_elements_in_lists)

# AAS Query Language to Cypher Query

AAS Query (Written in AAS Query Language) -> Cypher Query
Cypher Query -> Neo4j -> Neo4J Result
Neo4J Result -> AAS Query Result

## Examples

Note: The following examples are written in AAS Query Language. To see the corresponding Cypher Query, please check the folder `aas_mapping/examples/queries`.

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
