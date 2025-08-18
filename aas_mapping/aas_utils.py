import re
from typing import Dict, Tuple, List

IDENTIFIABLE_KEYS = {
    "assetAdministrationShells": "AssetAdministrationShell",
    "submodels": "Submodel",
    "conceptDescriptions": "ConceptDescription",
}
IDENTIFIABLES = ("AssetAdministrationShell", "Submodel", "ConceptDescription")

AAS_CLS_PARENTS: dict[str, tuple[str]] = {
    'AssetAdministrationShell': ('Identifiable', 'Referable',),
    'ConceptDescription': ('Identifiable', 'Referable',),
    'Submodel': ('Identifiable', 'Referable', 'Qualifiable',),
    'Capability': ('SubmodelElement', 'Referable', 'Qualifiable',),
    'Entity': ('SubmodelElement', 'Referable', 'Qualifiable',),
    'BasicEventElement': ('EventElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'Operation': ('SubmodelElement', 'Referable', 'Qualifiable',),
    'RelationshipElement': ('SubmodelElement', 'Referable', 'Qualifiable',),
    'AnnotatedRelationshipElement': ('RelationshipElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'SubmodelElementCollection': ('SubmodelElement', 'Referable', 'Qualifiable',),
    'SubmodelElementList': ('SubmodelElement', 'Referable', 'Qualifiable', 'Generic',),
    'Blob': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'File': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'MultiLanguageProperty': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'Property': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'Range': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'ReferenceElement': ('DataElement', 'SubmodelElement', 'Referable', 'Qualifiable',),
    'DataSpecificationIec61360': ('DataSpecificationContent',),
}

def identify_types(obj: Dict) -> Tuple[str]:
    """Return the types of the given object."""
    RELATIONSHIP_TYPES = ("ExternalReference", "ModelReference")
    QUALIFIER_KINDS = ("ValueQualifier", "ConceptQualifier", "TemplateQualifier")

    if "modelType" in obj:
        class_name = obj["modelType"]
        types = (class_name, *AAS_CLS_PARENTS[class_name])
        return types
    elif "type" in obj and obj["type"] in RELATIONSHIP_TYPES:
        return ("Reference", obj["type"])
    elif "kind" in obj and obj["kind"] in QUALIFIER_KINDS:
        return ("Qualifier", obj["kind"])
    elif "language" in obj and "text" in obj:
        return ("LangString",)
    elif "assetKind" in obj:
        return ("AssetInformation",)
    else:
        return ("Unknown",)

def itemize_id_short_path(id_short_path: str) -> List[str]:
    """
    Split the idShortPath into a list of idShorts. Dot separated or brackets with index.

    Example Input: "MySubmodelElementCollection.MySubSubmodelElementList2[0][0].MySubTestValue3"
    Example Result: ["MySubmodelElementCollection", "MySubSubmodelElementList2", 0, 0, "MySubTestValue3"]
    :param idShortPath: The path to the idShort attribute.
    """
    pattern = r'([a-zA-Z_]\w*)|\[(\d+)\]'
    matches = re.findall(pattern, id_short_path)
    result = [match[0] if match[0] else int(match[1]) for match in matches]
    return result