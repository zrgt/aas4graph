import logging
import re
import uuid
from typing import Iterable, Dict, List, Tuple, Optional, Set
import neo4j
import json

from aas_mapping.utils import add_quotes, is_iterable

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CypherClause = str

KEYS_TO_IGNORE = tuple()
IDENTIFIABLE_KEYS = ("assetAdministrationShells", "submodels", "conceptDescriptions")
IDENTIFIABLES = ("AssetAdministrationShell", "Submodel", "ConceptDescription")
SPECIFIC_RELATIONSHIPS = ("child", "references")


class AASNeo4JClient:
    DEFAULT_OPTIMIZATION_CLAUSES = [
        "CREATE INDEX FOR (r:Identifiable) ON (r.id);",
        "CREATE INDEX FOR (r:Referable) ON (r.idShort);",
        "CREATE INDEX FOR (r:Referable) ON (r.index);",  # For Referables in SubmodelElementLists
    ]
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
    node_names: Set[str] = set()

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password)) if uri else None
        if self.driver:
            self.optimize_database()

    def optimize_database(self):
        """Optimize the Neo4j database by creating indexes for the Identifiable and Referable nodes."""
        for clause in self.DEFAULT_OPTIMIZATION_CLAUSES:
            self.execute_clause(clause)

    def execute_clause(self, clause: CypherClause):
        """Execute the generated Cypher clauses in the Neo4j database. After execution, the clauses are cleared."""
        with self.driver.session() as session:
            result = session.run(clause)
            for record in result:
                logger.info(record)
            return result

    def read_file_and_create_clause(self, file_path: str) -> CypherClause:
        with open(file_path, 'r') as file:
            aas_json = json.load(file)
        return self.create_clause_for_aas_json(aas_json)

    def create_clause_for_aas_json(self, aas_json: Dict) -> CypherClause:
        clauses = ""
        for key in IDENTIFIABLE_KEYS:
            try:
                for obj in aas_json[key]:
                    _, obj_clauses, _ = self._create_clause_for_obj(obj)
                    clauses += obj_clauses
            except KeyError:
                logger.warning(f"Key '{key}' not found in the JSON file")
        return clauses

    def remove_all(self):
        """Remove all nodes and relationships from the Neo4j database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def upload_aas_json(self, file_path: str):
        """Upload a JSON file to the Neo4j database."""
        clauses = self.read_file_and_create_clause(file_path)
        self.execute_clause(clauses)
        save_clauses_to_file("aasjson.cypher", clauses)

    def add_referable(self, obj: Dict, parent_id: Optional[str] = None, id_short_path: Optional[str] = None):
        clauses = self._add_referable_clause(obj, parent_id, id_short_path)
        return self.execute_clause(clauses)

    def add_submodel_element(self, obj: Dict, parent_id: str, id_short_path: str):
        clauses = self._add_submodel_element_clause(obj, parent_id, id_short_path)
        return self.execute_clause(clauses)

    def add_identifiable(self, obj: Dict):
        clauses = self._add_referable_clause(obj)
        return self.execute_clause(clauses)

    def remove_referable(self, parent_id: str, id_short_path: str):
        clauses = self._remove_referable_clause(parent_id, id_short_path)
        return self.execute_clause(clauses)

    def get_referable(self, parent_id: str, id_short_path: str) -> Dict:
        clauses = self._get_subgraph_of_referable_clause(parent_id, id_short_path)
        result = self.execute_clause(clauses).single()
        subgraph_json = json.loads(result["json"]) if result else {}
        return self._convert_referable_subgraph_to_dict(subgraph_json)

    @staticmethod
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

    def identify_types(self, obj: Dict) -> List[str]:
        """Return the types of the given object."""
        RELATIONSHIP_TYPES = ("ExternalReference", "ModelReference")
        QUALIFIER_KINDS = ("ValueQualifier", "ConceptQualifier", "TemplateQualifier")

        if "modelType" in obj:
            class_name = obj["modelType"]
            types = [class_name, *self.AAS_CLS_PARENTS[class_name]]
            return list(types)
        elif "type" in obj and obj["type"] in RELATIONSHIP_TYPES:
            return ["Reference", obj["type"]]
        elif "kind" in obj and obj["kind"] in QUALIFIER_KINDS:
            return ["Qualifier", obj["kind"]]
        elif "language" in obj and "text" in obj:
            return ["LangString"]
        else:
            return ["Unknown"]

    def _create_clause_for_obj(self, obj: Dict, node_properties: Optional[Dict[str, any]] = None) -> Tuple[str, str, list[str]]:
        clauses = ""
        node_name = self._gen_unique_node_name(obj)
        node_labels = self.identify_types(obj)
        node_properties = node_properties or {}
        node_rels: List[Tuple[str, str]] = []

        for key, value in obj.items():
            if key in KEYS_TO_IGNORE:
                continue
            elif key == "keys" and "Reference" in node_labels:
                node_properties["keys_type"] = [i["type"] for i in value]
                node_properties["keys_value"] = [i["value"] for i in value]
            elif isinstance(value, dict):
                child_node_name, child_clauses, child_node_labels = self._create_clause_for_obj(value)
                clauses += child_clauses
                if "Referable" in child_node_labels:
                    node_rels.append(("child", child_node_name))
                node_rels.append((key, child_node_name))
            elif is_iterable(value):
                for i, item in enumerate(value, start=0):
                    # Add index to the properties of the internal SubmodelElement
                    child_node_name, child_clauses, child_node_labels = self._create_clause_for_obj(item, {"index": i})
                    clauses += child_clauses
                    if "Referable" in child_node_labels:
                        node_rels.append(("child", child_node_name))
                    node_rels.append((key, child_node_name))
            else:
                node_properties[key] = value

        clauses += self._create_node_clause(node_name, node_labels, node_properties)
        for rel_type, child_node_name in node_rels:
            clauses += self._create_relationship_clause(node_name, rel_type, child_node_name)

        return node_name, clauses, node_labels

    def _gen_unique_node_name(self, obj: Dict, prefix: Optional[str] = None) -> str:
        for _ in range(5):
            unique_obj_name = (prefix or obj.__class__.__name__.lower()) + uuid.uuid4().hex[:6]
            logger.info(f"Generated unique object name: {unique_obj_name}")

            if unique_obj_name not in self.node_names:
                self.node_names.add(unique_obj_name)
                return unique_obj_name

            logger.warning(f"Duplicate object name: {unique_obj_name}")
        raise ValueError("Could not generate unique object name")

    @staticmethod
    def _create_node_clause(node_name: str, node_labels: Iterable[str], properties: Dict[str, any]) -> str:
        repr_as_is_types = (list, int)
        kwargs_repr = ", ".join(
            f"{key}: {value if isinstance(value, repr_as_is_types) else add_quotes(value)}"
            for key, value in properties.items()
        )
        return f"CREATE ({node_name}:{':'.join(node_labels)} {{{kwargs_repr}}})\n"

    @staticmethod
    def _create_relationship_clause(source_node: str, rel_type: str, target_node: str) -> str:
        return f"CREATE ({source_node})-[:{rel_type}]->({target_node})\n"

    def _find_node_clause(self, parent_id: str, id_short_path: Optional[str] = None) -> Optional[str]:
        if not id_short_path:
            return f"MATCH (the_node:Identifiable {{id: '{parent_id}'}})\n"

        clause = f"MATCH (parent:Identifiable {{id: '{parent_id}'}})"
        id_shorts = self.itemize_id_short_path(id_short_path)
        for i, idShort in enumerate(id_shorts):
            if not i == len(id_shorts) - 1:
                clause += f"-[:child]->(child_{i} {{idShort: '{idShort}'}})\n"
            else:
                clause += f"-[:child]->(the_node {{idShort: '{idShort}'}})\n"
        return clause

    def _convert_referable_subgraph_to_dict(self, subgraph: Dict) -> Dict:
        """Take a Neo4J subgraph of a Referable and convert it to a dictionary."""

        def convert_node(node: Dict) -> Dict:
            return {key: value for key, value in node['properties'].items()}

        def add_relationships(node: Dict, node_dict: Dict, relationships: List[Dict]):
            for rel in relationships:
                if rel['start']['id'] == node['id']:
                    rel_type = rel['label']
                    if rel_type in SPECIFIC_RELATIONSHIPS:
                        continue
                    related_node = next(n for n in subgraph['nodes'] if n['id'] == rel['end']['id'])
                    related_node_dict = convert_node(related_node)

                    if "index" in related_node['properties']:
                        node_dict.setdefault(rel_type, []).append(related_node_dict)
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
                                item.pop('index', None)

                    if "keys_value" in related_node_dict and "keys_type" in related_node_dict:
                        related_node_dict["keys"] = [{"type": t, "value": v} for t, v in zip(related_node_dict.pop("keys_type"), related_node_dict.pop("keys_value"))]

        root_node = subgraph['nodes'][0]
        root_node_dict = convert_node(root_node)
        add_relationships(root_node, root_node_dict,
                          [r for r in subgraph['relationships'] if r['start']['id'] == root_node['id']])
        return root_node_dict

    def _add_referable_clause(self, obj: Dict, parent_id: Optional[str] = None, id_short_path: Optional[str] = None) -> CypherClause:
        node_labels = self.identify_types(obj)
        if "Identifiable" in node_labels:
            if parent_id or id_short_path:
                raise ValueError("Parent ID or ID short path should not be provided for Identifiable objects")
            _, clauses, _ = self._create_clause_for_obj(obj)
        else:
            if not (parent_id and id_short_path):
                raise ValueError("Parent ID and ID short path should be provided for Referable objects")
            clauses = self._add_submodel_element_clause(obj, parent_id, id_short_path)
        return clauses

    def _add_submodel_element_clause(self, obj: Dict, parent_id: str, id_short_path: str) -> CypherClause:
        clauses = self._find_node_clause(parent_id, id_short_path)
        node_name, obj_clauses, _ = self._create_clause_for_obj(obj)
        clauses += obj_clauses
        clauses += self._create_relationship_clause("the_node", "child", node_name)
        clauses += self._create_relationship_clause("the_node", "value", node_name)
        return clauses

    def _remove_referable_clause(self, parent_id: str, id_short_path: str) -> CypherClause:
        clauses = self._find_node_clause(parent_id, id_short_path)
        delete_clause = (
            "CALL apoc.path.subgraphAll(the_node, {relationshipFilter: '>'}) YIELD nodes "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "UNWIND nodes AS node "
            "DETACH DELETE node;"
        )
        return clauses + delete_clause

    def _get_subgraph_of_referable_clause(self, parent_id: str, id_short_path: Optional[str] = None) -> CypherClause:
        """
        Fetches a subgraph of Referable object from Neo4j.

        It includes the object node itself and all its children being attributes of the object.
        """
        find_node_clause = self._find_node_clause(parent_id, id_short_path)
        get_subgraph_clause = (
            "CALL apoc.path.subgraphAll(the_node, {relationshipFilter: '>'}) YIELD nodes, relationships "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "RETURN apoc.convert.toJson({nodes: nodes, relationships: relationships}) AS json;"
        )
        return find_node_clause + get_subgraph_clause


def save_clauses_to_file(file_name: str, clauses: CypherClause):
    """Save the generated Cypher clauses to a file."""
    with open(file_name, 'w', encoding='utf8') as file:
        file.write(clauses)


def main():
    aas_neo4j_client = AASNeo4JClient(uri="bolt://localhost:7687", user="neo4j", password="password")
    aas_neo4j_client.remove_all()
    aas_neo4j_client.upload_aas_json("submodels/IDTA 02006-2-0_Template_Digital Nameplate.json")

    parent_id = "https://admin-shell.io/idta/SubmodelTemplate/DigitalNameplate/2/0"
    id_short_path = "ContactInformation.Phone"
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

    result = aas_neo4j_client.add_submodel_element(obj, parent_id, id_short_path)
    print(result)
    result = aas_neo4j_client.get_referable(parent_id, id_short_path)
    print(result)
    result = aas_neo4j_client.remove_referable(parent_id, id_short_path)
    print(result)


if __name__ == '__main__':
    main()
