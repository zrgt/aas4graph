import logging
import re
import uuid
from typing import Iterable, Dict, List, Tuple, Optional, Set
import neo4j
import json

from aas_mapping.util_type import isIterable, get_aas_class, get_all_parent_classes_of_cls
from aas_mapping.utils import add_quotes

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CypherClause = str

KEYS_TO_IGNORE = tuple()
IDENTIFIABLE_KEYS = ("assetAdministrationShells", "submodels", "conceptDescriptions")
IDENTIFIABLES = ("AssetAdministrationShell", "Submodel", "ConceptDescription")

SPECIFIC_RELATIONSHIPS = ("child", "references")


def identify_types(obj: Dict) -> List[str]:
    RELATIONSHIP_TYPES = ("ExternalReference", "ModelReference")
    QUALIFIER_KINDS = ("ValueQualifier", "ConceptQualifier", "TemplateQualifier")

    """Identify the type of an object."""
    if "modelType" in obj:
        typ = obj["modelType"]
        basyx_typ = get_aas_class(typ)
        types = get_all_parent_classes_of_cls(basyx_typ)
        return types
    elif "type" in obj and obj["type"] in RELATIONSHIP_TYPES:
        return ["Reference", obj["type"]]
    elif "kind" in obj and obj["kind"] in QUALIFIER_KINDS:
        return ["Qualifier", obj["kind"]]
    elif "language" in obj and "text" in obj:
        return ["LangString"]
    else:
        return ["Unknown"]


def save_clauses_to_file(file_name: str, clauses: CypherClause):
    """Save the generated Cypher clauses to a file."""
    with open(file_name, 'w', encoding='utf8') as file:
        file.write(clauses)


class AASJSONToNeo4j:
    # TODO: Implement the following methods/parameters:
    # - method: get_referable_as_json

    DEFAULT_OPTIMIZATION_CLAUSES = [
        "CREATE INDEX FOR (r:Identifiable) ON (r.id);",
        "CREATE INDEX FOR (r:Referable) ON (r.idShort);",
        "CREATE INDEX FOR (r:Referable) ON (r.index);",  # For Referables in SubmodelElementLists
    ]
    node_names: Set[str] = set()

    def __init__(self, uri=None, user=None, password=None):
        if uri:
            self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None

    def execute_clauses(self, clauses: CypherClause):
        """Execute the generated Cypher clauses in the Neo4j database. After execution, the clauses are cleared."""
        with self.driver.session() as session:
            result = session.run(clauses)
            for record in result:
                logger.info(record)
            return result

    @staticmethod
    def read_file_and_create_clauses(file_path: str) -> CypherClause:
        with open(file_path, 'r') as file:
            aas_json = json.load(file)
        return AASJSONToNeo4j.create_clauses_for_aas_json(aas_json)

    @staticmethod
    def create_clauses_for_aas_json(aas_json: Dict) -> CypherClause:
        clauses = ""
        for i in IDENTIFIABLE_KEYS:
            try:
                for obj in aas_json[i]:
                    node, obj_clauses, node_labels = AASJSONToNeo4j._create_clauses_for_obj(obj)
                    clauses += obj_clauses
            except KeyError:
                logger.warning(f"Key '{i}' not found in the JSON file")
        return clauses

    @staticmethod
    def _create_clauses_for_obj(obj: Dict, node_properties: Dict[str, any] = None) -> Tuple[str, str, List[str]]:
        clauses = ""
        node_name = AASJSONToNeo4j._gen_unique_node_name(obj)
        node_labels = identify_types(obj)
        node_properties: Dict[str, any] = node_properties or {}
        node_rels: List[Tuple[str, str]] = []  # Relationship type and target node

        for key, value in obj.items():
            if key in KEYS_TO_IGNORE:
                continue
            elif key == "keys" and "Reference" in node_labels:
                # Reference keys are stored in a list
                node_properties["keys_type"] = [i["type"] for i in value]
                node_properties["keys_value"] = [i["value"] for i in value]
                continue
            elif isinstance(value, dict):
                child_node_name, child_clauses, child_node_labels = AASJSONToNeo4j._create_clauses_for_obj(value)
                clauses += child_clauses
                if "Referable" in child_node_labels:
                    node_rels.append(("child", child_node_name))
                node_rels.append((key, child_node_name))
            elif isIterable(value):
                # List of objects
                for i, item in enumerate(value, start=0):
                    # Add index to the properties of the internal SubmodelElement
                    child_node_name, child_clauses, child_node_labels = AASJSONToNeo4j._create_clauses_for_obj(item, {
                        "index": i})
                    clauses += child_clauses
                    if "Referable" in child_node_labels:
                        node_rels.append(("child", child_node_name))
                    node_rels.append((key, child_node_name))
            else:
                node_properties[key] = value
                continue

        clauses += AASJSONToNeo4j._create_node_clause(node_name, node_labels, node_properties)
        for rel_type, child_node_name in node_rels:
            clauses += AASJSONToNeo4j._create_relationship_clause(node_name, rel_type, child_node_name)

        return node_name, clauses, node_labels

    @staticmethod
    def _create_node_clause(node_name: str, node_labels: Iterable[str], properties: Dict[str, any]) -> str:
        """Generate a Cypher command to create a node."""
        # kwargs_repr = ', '.join([f"{key}: {add_quotes(value)}" for key, value in properties.items()])
        kwargs_repr = ""
        for key, value in properties.items():
            if isinstance(value, list):
                kwargs_repr += f"{key}: {value}, "
            elif isinstance(value, int):
                kwargs_repr += f"{key}: {value}, "
            else:
                kwargs_repr += f"{key}: {add_quotes(value)}, "
        kwargs_repr = kwargs_repr.rstrip(", ")
        return f"CREATE ({node_name}:{':'.join(node_labels)} {{{kwargs_repr}}})\n"

    @staticmethod
    def _create_relationship_clause(source_node: str, rel_type: str, target_node: str) -> str:
        """Generate a Cypher command to create a relationship."""
        return f"CREATE ({source_node})-[:{rel_type}]->({target_node})\n"

    @staticmethod
    def _gen_unique_node_name(obj, prefix: str = None):
        for _ in range(5):
            if prefix:
                unique_obj_name = prefix + uuid.uuid4().hex[:6]
            else:
                unique_obj_name = obj.__class__.__name__.lower() + uuid.uuid4().hex[:6]
            logger.info(f"Generated unique object name: {unique_obj_name}")

            if unique_obj_name not in AASJSONToNeo4j.node_names:
                AASJSONToNeo4j.node_names.add(unique_obj_name)
                return unique_obj_name

            logger.warning(f"Duplicate object name: {unique_obj_name}")
        else:
            raise ValueError("Could not generate unique object name")

    @staticmethod
    def itemize_idShortPath(idShortPath: str) -> List[str]:
        """
        Split the idShortPath into a list of idShorts. Dot separated or brackets with index.
        :param idShortPath: The path to the idShort attribute.
        """
        # Example "MySubmodelElementCollection.MySubSubmodelElementList2[0][0].MySubTestValue3"
        # Result: ["MySubmodelElementCollection", "MySubSubmodelElementList2", 0, 0, "MySubTestValue3"]
        pattern = r'([a-zA-Z_]\w*)|\[(\d+)\]'
        matches = re.findall(pattern, idShortPath)
        result = [match[0] if match[0] else int(match[1]) for match in matches]
        return result

    @staticmethod
    def create_clause_to_find_node(parent_id: str, idShortPath: str = None) -> Optional[str]:
        """
        Find the parent node of a SubmodelElement object.
        :param parent_id: The ID of the parent node. (e.g. Submodel, AssetAdministrationShell, ConceptDescription)
        :param idShortPath: The path to the idShort attribute.
        """
        if not idShortPath:
            return f"MATCH (the_node:Identifiable {{id: '{parent_id}'}})\n"

        clause = f"MATCH (parent:Identifiable {{id: '{parent_id}'}})"
        idShorts = AASJSONToNeo4j.itemize_idShortPath(idShortPath)
        for i, idShort in enumerate(idShorts):
            if not i == len(idShorts) - 1:
                clause += f"-[:child]->(child_{i} {{idShort: '{idShort}'}})\n"
            else:
                clause += f"-[:child]->(the_node {{idShort: '{idShort}'}})\n"
        return clause

    @staticmethod
    def convert_referable_subgraph_to_dict(subgraph):
        # Create a helper function to convert nodes into dictionaries
        def convert_node(node):
            # Extract the node properties
            node_dict = {key: value for key, value in node['properties'].items()}
            return node_dict

        # Create a helper function to recursively add related nodes based on relationships
        def add_relationships(node, node_dict, relationships):
            for rel in relationships:
                if rel['start']['id'] == node['id']:
                    rel_type = rel['label']
                    if rel_type in SPECIFIC_RELATIONSHIPS:
                        continue
                    related_node = next(n for n in subgraph['nodes'] if n['id'] == rel['end']['id'])
                    related_node_dict = convert_node(related_node)

                    if "index" in related_node['properties']:
                        if rel_type not in node_dict:
                            node_dict[rel_type] = []
                        node_dict[rel_type].append(related_node_dict)
                    else:
                        node_dict[rel_type] = related_node_dict

                    # Recursively process the related node if it has outgoing relationships
                    add_relationships(related_node, related_node_dict,
                                      [r for r in subgraph['relationships'] if r['start']['id'] == related_node['id']])

                    # Sort list entries by index in the dictionary and remove the index key
                    for key, value in node_dict.items():
                        if isinstance(value, list):
                            node_dict[key] = sorted(value, key=lambda x: x.get('index', 0))
                            for item in node_dict[key]:
                                if 'index' in item:
                                    del item['index']

                    if "keys_value" in related_node_dict and "keys_type" in related_node_dict:
                        related_node_dict["keys"] = [{"type": t, "value": v} for t, v in
                                                     zip(related_node_dict.pop("keys_type"),
                                                         related_node_dict.pop("keys_value"))]

        # The root node (Assuming it's the first node in the 'nodes' list)
        root_node = subgraph['nodes'][0]
        root_node_dict = convert_node(root_node)

        # Add the outgoing relationships for the root node
        add_relationships(root_node, root_node_dict,
                          [r for r in subgraph['relationships'] if r['start']['id'] == root_node['id']])

        return root_node_dict


class AASCypherClauseGenerator(AASJSONToNeo4j):

    # TODO: Implement the following methods/parameters:
    # - param: overwrite_existing: bool = False (smth like PATCH)

    def add_referable(self, obj: Dict, parentId: str = None, idShortPath: str = None):
        """
        Create and run a Cypher clause to add a Referable object.
        """
        clauses = self._add_referable(obj, parentId, idShortPath)
        return self.execute_clauses(clauses)

    def _add_referable(self, obj: Dict, parentId: str = None, idShortPath: str = None) -> CypherClause:
        """
        Create a Cypher clause to add a Referable object.
        :param obj: The Referable object.
        :param parentId: The ID of the parent node. (e.g. Submodel, AssetAdministrationShell, ConceptDescription)
        :param idShortPath: The path to the idShort attribute.
        """
        node_labels = identify_types(obj)
        if parentId and idShortPath and "Identifiable" not in node_labels:
            return self.add_submodel_element(self, obj, parentId, idShortPath)
        elif not parentId and not idShortPath and "Identifiable" in node_labels:
            return self.add_identifiable(self, obj)
        else:
            raise ValueError(f"Invalid combination of arguments. "
                             f"Please provide either parentId and idShortPath or none, if the object is an Identifiable."
                             f"Provided arguments: parentId={parentId}, idShortPath={idShortPath}, node_labels={node_labels}")

    def add_submodel_element(self, obj: Dict, parentId: str, idShortPath: str):
        """
        Create and run a Cypher clause to add a SubmodelElement object.
        """
        clauses = self._add_submodel_element(obj, parentId, idShortPath)
        return self.execute_clauses(clauses)

    def _add_submodel_element(self, obj: Dict, parentId: str, idShortPath: str) -> CypherClause:
        """
        Create a Cypher clause for a SubmodelElement object.
        :param obj: The SubmodelElement object.
        :param parentId: The ID of the parent node. (e.g. Submodel, AssetAdministrationShell, ConceptDescription)
        :param idShortPath: The path to the idShort attribute.
        """
        clauses = self.create_clause_to_find_node(parentId, idShortPath)
        node_name, obj_clauses, node_labels = self._create_clauses_for_obj(obj)
        clauses += obj_clauses
        clauses += self._create_relationship_clause("the_node", "child", node_name)
        clauses += self._create_relationship_clause("the_node", "value", node_name)
        return clauses

    def add_identifiable(self, obj: Dict):
        """
        Create and run a Cypher clause to add an Identifiable object.
        """
        clauses = self._add_identifiable(obj)
        return self.execute_clauses(clauses)

    def _add_identifiable(self, obj: Dict) -> CypherClause:
        """
        Create a Cypher clause for an Identifiable object.
        :param obj: The Identifiable object.
        """
        node_labels = identify_types(obj)
        if "Identifiable" not in node_labels:
            raise ValueError(f"Object is not an Identifiable. Provided node_labels: {node_labels}")
        node_name, clauses, node_labels = self._create_clauses_for_obj(obj)
        return clauses

    def remove_referable(self, parentId: str = None, idShortPath: str = None):
        """
        Create and run a Cypher clause to remove a Referable object.
        """
        clauses = self._remove_referable(parentId, idShortPath)
        return self.execute_clauses(clauses)

    def _remove_referable(self, parentId: str = None, idShortPath: str = None) -> CypherClause:
        """
        Create a Cypher clause to remove a Referable object.
        :param parentId: The ID of the parent node. (e.g. Submodel, AssetAdministrationShell, ConceptDescription)
        :param idShortPath: The path to the idShort attribute.
        """
        if not parentId or not idShortPath:
            raise ValueError("Both parent_id and id_short_path must be provided.")

        clauses = self.create_clause_to_find_node(parentId, idShortPath)
        delete_clause = (
            "CALL apoc.path.subgraphAll(the_node, {relationshipFilter: '>'}) YIELD nodes "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "UNWIND nodes AS node "
            "DETACH DELETE node;"
        )
        return clauses + delete_clause

    def get_referable(self, parentId: str, idShortPath: str):
        """
        Create and run a Cypher clause to get a Referable object.
        """
        clauses = self._get_subgraph_of_referable(parentId, idShortPath)

        with self.driver.session() as session:
            result = session.run(clauses).single()
            subgraph_json = json.loads(result["json"]) if result else {}
        return self.convert_referable_subgraph_to_dict(subgraph_json)

    def _get_subgraph_of_referable(self, parentId: str, idShortPath: str = None) -> CypherClause:
        """
        Fetches a subgraph of Referable object from Neo4j.

        It includes the object node itself and all its children being attributes of the object.
        """
        find_node_clause = self.create_clause_to_find_node(parentId, idShortPath)
        get_subgraph_clause = (
            "CALL apoc.path.subgraphAll(the_node, {relationshipFilter: '>'}) YIELD nodes, relationships "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "RETURN apoc.convert.toJson({nodes: nodes, relationships: relationships}) AS json;"
        )
        return find_node_clause + get_subgraph_clause



neo4j_driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
translator = AASJSONToNeo4j(uri="bolt://localhost:7687", user="neo4j", password="password")
clause_generator = AASCypherClauseGenerator()


def remove_all():
    """Remove all nodes and relationships from the Neo4j database."""
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


def upload_file():
    """Upload a JSON file to the Neo4j database."""
    remove_all()
    clauses = translator.read_file_and_create_clauses(
        r"C:\Users\igor\PycharmProjects\aas4graph\aas_mapping\submodels\IDTA 02006-2-0_Template_Digital Nameplate_light.json")
    save_clauses_to_file("aasjson.cypher", clauses)
    translator.execute_clauses(clauses)


def main():
    parentid = "https://admin-shell.io/idta/SubmodelTemplate/DigitalNameplate/2/0"
    idShortPath = "ContactInformation.Phone"
    obj = {
        "idShort": "Company",
        "semanticId": {
            "type": "ExternalReference",
            "keys": [
                {
                    "type": "GlobalReference",
                    "value": "0173-1#02-AAW001#001"
                }
            ]
        },
        "qualifiers": [
            {
                "kind": "ConceptQualifier",
                "type": "Multiplicity",
                "valueType": "xs:string",
                "value": "ZeroToOne"
            }
        ],
        "value": [
            {
                "language": "en",
                "text": "ABC Company"
            }
        ],
        "modelType": "MultiLanguageProperty"
    }
    remove_all()
    upload_file()
    clauses = clause_generator.add_submodel_element(obj, parentid, idShortPath)
    print(clauses)
    clauses = clause_generator.remove_referable(parentid, idShortPath)
    print(clauses)
    translator.get_referable("Email")


if __name__ == '__main__':
    main()
