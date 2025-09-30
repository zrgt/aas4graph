MATCH (sm0:Submodel)-[:submodelElements]->(sme:SubmodelElement {idShort: "SerialNumber"})
WHERE sme.value =~ 'SN[0-9]{4}'
RETURN sm0