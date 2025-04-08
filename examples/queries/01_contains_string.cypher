MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "Description"})
WHERE sme.value CONTAINS 'high-quality'
RETURN sm0
