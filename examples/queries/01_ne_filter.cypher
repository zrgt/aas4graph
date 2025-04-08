  MATCH (sm0)-[:child*0..]->(sme:SubmodelElement {idShort: "Material"})
  WHERE sme.value <> 'Plastic'
  RETURN sm0