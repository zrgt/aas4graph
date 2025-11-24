MATCH (aas:AssetAdministrationShell)-[:assetInformation]->(assetInformation)  
WHERE aas.idShort = assetInformation.assetType
RETURN aas