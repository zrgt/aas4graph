from basyx.aas.model import Referable, Qualifier, Extension, EmbeddedDataSpecification, AdministrativeInformation, \
    AssetInformation, Resource, DataSpecificationContent, Reference, ModelReference, DataSpecificationIEC61360, \
    HasDataSpecification, HasExtension, HasKind, HasSemantics, Namespace, UniqueIdShortNamespace, LangStringSet, \
    ValueReferencePair

COMPLEX_TYPES = (
    AdministrativeInformation,
    AssetInformation,
    DataSpecificationContent,
    DataSpecificationIEC61360,
    EmbeddedDataSpecification,
    Extension,
    LangStringSet,
    Qualifier,
    Resource,
    ValueReferencePair
)


class LangString:
    def __init__(self, lcode: str, value: str):
        self.lcode = lcode
        self.value = value


NODE_TYPES = (
    Referable,
    Reference,
    LangString,
    *COMPLEX_TYPES,
)

RELATIONSHIP_TYPES = (
    Reference,
    ModelReference
)

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
