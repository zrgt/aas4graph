MATCH (sm0:Submodel)-[:child]->(sme:SubmodelElement {idShort: "Status"})
WHERE NOT sme.value = 'Inactive'
RETURN sm0