MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "Status"})
WHERE NOT sme.value = 'Inactive'
RETURN sm0
