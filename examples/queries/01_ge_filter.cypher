  MATCH (sm0:Submodel)-[:child*0..]->(sme:SubmodelElement {idShort: "Weight"})
  WHERE sme.value >= 100
  RETURN sm0