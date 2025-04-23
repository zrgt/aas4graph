MATCH (sm0:Submodel)-[:child]->(sme:SubmodelElement {idShort: "ProductCode"})
WHERE sme.value STARTS WITH 'ABC-'
RETURN sm0