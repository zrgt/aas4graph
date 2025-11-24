MATCH (sm0:Submodel)-[:submodelElements]->(sme:SubmodelElement {idShort: 'Weight'})
WHERE sme.value >= 100
RETURN sm0