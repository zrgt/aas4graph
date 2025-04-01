MATCH (sm0)-[:child*0..]->(sme0:SubmodelElement {idShort:"FileVersion"})-[:child]->(sme1:SubmodelElement)-[:child]->(sme2:SubmodelElement {idShort:"FileVersionId"}),
      (sme1)-[:child]->(sme3:SubmodelElement {idShort:"FileName"})
WHERE sme2.value = '1.1'
  AND sme3.value = 'SomeFile'
RETURN sm0