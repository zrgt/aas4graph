MATCH (sm0:Submodel)-[:child*0..]->(sme1:SubmodelElement {idShort: "Color"}),
      (sm0)-[:child*0..]->(sme2:SubmodelElement {idShort: "Size"})
WHERE sme1.value = 'Blue'
  AND sme2.value > 50
RETURN sm0