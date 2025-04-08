MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "ProductCode"})
WHERE sme.value STARTS WITH 'ABC-'
RETURN sm0