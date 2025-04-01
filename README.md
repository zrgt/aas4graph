# AAS - Neo4j

This project is a proof of concept for the mapping of the Asset Administration Shell (AAS) in a Neo4J graph database.


# How it works

It reads an AAS and generates a Cypher clauses to create the graph in Neo4j.
These clauses are then executed in the Neo4j database.

## AAS - Neo4j Mapping

1. ``Referable`` = ``Node``
1. ``AssetInformation`` = ``Node``
2. If ``Referable`` contains other ``Referable`` -> ``Relationship``
3. ``Reference`` is a ``Relationship``

## Limitation or Not implemented
- Only basic Deserialization from Neo4j is implemented
- AAS Query Language Mapping to Cypher

# Getting started

## Run Neo4J server
```
YOUR_PATH_TO_NEO4J\neo4j-community-5.23.0\bin\neo4j console
```

## Add the AAS to Neo4j

```python
from aas_mapping.aasjson2neo import AASNeo4JClient

aas_neo4j_client = AASNeo4JClient(uri="bolt://localhost:7687", user="neo4j", password="password")
aas_neo4j_client.upload_aas_json("SOME_AAS.json")
```

## Show all nodes in Neo4j Browser
```
MATCH (n)
RETURN n;
```
