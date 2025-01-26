import logging
from enum import Enum
from typing import Iterable, Dict, List, Tuple

from basyx.aas import model
from basyx.aas.adapter.json import read_aas_json_file
import neo4j

from aas_mapping.settings import ATTRS_TO_IGNORE, NODE_TYPES, RELATIONSHIP_TYPES
from aas_mapping.util_type import isIterable, get_all_parent_classes
from aas_mapping.utils import gen_unique_obj_name, rm_quotes, add_quotes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AASToNeo4j:
    START_LINE = "CREATE (root:RootNode {title:'EmptyNode'})\n"

    def __init__(self, obj_store: model.DictObjectStore):
        self.obj_store = obj_store
        self.clauses = self.START_LINE
        self.objs_nodes: Dict[str, model.Identifiable] = {}
        self.global_rels: List[Tuple[str, str, model.Identifiable]] = []
        self.unresolved_global_rels: List[Tuple[str, str, model.Reference]] = []
        self.gen_cypher_clauses_for_all_objs()
        self.gen_global_relationship_clauses()
        self.gen_unresolved_global_relationship_clauses()

    def get_node_id(self, obj: model.Identifiable) -> str:
        """Get the unique node ID for a given object."""
        return next(key for key, value in self.objs_nodes.items() if value is obj)

    def execute_clauses(self, driver: neo4j.Driver):
        """Execute the generated Cypher clauses in the Neo4j database."""
        with driver.session() as session:
            result = session.run(self.clauses)
            for record in result:
                logger.info(record)

    def save_clauses_to_file(self, file_name: str):
        """Save the generated Cypher clauses to a file."""
        with open(file_name, 'w', encoding='utf8') as f:
            f.write(self.clauses)

    @classmethod
    def read_aas_json_file(cls, file_path: str) -> 'AASToNeo4j':
        """Read an AAS JSON file and return an instance of AASToNeo4j."""
        with open(file_path, 'r', encoding='utf8') as f:
            obj_store = read_aas_json_file(f)
        return cls(obj_store)

    def gen_cypher_clauses_for_all_objs(self):
        """Generate Cypher clauses for all objects in the object store."""
        for obj in self.obj_store:
            self.clauses += self.gen_clauses_for_obj(obj)

    def gen_clauses_for_obj(self, obj: model.Identifiable) -> str:
        """Generate Cypher clauses for a single object."""
        clauses = ""
        local_rels: List[Tuple[str, model.Identifiable]] = []
        kwargs: Dict[str, any] = {}

        variable_name = gen_unique_obj_name(obj)
        if variable_name in self.objs_nodes:
            raise ValueError(f"Duplicate object name: {variable_name}")

        if not isinstance(obj, NODE_TYPES):
            return clauses

        for attr, value in obj.__dict__.items():
            attr = attr.strip('_')
            attr = "id_" if attr == "id" else attr

            if attr in ATTRS_TO_IGNORE or value is None or value == "":
                continue

            original_value = value
            if not isIterable(value):
                value = [value]

            if len(value) > 0:
                first_value = next(iter(value))
                if isinstance(first_value, NODE_TYPES):
                    for item in value:
                        clauses += self.gen_clauses_for_obj(item)
                        local_rels.append((attr, item))
                elif isinstance(first_value, RELATIONSHIP_TYPES):
                    for item in value:
                        self.shelve_global_relationship(variable_name, item, attr)
                else:
                    kwargs[attr] = original_value

        obj_parent_classes = get_all_parent_classes(obj)
        clauses += self.create_node_cmd(variable_name, obj_parent_classes, kwargs)
        self.objs_nodes[variable_name] = obj

        for rel in local_rels:
            clauses += self.create_relationship_cmd(variable_name, rel[0], self.get_node_id(rel[1]))

        clauses += "\n"
        return clauses

    def create_node_cmd(self, node_name: str, node_types: Iterable[str], properties: Dict[str, any]) -> str:
        """Generate a Cypher command to create a node."""
        kwargs_repr = self._repr_kwargs(properties)
        return f"CREATE ({node_name}:{':'.join(node_types)} {{{kwargs_repr}}})\n"

    def create_relationship_cmd(self, source_node: str, rel_type: str, target_node: str) -> str:
        """Generate a Cypher command to create a relationship."""
        return f"CREATE ({source_node})-[:{rel_type}]->({target_node})\n"

    def _repr_kwarg(self, key: str, value: any) -> str:
        """Generate a string representation of a key-value pair for Cypher."""
        if isinstance(value, str):
            value_repr = add_quotes(rm_quotes(value))
        elif isinstance(value, (bool, int, float)):
            value_repr = str(value)
        elif isinstance(value, Enum):
            value_repr = add_quotes(value.name)
        elif isinstance(value, type):
            value_repr = add_quotes(value.__name__)
        elif isinstance(value, model.datatypes.Date):
            value_repr = f"date('{value}')"
        # elif isinstance(value, datetime.datetime):
        #     value_repr = f"datetime('{value}')"
        elif isinstance(value, model.LangStringSet):
            lang_strs = ", ".join([add_quotes(f"{lang}: {rm_quotes(val)}") for lang, val in value.items()])
            value_repr = f"[{lang_strs}]"
        elif isinstance(value, (list, set)):
            value_repr = f"[{', '.join([rm_quotes(str(v)) for v in value])}]"
        else:
            raise ValueError(f"Unsupported type: {type(value)}")
        return f"{key}:{value_repr}"

    def _repr_kwargs(self, kwargs: Dict[str, any]) -> str:
        """Generate a string representation of a dictionary for Cypher."""
        kwarg_reprs = []
        for key, value in kwargs.items():
            try:
                kwarg_reprs.append(self._repr_kwarg(key, value))
            except ValueError as e:
                logger.warning(f"Skipping {key}: {e}")
        return ', '.join(kwarg_reprs)

    def shelve_global_relationship(self, source_key: str, rel_obj: model.Reference, label: str):
        """Store global relationships for later processing."""
        if not isinstance(rel_obj, RELATIONSHIP_TYPES):
            raise ValueError(f"Unsupported relationship type: {type(rel_obj)}")

        target_obj = None
        if isinstance(rel_obj, model.ModelReference):
            try:
                target_obj = rel_obj.resolve(self.obj_store)
            except KeyError:
                pass
        elif isinstance(rel_obj, model.Reference):
            try:
                target_obj = self.obj_store.get_identifiable(rel_obj.key[0].value)
            except KeyError:
                pass
        else:
            raise ValueError(f"Unsupported relationship type: {type(rel_obj)}")

        if target_obj is None:
            self.unresolved_global_rels.append((source_key, label, rel_obj))
        else:
            self.global_rels.append((source_key, label, target_obj))

    def gen_global_relationship_clauses(self):
        """Generate Cypher clauses for global relationships."""
        for source_key, rel_type, target_obj in self.global_rels:
            target_node = self.get_node_id(target_obj)
            self.clauses += self.create_relationship_cmd(source_key, rel_type, target_node)

    def gen_unresolved_global_relationship_clauses(self):
        """Generate Cypher clauses for unresolved global relationships."""
        for source_key, rel_type, rel_obj in self.unresolved_global_rels:
            unresolved_rel_node_name = gen_unique_obj_name(rel_obj, prefix="UnresolvedRelationship")
            unresolved_rel_node_types = get_all_parent_classes(rel_obj)
            unresolved_rel_node_types.append("UnresolvedRelationship")

            last_key = rel_obj.key[-1]
            properties = {
                "type": last_key.type,
                "value": last_key.value
            }
            self.clauses += self.create_node_cmd(unresolved_rel_node_name, unresolved_rel_node_types, properties)
            self.clauses += self.create_relationship_cmd(source_key, rel_type, unresolved_rel_node_name)


def main():
    def remove_all(neo4j_driver: neo4j.Driver):
        """Remove all nodes and relationships from the Neo4j database."""
        with neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    neo4j_driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    remove_all(neo4j_driver)

    # # iterate over all json files in submodel folder
    # for root, dirs, files in os.walk("submodels"):
    #     for file in files:
    #         if file.endswith(".json"):
    #             print(f"Processing {file}")
    #             translator = AASToNeo4j.read_aas_json_file(os.path.join(root, file))
    #             translator.execute_clauses(neo4j_driver)
    #

    translator = AASToNeo4j.read_aas_json_file("example.json")
    translator.execute_clauses(neo4j_driver)


if __name__ == '__main__':
    main()
