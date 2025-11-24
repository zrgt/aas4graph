MATCH (sm0:Submodel)-[:submodelElements]->(sme:SubmodelElement {idShort: "ProductCode"})
WHERE sme.value STARTS WITH 'ABC-'
RETURN sm0