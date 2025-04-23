MATCH (sm0:Submodel)-[:child]->(sme:SubmodelElement {idShort: 'Weight'})
WHERE sme.value >= 100
RETURN sm0