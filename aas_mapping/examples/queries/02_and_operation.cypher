MATCH (sm0:Submodel)-[:submodelElements]->(sme1:SubmodelElement {idShort: "Color"}),
      (sm0)-[:submodelElements]->(sme2:SubmodelElement {idShort: "Size"})
WHERE sme1.value = 'Blue'
  AND sme2.value > 50
RETURN sm0
