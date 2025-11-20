# AAS - Neo4j

This project is a proof of concept for the mapping of the Asset Administration Shell (AAS) in a Neo4J graph database.


# How it works

It reads an AAS and generates a Cypher clauses to create the graph in Neo4j.
These clauses are then executed in the Neo4j database.


We have developed Classes to map the Cypher MATCH clause and its variables

## AAS - Neo4j Mapping

1. ``Referable`` = ``Node``
1. ``AssetInformation`` = ``Node``
2. If ``Referable`` contains other ``Referable`` -> ``Relationship``
3. ``Reference`` is a ``Relationship``

### Model dicts in Neo4J as lists
In Neo4J it is not possible to save dicts or list of dicts in a node property.
By creating separate nodes for each dict and connecting them with relationships, we complicate the model and the Neo4J writing process will be longer.
That's why we decided to model lists of dicts as multiple lists where each list represent values saved under one key.


## Limitation or Not implemented
- Only basic Deserialization from Neo4j is implemented
- AAS Query Language Mapping to our Cypher Schema is not implemented yet
Todo:
- Resolve ModelReferences 
- Resolve ExternalReferences for EClass
- Model ECLASS as Nodes with their classifications

# Getting started

## Run Neo4J server
```
YOUR_PATH_TO_NEO4J\neo4j-community-5.26.10\bin\neo4j console
```

## Add the AAS to Neo4j

```python
from aas_mapping.aas_neo4j_adapter.aas_neo4j_client import AASNeo4JClient

aas_neo4j_client = AASNeo4JClient(uri="bolt://localhost:7687", user="neo4j", password="12345678", 
                                  model_config=AAS_NEO4J_MODEL_CONFIG)
aas_neo4j_client.upload_json_file("SOME_AAS.json")
```

## Show all nodes in Neo4j Browser
```
MATCH (n)
RETURN n;
```
