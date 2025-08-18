import logging
import os
import time
from dataclasses import dataclass
from os.path import isfile, join
from typing import Dict, List, Tuple, Optional, Set, Any
import neo4j
import json

from neo4j import Driver

from aas_mapping import aas_utils
from aas_mapping.aas_utils import IDENTIFIABLE_KEYS

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CypherClause = str

KEYS_TO_IGNORE = tuple()
SPECIFIC_RELATIONSHIPS = ("child", "references")


@dataclass
class AASUploadStats:
    overall_start_time: float
    total_files: int = 0
    total_batches: int = 0
    batch_size: int = 0
    total_nodes_created: int = 0
    total_relationships_created: int = 0
    total_time: float = 0.0
    total_processing_time: float = 0.0
    total_node_creation_time: float = 0.0
    total_relationship_creation_time: float = 0.0

    def __init__(self):
        super().__init__()
        self.overall_start_time = time.time()

    def finish(self):
        self.total_time = time.time() - self.overall_start_time
        logger.info(f"Total processing time: {self.total_time:.2f} seconds")
        logger.info(f"Total nodes created: {self.total_nodes_created}")
        logger.info(f"Total relationships created: {self.total_relationships_created}")
        logger.info(f"Total batches processed: {self.total_batches}")
        logger.info(f"Total files processed: {self.total_files}")
        logger.info(f"Total processing time: {self.total_processing_time:.2f} seconds")
        logger.info(f"Total node creation time: {self.total_node_creation_time:.2f} seconds")
        logger.info(f"Total relationship creation time: {self.total_relationship_creation_time:.2f} seconds")


class BaseNeo4JClient:
    driver: Driver

    def execute_clause(self, clause: CypherClause, single: bool = False):
        """Execute the generated Cypher clauses in the Neo4j database. After execution, the clauses are cleared."""
        with self.driver.session() as session:
            if single:
                result = session.run(clause).single() if single else session.run(clause)
            else:
                result = session.run(clause)
                if result:
                    result = [record for record in result]
            return result

    def _remove_all(self, batch_size: int = 10000):
        """Remove all nodes and relationships from the Neo4j database."""
        with self.driver.session() as session:
            while True:
                # Query to find and detach/delete a limited number of nodes
                # We use a subquery to ensure the count is done correctly before the delete
                # and to handle the large number of nodes more efficiently.
                result = session.run("""
                    MATCH (n)
                    WITH n LIMIT $batch_size
                    DETACH DELETE n
                    RETURN count(n) AS nodes_deleted
                """, batch_size=batch_size)

                nodes_deleted = result.single()["nodes_deleted"]

                # Log the progress
                logger.info(f"Deleted {nodes_deleted} nodes.")

                # If the number of nodes deleted is less than the batch size,
                # it means we have reached the end of the database.
                if nodes_deleted < batch_size:
                    break

    def save_clauses_to_file(file_name: str, clauses: CypherClause):
        """Save the generated Cypher clauses to a file."""
        with open(file_name, 'w', encoding='utf8') as file:
            file.write(clauses)


class AASUploaderInNeo4J(BaseNeo4JClient):
    DEFAULT_OPTIMIZATION_CLAUSES = [
        "CREATE INDEX FOR (r:Identifiable) ON (r.id);",
        "CREATE INDEX FOR (r:Referable) ON (r.idShort);",
        "CREATE INDEX FOR (r:Referable) ON (r.index);",  # For Referables in SubmodelElementLists
    ]

    # Attributes of objects that are lists of dictionaries and should be converted to multiple lists with simple values
    COMPLEX_VALUE_LIST_AS_MULTIPLE_SIMPLE_VALUE_LISTS = {
        "DataSpecificationIec61360": ["preferredName", "shortName", "definition"],
        "Reference": ["keys"],
        # "Qualifiable": ["qualifiers"], The problem is that qualifier can have a SemanticId
        "Referable": ["description", "displayName"],
    }

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password)) if uri else None
        if self.driver:
            self.optimize_database()
        self.uid_counter = 0

    def optimize_database(self):
        """Optimize the Neo4j database by creating indexes for the Identifiable and Referable nodes."""
        for clause in self.DEFAULT_OPTIMIZATION_CLAUSES:
            try:
                self.execute_clause(clause, single=True)
            except neo4j.exceptions.ClientError as e:
                if e.code == "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                    logger.info(f"Index already exists: {clause}")

    def _get_props_to_model_as_multiple_lists(self, node_labels: List[str]) -> List[str]:
        """
        Get the node properties that are list of dictionaries and should be converted to property lists.
        """
        property_list_of_dicts_to_model_as_multiple_lists = []
        for label in node_labels:
            if label in self.COMPLEX_VALUE_LIST_AS_MULTIPLE_SIMPLE_VALUE_LISTS:
                property_list_of_dicts_to_model_as_multiple_lists.extend(
                    self.COMPLEX_VALUE_LIST_AS_MULTIPLE_SIMPLE_VALUE_LISTS[label])
        return property_list_of_dicts_to_model_as_multiple_lists

    def _gen_unique_node_name(self) -> int:
        """Generate unique ID for nodes."""
        self.uid_counter += 1
        return self.uid_counter

    def _group_nodes_by_label(self, nodes: List[Dict]) -> Dict[Tuple[str], List[Dict]]:
        """Group nodes by their labels."""
        grouped = {}
        for node in nodes:
            labels = tuple(sorted(node.pop('labels')))
            if labels not in grouped:
                grouped[labels] = []
            grouped[labels].append(node)
        return grouped

    def _add_relationship(self, relationships: Dict[str, List], rel_type: str, from_uid: int, to_uid: int):
        """Add a relationship to the relationships dictionary."""
        if rel_type not in relationships:
            relationships[rel_type] = []
        relationships[rel_type].append({
            'from_uid': from_uid,
            'to_uid': to_uid,
        })

    def _merge_relationships(self, target: Dict[str, List], source: Dict[str, List]):
        """Merge relationships from source into target."""
        for key, value in source.items():
            if key in target:
                target[key].extend(value)
            else:
                target[key] = value.copy()

    def _cleanup_uids(self, internal_ids: List[int]):
        """Remove `uid` property only from the nodes created by this process."""
        delete_query = """
        UNWIND $ids AS id
        MATCH (n)
        WHERE id(n) = id
        REMOVE n.uid
        """
        with self.driver.session() as session:
            session.run(delete_query, ids=internal_ids)

    def _create_nodes(self, grouped_nodes: Dict[Tuple[str], List[Dict]]) -> Dict[int, int]:
        """Create nodes in Neo4j and return uid to internal_id mapping."""
        create_nodes_query = """
        UNWIND keys($data) AS labelString
        WITH split(labelString, ",") AS labels, $data[labelString] AS propertiesList
        UNWIND propertiesList AS properties
        CALL {
            WITH labels, properties
            CALL apoc.create.node(labels, properties) YIELD node
            RETURN id(node) AS internal_id, properties.uid AS uid
        }
        RETURN internal_id, uid
        """

        # Convert tuple keys to strings for Neo4j compatibility
        data_for_query = {
            ",".join(label_tuple): node_list
            for label_tuple, node_list in grouped_nodes.items()
        }

        uid_to_internal_id = {}

        with self.driver.session() as session:
            # Create indexes for better performance
            for labels in grouped_nodes.keys():
                for label in labels:
                    session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.uid)")

            # Create nodes
            result = session.run(create_nodes_query, data=data_for_query)
            for record in result:
                uid_to_internal_id[record['uid']] = record['internal_id']

        return uid_to_internal_id

    def _create_relationships(self, relationships: Dict[str, List], uid_to_internal_id: Dict[int, int]):
        """Create relationships in Neo4j."""
        with self.driver.session() as session:
            total_created = 0

            for rel_type, rel_list in relationships.items():
                # Prepare relationship data
                prepared_rels = []
                for rel in rel_list:
                    try:
                        prepared_rels.append({
                            'from_id': uid_to_internal_id[rel['from_uid']],
                            'to_id': uid_to_internal_id[rel['to_uid']]
                        })
                    except KeyError:
                        logger.warning(
                            f"Skipping relationship {rel_type} from {rel['from_uid']} to {rel['to_uid']} due to missing UID mapping.")
                        continue

                if prepared_rels:
                    # Create relationships in batch
                    create_rels_query = f"""
                    UNWIND $relationships AS rel
                    MATCH (from_node) WHERE id(from_node) = rel.from_id
                    MATCH (to_node) WHERE id(to_node) = rel.to_id
                    CREATE (from_node)-[:{rel_type}]->(to_node)
                    RETURN count(*) as created
                    """

                    result = session.run(create_rels_query, relationships=prepared_rels)
                    created = result.single()['created']
                    total_created += created
                    print(f"Created {created} relationships of type '{rel_type}'")

            return total_created

    def _process_dict(self, obj: Dict, node_properties: Optional[Dict[str, any]] = None) -> Tuple[
        List[Dict], Dict[str, List]]:
        nodes = []
        relationships = {}
        node_properties = node_properties or {}

        node_uid = self._gen_unique_node_name()
        node_labels = aas_utils.identify_types(obj)
        node_properties.update({
            'uid': node_uid,
            'labels': node_labels
        })

        # unpack the DICTS_TO_PROPERTY_LISTS
        node_property_dicts_as_lists = self._get_props_to_model_as_multiple_lists(node_labels)

        for key, value in obj.items():
            if key in KEYS_TO_IGNORE:
                continue
            elif key in node_property_dicts_as_lists:
                # BEFORE: keys = [{"type": "GlobalReference", "value": "0173-1#02-AAW001#001"}}, ...]
                # AFTER:  keys_type = ["GlobalReference", ...]
                #         keys_value = ["0173-1#02-AAW001#001", ...]
                if value:
                    for dict_key in value[0].keys():
                        node_properties[f"{key}_{dict_key}"] = [dict_[dict_key] for dict_ in value]
            elif isinstance(value, dict):
                child_nodes, child_rels = self._process_dict(value)
                nodes.extend(child_nodes)
                self._merge_relationships(relationships, child_rels)

                # Create relationship to the last created node
                if child_nodes:
                    self._add_relationship(relationships, key, node_uid, child_nodes[-1]['uid'])
                    if "Referable" in child_nodes[-1]['labels']:
                        self._add_relationship(relationships, "child", node_uid, child_nodes[-1]['uid'])

            elif isinstance(value, list):
                for i, item in enumerate(value, start=0):
                    if isinstance(item, dict):
                        child_nodes, child_rels = self._process_dict(item, node_properties={"index": i})
                        nodes.extend(child_nodes)
                        self._merge_relationships(relationships, child_rels)

                        # Create relationship to the last created node
                        if child_nodes:
                            self._add_relationship(relationships, key, node_uid, child_nodes[-1]['uid'])
                    else:
                        logger.warning(f"Unsupported type in list: {type(item)}")
                        continue
            else:
                node_properties[key] = value

        nodes.append(node_properties)
        return nodes, relationships

    def _process_aas_json_data(self, aas_json_data: Dict[str, Any]) -> Tuple[List[Dict], Dict[str, List]]:
        """Process JSON data into nodes and relationships."""
        nodes = []
        relationships = {}

        for key, label in IDENTIFIABLE_KEYS.items():
            try:
                for obj in aas_json_data[key]:
                    child_nodes, child_rels = self._process_dict(obj)
                    nodes.extend(child_nodes)
                    self._merge_relationships(relationships, child_rels)
            except KeyError:
                logger.info(f"Key '{key}' not found in the JSON file")
        return nodes, relationships

    def _process_aas_json_file(self, file_path: str) -> Tuple[List[Dict], Dict[str, List]]:
        """Process a single JSON file and return nodes and relationships."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            nodes, relationships = self._process_aas_json_data(data)
        return nodes, relationships

    def _process_aas_json_file_batch(self, directory: str, file_batch: List[str]) -> Tuple[List[Dict], Dict[str, List]]:
        """Process a batch of JSON files and return nodes and relationships."""
        batch_nodes = []
        batch_relationships = {}
        for filename in file_batch:
            nodes, relationships = self._process_aas_json_file(join(directory, filename))
            batch_nodes.extend(nodes)
            self._merge_relationships(batch_relationships, relationships)
        return batch_nodes, batch_relationships

    def _upload_nodes_and_relationships(self, nodes: List[Dict], relationships: Dict[str, List],
                                        stats: AASUploadStats = None,
                                        exist_uid_to_internal_id: Optional[Dict[int, int]] = None
                                        ) -> AASUploadStats:
        """Upload nodes and relationships to Neo4j."""
        if stats is None:
            stats = AASUploadStats()

        # Group nodes and filter relationships for this batch
        grouped_nodes = self._group_nodes_by_label(nodes)

        # Create nodes in Neo4j
        node_start_time = time.time()

        uid_to_internal_id = self._create_nodes(grouped_nodes)
        if exist_uid_to_internal_id:
            # Merge existing UID to internal ID mapping with newly created nodes
            uid_to_internal_id.update(exist_uid_to_internal_id)

        node_count = sum(len(nodes) for nodes in grouped_nodes.values())
        node_creation_time = time.time() - node_start_time
        stats.total_node_creation_time += node_creation_time
        stats.total_nodes_created += node_count
        logger.info(f"Created {node_count} nodes in {node_creation_time:.2f} seconds")

        # Create relationships in Neo4j
        rel_start_time = time.time()
        relationship_count = self._create_relationships(relationships, uid_to_internal_id)
        relationship_creation_time = time.time() - rel_start_time
        stats.total_relationship_creation_time += relationship_creation_time
        stats.total_relationships_created += relationship_count
        logger.info(f"Created {relationship_count} relationships in {relationship_creation_time:.2f} seconds")

        # Memory cleanup
        self._cleanup_uids(list(uid_to_internal_id.values()))
        del grouped_nodes, uid_to_internal_id

        return stats

    def upload_all_aas_json_from_dir(self, directory: str, batch_size: int = 50) -> Dict[str, int]:
        """Upload JSON files from directory into Neo4j using batch processing."""
        stats = AASUploadStats()

        # Get all JSON files
        json_files = [f for f in os.listdir(directory) if isfile(join(directory, f)) and f.endswith('.json')]
        stats.total_files = len(json_files)
        stats.total_batches = (stats.total_files + batch_size - 1) // batch_size  # Ceiling division

        logger.info(f"Found {stats.total_files} JSON files in directory '{directory}'")
        logger.info(f"Batch size: {stats.total_batches} batches of {batch_size} files each")

        # Process files in batches
        for batch_num in range(stats.total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, stats.total_files)
            current_batch = json_files[start_idx:end_idx]

            logger.info(f"\n--- Processing Batch {batch_num + 1}/{stats.total_batches} ---")
            logger.info(f"Files {start_idx + 1}-{end_idx} of {stats.total_files}")

            # Process current batch
            batch_start_time = time.time()
            batch_nodes, batch_relationships = self._process_aas_json_file_batch(directory, current_batch)
            processing_time = time.time() - batch_start_time
            stats.total_processing_time += processing_time
            logger.info(f"Processed {len(current_batch)} files in {processing_time:.2f} seconds")

            if not batch_nodes:
                logger.info("No nodes to create in this batch, skipping...")
                continue

            self._upload_nodes_and_relationships(batch_nodes, batch_relationships, stats)
            batch_total_time = time.time() - batch_start_time
            logger.info(f"Batch {batch_num + 1} completed in {batch_total_time:.2f} seconds")

        stats.finish()
        return stats

    def upload_aas_json_file(self, file_path: str):
        """Upload a single JSON file to the Neo4j database."""
        nodes, relationships = self._process_aas_json_file(file_path)
        stats = self._upload_nodes_and_relationships(nodes, relationships)
        stats.finish()

    def upload_aas_json(self, aas_json_data: Dict[str, Any]):
        """Upload AAS JSON data directly to the Neo4j database."""
        nodes, relationships = self._process_aas_json_data(aas_json_data)
        stats = self._upload_nodes_and_relationships(nodes, relationships)
        stats.finish()


class AASNeo4JClient(AASUploaderInNeo4J):
    node_names: Set[str] = set()

    def add_identifiable(self, obj: Dict):
        if self.identifiable_exists(obj['id']):
            raise KeyError(f"Identifiable with id {obj['id']} already exists in the database.")
        nodes, relationships = self._process_dict(obj)
        return self._upload_nodes_and_relationships(nodes, relationships)

    def add_referable(self, obj: Dict, parent_id: Optional[str] = None, id_short_path: Optional[str] = None):
        node_labels = aas_utils.identify_types(obj)
        if "Identifiable" in node_labels:
            if parent_id or id_short_path:
                raise ValueError("Parent ID or ID short path should not be provided for Identifiable objects")
            return self.add_identifiable(obj)
        else:
            if not (parent_id and id_short_path):
                raise ValueError("Parent ID and ID short path should be provided for Referable objects")
            return self.add_submodel_element(obj, parent_id, id_short_path)

    def add_submodel_element(self, obj: Dict, parent_id: str, id_short_path: str):
        parent_node_internal_id = self._find_node(parent_id, id_short_path)
        nodes, relationships = self._process_dict(obj)

        self._add_relationship(relationships, "child", parent_node_internal_id, nodes[-1]['uid'])
        self._add_relationship(relationships, "value", parent_node_internal_id, nodes[-1]['uid'])
        stats = self._upload_nodes_and_relationships(nodes, relationships,
                                                     exist_uid_to_internal_id={
                                                         parent_node_internal_id: parent_node_internal_id})
        return stats

    def identifiable_exists(self, identifier: str) -> bool:
        """Check if an Identifiable node with the given ID exists in the Neo4j database."""
        clause = f"MATCH (n:Identifiable {{id: '{identifier}'}} ) RETURN count(n)>0"
        result = self.execute_clause(clause, single=True)
        return result[0]

    def remove_referable(self, parent_id: str, id_short_path: str = None):
        clauses, referable_node = self._find_node_clause(parent_id, id_short_path)
        delete_clause = (
            f"CALL apoc.path.subgraphAll({referable_node}, {{relationshipFilter: '>'}}) YIELD nodes "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "UNWIND nodes AS node "
            "DETACH DELETE node "
            "RETURN count(node) AS deletedNodes; "
        )
        return self.execute_clause(clauses + delete_clause)

    def remove_identifiable(self, identifier: str):
        return self.remove_referable(identifier)

    def get_referable(self, parent_id: str, id_short_path: str = None) -> Dict:
        subgraph_json = self._get_subgraph_of_referable(parent_id, id_short_path)
        return self._convert_referable_subgraph_to_dict(subgraph_json)

    def get_identifiable(self, identifier: str) -> Dict:
        return self.get_referable(identifier)

    def count_nodes_with_label(self, label: str) -> int:
        """Count the number of nodes with a specific label."""
        clause = f"MATCH (n:{label}) RETURN COUNT(n) AS count"
        result = self.execute_clause(clause, single=True)
        return result["count"] if result else 0

    def count_referables(self) -> int:
        return self.count_nodes_with_label("Referable")

    def count_identifiables(self) -> int:
        return self.count_nodes_with_label("Identifiable")

    def _find_node(self, parent_id: str, id_short_path: Optional[str] = None) -> int:
        """
        Find a node in the Neo4j database based on the parent ID and optional idShortPath.
        """
        clause, found_node = self._find_node_clause(parent_id, id_short_path)
        clause += f"RETURN ID({found_node}) AS node_id"
        with self.driver.session() as session:
            result = session.run(clause).single()
            if result is None:
                raise KeyError(f"No node found with parent_id={parent_id} and id_short_path={id_short_path}")
            elif len(result["node_id"]) != 1:
                raise ValueError(f"Multiple nodes found with parent_id={parent_id} and id_short_path={id_short_path}")
            return result["node_id"][0]

    def _find_node_clause(self, parent_id: str, id_short_path: Optional[str] = None) -> Optional[str]:
        found_node = "the_node"

        if not id_short_path:
            return f"MATCH ({found_node}:Identifiable {{id: '{parent_id}'}})\n"

        clause = f"MATCH (parent:Identifiable {{id: '{parent_id}'}})"
        id_shorts = aas_utils.itemize_id_short_path(id_short_path)
        for i, idShort in enumerate(id_shorts):
            if not i == len(id_shorts) - 1:
                clause += f"-[:child]->(child_{i} {{idShort: '{idShort}'}})\n"
            else:
                clause += f"-[:child]->({found_node} {{idShort: '{idShort}'}})\n"
        return clause, found_node

    def _get_subgraph_of_referable(self, parent_id: str, id_short_path: Optional[str] = None):
        """
        Fetches a subgraph of Referable object from Neo4j.

        It includes the object node itself and all its children being attributes of the object.
        """
        find_node_clause, found_parent_node = self._find_node_clause(parent_id, id_short_path)
        get_subgraph_clause = (
            f"CALL apoc.path.subgraphAll({found_parent_node}, {{relationshipFilter: '>'}}) YIELD nodes, relationships "
            "WHERE NOT EXISTS { MATCH (node)-[:references]-() } "
            "RETURN apoc.convert.toJson({nodes: nodes, relationships: relationships}) AS json;"
        )
        result = self.execute_clause(find_node_clause + get_subgraph_clause, single=True)
        if result is None:
            raise KeyError(f"No Referable found with: id={parent_id}, id_short_path={id_short_path}")
        subgraph_json = json.loads(result["json"])
        return subgraph_json

    def _convert_referable_subgraph_to_dict(self, subgraph: Dict) -> Dict:
        """Take a Neo4J subgraph of a Referable and convert it to a dictionary."""

        def convert_node(node: Dict) -> Dict:
            return {key: value for key, value in node['properties'].items()}

        def create_list_of_dicts(*lists: List[List[any]], keys: List[str]) -> List[Dict]:
            if len(keys) != len(lists):
                raise ValueError("Number of keys must match number of input lists.")

            objs = [dict(zip(keys, values)) for values in zip(*lists)]
            return objs

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
                        if value and isinstance(value, list) and isinstance(value[0], dict) and value[0].get(
                                'index') is not None:
                            node_dict[key] = sorted(value, key=lambda x: x.get('index', 0))
                            for item in node_dict[key]:
                                item.pop('index', None)

                    # Handle specific keys for certain node types
                    related_node_labels = related_node['labels']
                    props_list_of_dicts = self._get_props_to_model_as_multiple_lists(related_node_labels)
                    if props_list_of_dicts:
                        for original_prop in props_list_of_dicts:
                            original_prop_prefix = original_prop + "_"

                            # Find all keys that belong to this original_prop
                            part_attr_keys = [key for key in related_node_dict if key.startswith(original_prop_prefix)]

                            if not part_attr_keys:
                                continue

                            # Extract lists and strip the prefix from keys
                            lists = [related_node_dict.pop(key) for key in part_attr_keys]
                            keys = [key.removeprefix(original_prop_prefix) for key in part_attr_keys]
                            related_node_dict[original_prop] = create_list_of_dicts(*lists, keys=keys)

        root_node = subgraph['nodes'][0]
        root_node_dict = convert_node(root_node)
        add_relationships(root_node, root_node_dict,
                          [r for r in subgraph['relationships'] if r['start']['id'] == root_node['id']])
        return root_node_dict


def main():
    def optimized_upload_all_submodels(submodels_folder="examples/aas/Festo_AAS_JSON/"):
        # Use the OptimizedAASNeo4JClient for batch processing
        optimized_client = AASUploaderInNeo4J(uri="bolt://localhost:7687", user="neo4j", password="password")
        optimized_client._remove_all()
        # set timer
        import time
        start_time = time.time()
        result = optimized_client.upload_all_aas_json_from_dir(submodels_folder, batch_size=100)
        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")

    logger.setLevel(logging.INFO)
    optimized_upload_all_submodels()


if __name__ == '__main__':
    main()
