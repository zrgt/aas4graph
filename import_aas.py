# import neo4j
# from aas_mapping.aas2neo import AASToNeo4j

# # Connect to Neo4j
# neo4j_driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", 
#                                         auth=("neo4j", "password"))

# # Import an AAS file
# translator = AASToNeo4j.read_aas_json_file("aas_mapping/submodels/IDTA 02006-2-0_Template_Digital Nameplate.json")
# translator.execute_clauses(neo4j_driver) 

import neo4j
from aas_mapping.aas2neo import AASToNeo4j

# Connect to Neo4j
neo4j_driver = neo4j.GraphDatabase.driver("bolt://localhost:7689", 
                                        auth=("neo4j", "password"))

# Import an AAS file
translator = AASToNeo4j.read_aas_json_file("aas_mapping/submodels/IDTA 02006-2-0_Template_Digital Nameplate.json")
translator.execute_clauses(neo4j_driver) 

