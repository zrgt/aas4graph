MATCH (sm0:Submodel)-[:submodelElements]->(sme0:SubmodelElement {idShort:"FileVersion"})-[:value]->(sme1:SubmodelElement)-[:value]->(sme2:SubmodelElement {idShort:"FileVersionId"}),
      (sme1)-[:value]->(sme3:SubmodelElement {idShort:"FileName"})
WHERE sme2.value = '1.1'
  AND sme3.value = 'SomeFile'
RETURN sm0