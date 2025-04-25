MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Material"})
WHERE sme0.value <> 'Plastic'
RETURN sm0