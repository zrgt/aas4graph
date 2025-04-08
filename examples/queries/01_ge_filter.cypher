  MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "Weight"})
  WHERE sme.value >= 100
  RETURN sm0