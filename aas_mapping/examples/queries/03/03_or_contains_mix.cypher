MATCH (sm0),
      (sm0)-[:child]->(sme0:SubmodelElement {idShort: "Description"})
WHERE sme0.value CONTAINS 'urgent'
   OR sm0.idShort = "MaintenanceLog"
RETURN sm0
