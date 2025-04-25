MATCH (sm0:Submodel)-[:child]->(sme0:SubmodelElement {idShort:"Documents"})-[:child]->(sme1:SubmodelElement)-[:child]->(sme2:SubmodelElement {idShort:"DocumentClassification"})-[:child]->(sme3:SubmodelElement {idShort:"Class"}),
      (sme1)-[:child]->(sme4:SubmodelElement {idShort:"DocumentVersion"})-[:child]->(mlp0:MultiLanguageProperty {idShort:"SMLLanguages"})-[:value]->(ls0:LangString)
WHERE sme3.value = '03-01'
  AND ls0.language = 'nl'
RETURN sm0