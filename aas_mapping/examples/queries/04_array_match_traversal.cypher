MATCH (sm0:Submodel)-[:child*0..]->(sme0:SubmodelElement {idShort:"Components"})-[:child]->(sme1:SubmodelElement),
      (sme1)-[:child]->(sme2:SubmodelElement {idShort:"Name"}),
      (sme1)-[:child]->(sme3:SubmodelElement {idShort:"Status"})
WHERE sme2.value = "Motor" AND sme3.value = "Active"
RETURN sm0