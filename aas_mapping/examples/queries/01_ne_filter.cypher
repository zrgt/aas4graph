MATCH (sm0:Submodel)-[:submodelElements]->(sme:SubmodelElement {idShort: "Material"})
WHERE sme.value <> 'Plastic'
RETURN sm0