MATCH (sm0:Submodel {idShort:"TechnicalData"}),
      (sm0)-[:child]->(sme0:SubmodelElement {idShort:"Pressure"})
WHERE sme0.value < 200
RETURN sm0