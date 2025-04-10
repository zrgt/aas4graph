MATCH (sm0:Submodel)-[:child*0..]->(sme1:SubmodelElement {idShort: "Material"}),
      (sm0)-[:child*0..]->(sme2:SubmodelElement {idShort: "Weight"})
WHERE (sme1.value = 'Steel' OR sme1.value = 'Aluminum')
  AND sme2.value < 200
RETURN sm0