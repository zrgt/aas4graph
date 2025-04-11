MATCH (sm0:Submodel)-[:child]->(sme:SubmodelElement {idShort: "Material"})
WHERE sme.value <> 'Plastic'
RETURN sm0