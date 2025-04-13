MATCH (sm0:Submodel)-[:child]->(sme1:SubmodelElement {idShort: "Material"}),
      (sm0)-[:child]->(sme2:SubmodelElement {idShort: "Weight"})
WHERE (sme1.value = 'Steel' OR sme1.value = 'Aluminum')
  AND sme2.value < 200
RETURN sm0