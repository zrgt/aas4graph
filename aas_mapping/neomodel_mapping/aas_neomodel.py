from neomodel import StructuredNode, StringProperty, RelationshipTo, BooleanProperty, DateTimeProperty, ArrayProperty, \
    StructuredRel, ZeroOrOne, ZeroOrMore, OneOrMore, One


class ReferenceRel(StructuredRel):
    key = ArrayProperty()
    referred_semantic_id = RelationshipTo('AssetAdministrationShellNode', 'referred_semantic_id', cardinality=ZeroOrOne)


class ModelReferenceRel(ReferenceRel):
    key = ArrayProperty()
    type = StringProperty()
    referred_semantic_id = RelationshipTo('ANYNode', 'referred_semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)


class QualifierNode(StructuredNode):
    type = StringProperty()
    value_type = StringProperty()
    value = StringProperty()
    value_id = RelationshipTo('ANYNode', 'value_id', model=ReferenceRel, cardinality=ZeroOrOne)
    kind = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)


class ExtensionNode(StructuredNode):
    name = StringProperty()
    value_type = StringProperty()
    value = StringProperty()
    refers_to = RelationshipTo('ReferableNodeNode', 'refers_to', model=ModelReferenceRel, cardinality=OneOrMore)
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)


class EmbeddedDataSpecificationNode(StructuredNode):
    data_specification = RelationshipTo('ANYNode', 'data_specification', model=ReferenceRel, cardinality=One)
    data_specification_content = RelationshipTo('DataSpecificationContentNode', 'data_specification_content',
                                                cardinality=One)


class AdministrativeInformationNode(StructuredNode):
    version = StringProperty()
    revision = StringProperty()
    creator = RelationshipTo('ANYNode', 'creator', model=ReferenceRel, cardinality=ZeroOrOne)
    template_id = StringProperty()
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class AssetInformationNode(StructuredNode):
    asset_kind = StringProperty()
    global_asset_id = StringProperty()
    specific_asset_id = ArrayProperty()
    asset_type = StringProperty()
    default_thumbnail = RelationshipTo('ResourceNode', 'default_thumbnail', cardinality=ZeroOrOne)


class ResourceNode(StructuredNode):
    path = StringProperty()
    content_type = StringProperty()


class DataSpecificationContentNode(StructuredNode):
    pass


class SubmodelNode(StructuredNode):
    id_ = StringProperty()
    submodel_element = RelationshipTo('SubmodelElementNode', 'submodel_element', cardinality=OneOrMore)
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    administration = RelationshipTo('AdministrativeInformationNode', 'administration', cardinality=ZeroOrOne)
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    kind = StringProperty()
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class SubmodelElementNode(StructuredNode):
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class DataSpecificationIEC61360Node(DataSpecificationContentNode):
    preferred_name = StringProperty()
    data_type = StringProperty()
    definition = StringProperty()
    short_name = StringProperty()
    unit = StringProperty()
    unit_id = RelationshipTo('ANYNode', 'unit_id', model=ReferenceRel, cardinality=ZeroOrOne)
    source_of_definition = StringProperty()
    symbol = StringProperty()
    value_format = StringProperty()
    value_list = ArrayProperty()
    value = StringProperty()
    level_types = ArrayProperty()


class AssetAdministrationShellNode(StructuredNode):
    asset_information = RelationshipTo('AssetInformationNode', 'asset_information', cardinality=One)
    id_ = StringProperty()
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    administration = RelationshipTo('AdministrativeInformationNode', 'administration', cardinality=ZeroOrOne)
    submodel = RelationshipTo('SubmodelNode', 'submodel', model=ModelReferenceRel, cardinality=ZeroOrMore)
    derived_from = RelationshipTo('AssetAdministrationShellNode', 'derived_from', model=ModelReferenceRel,
                                  cardinality=ZeroOrOne)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)


class ConceptDescriptionNode(StructuredNode):
    id_ = StringProperty()
    is_case_of = RelationshipTo('ANYNode', 'is_case_of', model=ReferenceRel, cardinality=ZeroOrMore)
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    administration = RelationshipTo('AdministrativeInformationNode', 'administration', cardinality=ZeroOrOne)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)


class DataElementNode(SubmodelElementNode):
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class PropertyNode(DataElementNode):
    id_short = StringProperty()
    value_type = StringProperty()
    value = StringProperty()
    value_id = RelationshipTo('ANYNode', 'value_id', model=ReferenceRel, cardinality=ZeroOrOne)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class MultiLanguagePropertyNode(DataElementNode):
    id_short = StringProperty()
    value = StringProperty()
    value_id = RelationshipTo('ANYNode', 'value_id', model=ReferenceRel, cardinality=ZeroOrOne)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class RangeNode(DataElementNode):
    id_short = StringProperty()
    value_type = StringProperty()
    min = StringProperty()
    max = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class BlobNode(DataElementNode):
    id_short = StringProperty()
    content_type = StringProperty()
    value = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class FileNode(DataElementNode):
    id_short = StringProperty()
    content_type = StringProperty()
    value = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class ReferenceElementNode(DataElementNode):
    id_short = StringProperty()
    value = RelationshipTo('ANYNode', 'value', model=ReferenceRel, cardinality=ZeroOrOne)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class SubmodelElementCollectionNode(SubmodelElementNode):
    id_short = StringProperty()
    value = RelationshipTo('SubmodelElementNode', 'value', cardinality=OneOrMore)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class SubmodelElementListNode(SubmodelElementNode):
    id_short = StringProperty()
    type_value_list_element = StringProperty()
    value = RelationshipTo('_SENode', 'value', cardinality=OneOrMore)
    semantic_id_list_element = RelationshipTo('ANYNode', 'semantic_id_list_element', model=ReferenceRel,
                                              cardinality=ZeroOrOne)
    value_type_list_element = StringProperty()
    order_relevant = BooleanProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class RelationshipElementNode(SubmodelElementNode):
    id_short = StringProperty()
    first = RelationshipTo('ANYNode', 'first', model=ReferenceRel, cardinality=One)
    second = RelationshipTo('ANYNode', 'second', model=ReferenceRel, cardinality=One)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class AnnotatedRelationshipElementNode(RelationshipElementNode):
    id_short = StringProperty()
    first = RelationshipTo('ANYNode', 'first', model=ReferenceRel, cardinality=One)
    second = RelationshipTo('ANYNode', 'second', model=ReferenceRel, cardinality=One)
    display_name = StringProperty()
    annotation = RelationshipTo('DataElementNode', 'annotation', cardinality=OneOrMore)
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class OperationNode(SubmodelElementNode):
    id_short = StringProperty()
    input_variable = RelationshipTo('SubmodelElementNode', 'input_variable', cardinality=OneOrMore)
    output_variable = RelationshipTo('SubmodelElementNode', 'output_variable', cardinality=OneOrMore)
    in_output_variable = RelationshipTo('SubmodelElementNode', 'in_output_variable', cardinality=OneOrMore)
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class CapabilityNode(SubmodelElementNode):
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class EntityNode(SubmodelElementNode):
    id_short = StringProperty()
    entity_type = StringProperty()
    statement = RelationshipTo('SubmodelElementNode', 'statement', cardinality=OneOrMore)
    global_asset_id = StringProperty()
    specific_asset_id = ArrayProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class EventElementNode(SubmodelElementNode):
    id_short = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class BasicEventElementNode(EventElementNode):
    id_short = StringProperty()
    observed = RelationshipTo('UnionNode', 'observed', model=ModelReferenceRel, cardinality=One)
    direction = StringProperty()
    state = StringProperty()
    message_topic = StringProperty()
    message_broker = RelationshipTo('UnionNode', 'message_broker', model=ModelReferenceRel, cardinality=ZeroOrOne)
    last_update = DateTimeProperty()
    min_interval = StringProperty()
    max_interval = StringProperty()
    display_name = StringProperty()
    category = StringProperty()
    description = StringProperty()
    semantic_id = RelationshipTo('ANYNode', 'semantic_id', model=ReferenceRel, cardinality=ZeroOrOne)
    qualifier = RelationshipTo('QualifierNode', 'qualifier', cardinality=OneOrMore)
    extension = RelationshipTo('ExtensionNode', 'extension', cardinality=OneOrMore)
    supplemental_semantic_id = RelationshipTo('ANYNode', 'supplemental_semantic_id', model=ReferenceRel,
                                              cardinality=OneOrMore)
    embedded_data_specifications = RelationshipTo('EmbeddedDataSpecificationNode', 'embedded_data_specifications',
                                                  cardinality=OneOrMore)


class ANYNode(StructuredNode):
    name = StringProperty()
