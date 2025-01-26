from basyx.aas.model import Referable, Qualifier, Extension, EmbeddedDataSpecification, AdministrativeInformation, \
    AssetInformation, Resource, DataSpecificationContent, Reference, ModelReference, DataSpecificationIEC61360, \
    AssetAdministrationShell, ConceptDescription, SubmodelElement, Submodel, HasDataSpecification, HasExtension, \
    HasKind, HasSemantics, Namespace, UniqueIdShortNamespace, LangStringSet, ValueReferencePair

NODE_TYPES = (
    Qualifier, Extension, EmbeddedDataSpecification, AdministrativeInformation, AssetInformation, Resource,
    DataSpecificationContent,
    Submodel, SubmodelElement,
    DataSpecificationIEC61360, AssetAdministrationShell, ConceptDescription,
    LangStringSet, ValueReferencePair)
RELATIONSHIP_TYPES = (Reference, ModelReference)

ATTRS_TO_IGNORE = ('namespace_element_sets', 'self', 'parent', 'source')

IGNORED_PARENT_CLASSES = [
    # Abstract or general classes
    object,
    HasDataSpecification,
    HasExtension,
    HasKind,
    HasSemantics,
    # Namespaces
    Namespace,
    UniqueIdShortNamespace,
]