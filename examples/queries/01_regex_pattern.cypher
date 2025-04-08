MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "SerialNumber"})
WHERE sme.value =~ 'SN[0-9]{4}'
RETURN sm0
