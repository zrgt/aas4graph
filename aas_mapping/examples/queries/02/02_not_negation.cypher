MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Status"})
WHERE NOT sme0.value = 'Inactive'
RETURN sm0