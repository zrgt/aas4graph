MATCH (sm0:Submodel)-[:submodelElements]->(sme:SubmodelElement {idShort: "Status"})
WHERE NOT sme.value = 'Inactive'
RETURN sm0