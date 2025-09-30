MATCH (sm0:Submodel)-[:submodelElements]->(sme1:SubmodelElement {idShort: "Material"}),
      (sm0)-[:value]->(sme2:SubmodelElement {idShort: "Weight"})
WHERE (sme1.value = 'Steel' OR sme1.value = 'Aluminum')
  AND sme2.value < 200
RETURN sm0