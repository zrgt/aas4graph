MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "SerialNumber"})
WHERE sme0.value =~ 'SN[0-9]{4}'
RETURN sm0