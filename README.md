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
- Only Serialization of AAS to Neo4j is implemented, the Deserialization from Neo4j is not
- AAS Query Language Mapping to Cypher
- Works only with ObjStore

# Getting started

## Run Neo4J server
```
YOUR_PATH_TO_NEO4J\neo4j-community-5.23.0\bin\neo4j console
```
C:\Users\igor\neo4j\neo4j-community-5.23.0\bin\neo4j console

## Add the AAS to Neo4j
```python
import neo4j
from aas_mapping.aas2neo import AASToNeo4j

neo4j_driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", 
                                          auth=("neo4j", "password"))
translator = AASToNeo4j.read_aas_json_file("SOME_AAS.json")
translator.execute_clauses(neo4j_driver)
```

## Show all nodes in Neo4j Browser
```
MATCH (n)
RETURN n;
```
