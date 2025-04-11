MATCH (sm0:Submodel)-[:child]->(sme:SubmodelElement {idShort: "Description"})
WHERE sme.value CONTAINS 'high-quality'
RETURN sm0