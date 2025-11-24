MATCH (sm0:Submodel)-[:submodelElements]->(sme1:SubmodelElement {idShort: "Material"}),
      (sm0)-[:value]->(sme2:SubmodelElement {idShort: "Weight"})
WHERE sme1.value = 'Metal'
   OR sme2.value <= 50
RETURN sm0