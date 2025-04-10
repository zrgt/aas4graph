MATCH (sm0:Submodel)-[:child*0..]->(sme0:SubmodelElement {idShort:"Temperature"})
WHERE sme0.value > 50
RETURN sm0