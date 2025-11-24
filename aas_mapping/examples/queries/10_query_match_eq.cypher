MATCH (sm0:Submodel)-[:submodelElements]->(sme0:SubmodelElement {idShort:"Documents"})-[:value]->(sme1:SubmodelElement)-[:value]->(sme2:SubmodelElement {idShort:"DocumentClassification"})-[:value]->(sme3:SubmodelElement {idShort:"Class"}),
      (sme1)-[:value]->(sme4:SubmodelElement {idShort:"DocumentVersion"})-[:value]->(mlp0:MultiLanguageProperty {idShort:"SMLLanguages"})
WHERE sme3.value = '03-01'
  AND 'nl' IN mlp0.value_language
RETURN sm0