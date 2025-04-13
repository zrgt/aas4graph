MATCH (sm0:Submodel),
      (sm0)-[:child]->(sme0:SubmodelElement {idShort:'ProductClassifications'})-[:child]->(sme1:SubmodelElement {idShort:'ProductClassificationItem'})-[:child]->(sme2:SubmodelElement {idShort:'ProductClassId'}),
      (sm0)-[:child]->(sme3:SubmodelElement)
WHERE sm0.idShort = 'TechnicalData'
  AND sme2.value = '27-37-09-05'
  AND sm0.idShort = 'TechnicalData'
  AND sme3.semanticId = '0173-1#02-BAF016#006'
  AND sme3.value < 100
RETURN sm0