MATCH (sm0:Submodel),
      (sm0)-[:submodelElements]->(sme0:SubmodelElement {idShort:'ProductClassifications'})-[:value]->(sme1:SubmodelElement {idShort:'ProductClassificationItem'})-[:value]->(sme2:SubmodelElement {idShort:'ProductClassId'}),
      (sm0)-[:submodelElements]->(sme3:SubmodelElement)-[:semanticId]->(sid0)
WHERE sm0.idShort = 'TechnicalData'
  AND sme2.value = '27-37-09-05'
  AND sm0.idShort = 'TechnicalData'
  AND sid0 = '0173-1#02-BAF016#006'
  AND sme3.value < 100
RETURN sm0