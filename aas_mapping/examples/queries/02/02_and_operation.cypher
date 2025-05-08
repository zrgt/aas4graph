MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort: "Color"}),
      (sm0)-[:child]->(sme1:SubmodelElement {idShort: "Size"})
WHERE sme0.value = 'Blue' AND sme1.value > 50
RETURN sm0