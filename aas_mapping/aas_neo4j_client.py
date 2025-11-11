import hashlib
import logging
import os
import time
from copy import deepcopy
from dataclasses import dataclass
from os.path import isfile, join
from typing import Dict, List, Tuple, Optional, Set, Any, Iterable
import neo4j
import json

from neo4j import Driver, Session
from neo4j.exceptions import TransientError, ClientError

from aas_mapping import aas_utils
from aas_mapping.aas_utils import IDENTIFIABLE_KEYS

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CypherClause = str

KEYS_TO_IGNORE = tuple()
SPECIFIC_RELATIONSHIPS = ("child", "references")
ORDER_IMPORTANT_RELATIONSHIPS = ("specificAssetIds", )


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
                result = session.run(clause).single()
            else:
                result = session.run(clause)
                if result:
                    result = [record for record in result]
            return result

    def _remove_all(self, batch_size = 10000):
        """
        Remove all nodes and relationships from the Neo4j database in batches.
        It prevents memory errors on large databases.
        """
        with self.driver.session() as session:
            while True:
                result = session.run(f"""
                    MATCH (n)
                    WITH n LIMIT {batch_size}
                    DETACH DELETE n
                    RETURN count(n) AS nodes_deleted
                """)
                nodes_deleted = result.single()["nodes_deleted"]
                logger.info(f"Deleted {nodes_deleted} nodes.")

                # If the number of nodes deleted is less than the batch size,
                # it means we have reached the end of the database.
                if nodes_deleted < batch_size:
                    break

    def _truncate_db(self, db_name="neo4j"):
        """
        Remove all nodes and relationships from the Neo4j database in batches.
        It prevents memory errors on large databases.
        """
        with self.driver.session(database="system") as session:  # must run on system DB
            session.run(f"CREATE OR REPLACE DATABASE {db_name};")
            logger.info(f"Database '{db_name}' truncated successfully.")
        session.close()

    def save_clauses_to_file(self, file_name: str, clauses: CypherClause):
        """Save the generated Cypher clauses to a file."""
        with open(file_name, 'w', encoding='utf8') as file:
            file.write(clauses)


class AASUploaderInNeo4J(BaseNeo4JClient):
    # In AAS, multiple references may point to the same target. By deduplicating
    # these references, we ensure that only one canonical instance is created
    # and reused whenever all reference attributes are identical.
    DEDUPLICATED_OBJECT_TYPES = {
        "Reference",
        # "Qualifier",
        # "Extension",
        "ConceptDescription",
        # "EmbeddedDataSpecification"
    }

    DEFAULT_OPTIMIZATION_CLAUSES = [
        "CREATE INDEX FOR (r:Identifiable) ON (r.id);",
        "CREATE INDEX FOR (r:Referable) ON (r.idShort);",
        "CREATE INDEX rel_list_index FOR () - [r:value]-() ON (r.list_index);"
    ]

    # Attributes of objects that are lists of dictionaries and should be converted to multiple lists with simple values
    # BEFORE: keys = [{"type": "GlobalReference", "value": "0173-1#02-AAW001#001"}}, ...]
    # AFTER:  keys_type = ["GlobalReference", ...]
    #         keys_value = ["0173-1#02-AAW001#001", ...]
    LIST_OF_DICTS_PROP_AS_MULTIPLE_LIST_PROPS = {
        "MultiLanguageProperty": ["value"],
        "DataSpecificationIec61360": ["preferredName", "shortName", "definition"],
        "Reference": ["keys"],
        # "Qualifiable": ["qualifiers"] # Problem: qualifier can have a SemanticId
        "Referable": ["description", "displayName"],
    }

    # Attributes of objects that are dictionaries and should be converted to multiple properties with simple values
    # BEFORE: keys = {"type": "GlobalReference", "value": "0173-1#02-AAW001#001"}
    # AFTER:  keys_type = "GlobalReference"
    #         keys_value = "0173-1#02-AAW001#001"
    DICT_PROP_AS_MULTIPLE_PROPS = {
        "Reference": ["referredSemanticId"],
        "AssetInformation": ["defaultThumbnail"],
        # "Identifiable": ["administration"], # Problem: AdministrativeInfo can have a Reference in "creator" attr
    }

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password)) if uri else None
        self.uid_counter = 0

        # e.g. {HASH: uid}
        self.deduplicated_nodes: dict[str: int] = {}
        self.deduplicated_rels: set[str] = set()
        self.uid_to_internal_id: dict[str: int] = {}

    def optimize_database(self):
        """Optimize the Neo4j database by creating all necessary indexes."""
        for clause in self.DEFAULT_OPTIMIZATION_CLAUSES:
            try:
                self.execute_clause(clause, single=True)
            except neo4j.exceptions.ClientError as e:
                if e.code == "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists":
                    logger.info(f"Index already exists: {clause}")
                else:
                    logger.warning(f"Failed to create index: {clause}, Error: {e}")

    def _remove_all_indexes_and_constraints(self):
        def drop_all_indexes_and_constraints(tx):
            # Drop all indexes
            indexes = tx.run("SHOW INDEXES YIELD name").values()
            for (name,) in indexes:
                tx.run(f"DROP INDEX `{name}`")
                print(f"Dropped index: {name}")

            # Drop all constraints
            constraints = tx.run("SHOW CONSTRAINTS YIELD name").values()
            for (name,) in constraints:
                tx.run(f"DROP CONSTRAINT `{name}`")
                print(f"Dropped constraint: {name}")

        with self.driver.session() as session:
            session.execute_write(drop_all_indexes_and_constraints)

    def _get_props_to_model_as_multiple_lists(self, node_labels: Iterable[str]) -> List[str]:
        """
        Get the node properties that are list of dictionaries and should be converted to property lists.
        """
        property_list_of_dicts_to_model_as_multiple_lists = []
        for label in node_labels:
            if label in self.LIST_OF_DICTS_PROP_AS_MULTIPLE_LIST_PROPS:
                property_list_of_dicts_to_model_as_multiple_lists.extend(
                    self.LIST_OF_DICTS_PROP_AS_MULTIPLE_LIST_PROPS[label])
        return property_list_of_dicts_to_model_as_multiple_lists

    def _get_complex_props_to_model_as_multiple_simple_props(self, node_labels: Iterable[str]) -> List[str]:
        """
        Get the node properties that are list of dictionaries and should be converted to property lists.
        """
        property_list_of_dicts_to_model_as_multiple_simple_props = []
        for label in node_labels:
            if label in self.DICT_PROP_AS_MULTIPLE_PROPS:
                property_list_of_dicts_to_model_as_multiple_simple_props.extend(
                    self.DICT_PROP_AS_MULTIPLE_PROPS[label])
        return property_list_of_dicts_to_model_as_multiple_simple_props


    def _gen_unique_node_name(self) -> int:
        self.uid_counter += 1
        return self.uid_counter

    def _group_nodes_by_label(self, nodes: List[Dict]) -> Dict[Tuple[str], List[Dict]]:
        grouped = {}
        for node in nodes:
            labels = tuple(sorted(node.pop('labels')))
            if labels not in grouped:
                grouped[labels] = []
            grouped[labels].append(node)
        return grouped

    def _add_relationship(self, relationships: Dict[str, List], rel_type: str, from_uid: int, to_uid: int,
                          rel_props: Optional[dict] = None):
        """Add a relationship to the relationships dictionary."""
        if rel_type not in relationships:
            relationships[rel_type] = []
        if rel_props is None:
            rel_props = {}
        relationships[rel_type].append({
            'from_uid': from_uid,
            'to_uid': to_uid,
            'rel_props': rel_props
        })

    def _merge_relationships(self, target: Dict[str, List], source: Dict[str, List]):
        """Merge relationships from source into target."""
        for key, value in source.items():
            target.setdefault(key, []).extend(value)

    def _create_nodes(self, session: Session, grouped_nodes: Dict[Tuple[str], List[Dict]]) -> Dict[int, int]:
        """Create nodes in Neo4j and return uid to internal_id mapping."""
        create_nodes_query = """
        UNWIND keys($data) AS labelsString
        
        WITH split(labelsString, ",") AS labels, $data[labelsString] AS nodesProperties
        
        UNWIND nodesProperties AS nodeProperties
        CREATE (n:$(labels))
        SET n = nodeProperties
        
        RETURN elementId(n) AS internal_id, nodeProperties.uid AS uid
        """

        # Convert tuple keys to strings for Neo4j compatibility
        data_for_query = {
            ",".join(label_tuple): node_list
            for label_tuple, node_list in grouped_nodes.items()
        }

        for labels in grouped_nodes.keys():
            for label in labels:
                session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.uid)")

        uid_to_internal_id = {}
        # Create nodes
        result = session.run(create_nodes_query, data=data_for_query)
        for record in result:
            uid_to_internal_id[record['uid']] = record['internal_id']

        return uid_to_internal_id

    def _create_relationships(self, session: Session, relationships: Dict[str, List],
                              uid_to_internal_id: Dict[int, int], db_batch_size: int = 10000):
        """Create relationships in Neo4j."""
        created_rels = 0
        for rel_type, rel_list in relationships.items():
            for i in range(0, len(rel_list), db_batch_size):
                batch_rels = rel_list[i:i + db_batch_size]
                prepared_rels = []
                for rel in batch_rels:
                    try:
                        prepared_rels.append({
                            'from_id': uid_to_internal_id[rel['from_uid']],
                            'to_id': uid_to_internal_id[rel['to_uid']],
                            'rel_props': rel['rel_props']
                        })
                    except KeyError:
                        logger.warning(
                            f"Skipping relationship {rel_type} from {rel['from_uid']} to {rel['to_uid']} due to missing UID mapping.")
                        continue

                if prepared_rels:
                    # Create relationships in batch
                    create_rels_query = f"""
                    UNWIND $relationships AS rel
                    MATCH (from_node) WHERE elementId(from_node) = rel.from_id
                    MATCH (to_node) WHERE elementId(to_node) = rel.to_id
                    CREATE (from_node)-[r:{rel_type}]->(to_node)
                    SET r = rel.rel_props
                    RETURN count(*) as created
                    """

                    try:
                        result = session.run(create_rels_query, relationships=prepared_rels)
                        created = result.single()['created']
                        created_rels += created
                    except TransientError as e:
                        logger.error(f"Transient error during relationship creation batch: {e}")

        return created_rels

    def _process_dict(self, obj: Dict, node_properties: Optional[Dict[str, any]] = None) -> Tuple[List[Dict], Dict[str, List]]:
        nodes = []
        relationships: dict[str, dict[str, str]] = {}
        node_properties = node_properties or {}

        node_uid = self._gen_unique_node_name()
        node_labels = aas_utils.identify_types(obj)
        node_properties.update({
            'uid': node_uid,
            'labels': node_labels
        })

        # unpack the DICTS_TO_PROPERTY_LISTS
        list_of_dicts_prop_as_multiple_list_props = self._get_props_to_model_as_multiple_lists(node_labels)
        dict_prop_as_multiple_props = self._get_complex_props_to_model_as_multiple_simple_props(node_labels)

        for key, value in obj.items():
            if key in KEYS_TO_IGNORE:
                continue
            elif key in list_of_dicts_prop_as_multiple_list_props:
                # BEFORE: keys = [{"type": "GlobalReference", "value": "0173-1#02-AAW001#001"}}, ...]
                # AFTER:  keys_type = ["GlobalReference", ...]
                #         keys_value = ["0173-1#02-AAW001#001", ...]
                if value:
                    for dict_key in value[0].keys():
                        node_properties[f"{key}_{dict_key}"] = [dict_[dict_key] for dict_ in value]
            elif key in dict_prop_as_multiple_props:
                if value:
                    child_nodes, child_rels = self._process_dict(value)
                    if len(child_nodes) > 1:
                        raise ValueError(f"The dict should have only one child node, got {len(child_nodes)}: {value}")

                    for sub_key, sub_value in child_nodes[0].items():
                        if sub_key not in ("uid", "labels"):
                            node_properties[f"{key}_{sub_key}"] = sub_value

                    rels = {
                        f"{key}_{rel_type}": {**rel, "from_uid": node_uid}
                        for rel_type, rel in child_rels.items()
                    }
                    self._merge_relationships(relationships, rels)

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
                        child_nodes, child_rels = self._process_dict(item)
                        nodes.extend(child_nodes)
                        self._merge_relationships(relationships, child_rels)

                        # Create relationship to the last created node
                        if child_nodes:
                            rel_props = {"is_list": True}
                            if "SubmodelElementList" in node_labels or key in ORDER_IMPORTANT_RELATIONSHIPS:
                                rel_props = {"list_index": i}
                            self._add_relationship(relationships, key, node_uid, child_nodes[-1]['uid'], rel_props=rel_props)
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
                                        exist_uid_to_internal_id: Optional[Dict[int, int]] = None,
                                        db_batch_size: int = 1000) -> AASUploadStats:
        """Upload nodes and relationships to Neo4j in a single transaction."""
        if stats is None:
            stats = AASUploadStats()

        # Group nodes and filter relationships for this batch
        grouped_nodes = self._group_nodes_by_label(nodes)

        # --- 🔧 Deduplication step ---
        deduplicated_uid_map = {}  # new_uid -> existing_uid mapping for this batch

        for label_tuple in list(grouped_nodes.keys()):
            # Check if any of the labels in this tuple should be deduplicated
            if not any(lbl in self.DEDUPLICATED_OBJECT_TYPES for lbl in label_tuple):
                continue

            filtered_nodes = []
            for node in grouped_nodes[label_tuple]:
                node_uid = node["uid"]

                node_copy = deepcopy(node)
                node_copy.pop("uid")
                # Deterministic JSON hash from properties
                hash_input = json.dumps(node_copy, sort_keys=True)
                hash_value = hashlib.sha256(hash_input.encode()).hexdigest()

                if hash_value in self.deduplicated_nodes:
                    # This node already exists (deduplicate)
                    existing_uid = self.deduplicated_nodes[hash_value]
                    deduplicated_uid_map[node_uid] = existing_uid
                else:
                    node["hash"] = hash_value
                    # First time we see this node -> keep it
                    self.deduplicated_nodes[hash_value] = node_uid
                    filtered_nodes.append(node)

            # Replace node list with deduplicated version
            grouped_nodes[label_tuple] = filtered_nodes

        # --- 🔧 Rewrite relationships to use deduplicated UIDs ---
        if deduplicated_uid_map:
            for rel_type, rel_list in relationships.items():
                for rel in rel_list:
                    if rel["from_uid"] in deduplicated_uid_map:
                        rel["from_uid"] = deduplicated_uid_map[rel["from_uid"]]
                    if rel["to_uid"] in deduplicated_uid_map:
                        rel["to_uid"] = deduplicated_uid_map[rel["to_uid"]]

        if deduplicated_uid_map: # TODO: Fast half-working temporal solution. DELETE!
            for rel_type, rel_list in relationships.items():
                unique_rels = []
                seen = set()
                for rel in rel_list:
                    key = (rel['from_uid'], rel['to_uid'])
                    if key not in seen:
                        seen.add(key)
                        unique_rels.append(rel)
                relationships[rel_type] = unique_rels

        # --- Continue with database operations ---
        with self.driver.session() as session:
            # 1. Create Nodes in Batches
            node_start_time = time.time()
            self.uid_to_internal_id.update(self._create_nodes(session, grouped_nodes))
            if exist_uid_to_internal_id:
                # Merge existing UID to internal ID mapping with newly created nodes
                self.uid_to_internal_id.update(exist_uid_to_internal_id)

            node_creation_time = time.time() - node_start_time
            stats.total_node_creation_time += node_creation_time
            node_count = sum(len(nodes) for nodes in grouped_nodes.values())
            stats.total_nodes_created += node_count
            logger.info(f"Created {node_count} nodes in {node_creation_time:.2f} seconds")

            # 2. Create Relationships in Batches
            rel_start_time = time.time()
            relationship_count = self._create_relationships(session, relationships, self.uid_to_internal_id, db_batch_size)
            relationship_creation_time = time.time() - rel_start_time
            stats.total_relationship_creation_time += relationship_creation_time
            stats.total_relationships_created += relationship_count
            logger.info(f"Created {relationship_count} relationships in {relationship_creation_time:.2f} seconds")

            # 3. Cleanup UIDs in Batches
            # self._cleanup_uids_in_session(session, list(uid_to_internal_id.values()), db_batch_size)

        # del grouped_nodes, uid_to_internal_id
        del grouped_nodes

        return stats

    def _cleanup_uids_in_session(self, session: Session, internal_ids: List[int], batch_size: int):
        """Removes `uid` property from nodes in batches within an existing session."""
        delete_query = """
        UNWIND $ids AS id
        MATCH (n)
        WHERE elementId(n) = id
        REMOVE n.uid
        """
        for i in range(0, len(internal_ids), batch_size):
            batch_ids = internal_ids[i:i + batch_size]
            try:
                session.run(delete_query, ids=batch_ids)
            except ClientError as e:
                logging.warning(f"Error during UID cleanup for batch: {e}")

    def upload_all_aas_json_from_dir(self, directory: str, file_batch_size: int = 50,
                                     db_batch_size: int = 10000) -> AASUploadStats:
        """Upload JSON files from directory into Neo4j using batch processing."""
        stats = AASUploadStats()
        json_files = [f for f in os.listdir(directory) if isfile(join(directory, f)) and f.endswith('.json')]
        stats.total_files = len(json_files)
        stats.total_batches = (stats.total_files + file_batch_size - 1) // file_batch_size

        logger.info(f"Found {stats.total_files} JSON files in directory '{directory}'")
        logger.info(f"File batch size: {stats.total_batches} batches of {file_batch_size} files each")
        logger.info(f"Database transaction batch size: {db_batch_size}")

        # Process files in batches
        for batch_num in range(stats.total_batches):
            start_idx = batch_num * file_batch_size
            end_idx = min(start_idx + file_batch_size, stats.total_files)
            current_file_batch = json_files[start_idx:end_idx]

            logger.info(f"\n--- Processing Batch {batch_num + 1}/{stats.total_batches} ---")
            logger.info(f"Files {start_idx + 1}-{end_idx} of {stats.total_files}")

            # Process current batch
            batch_start_time = time.time()
            batch_nodes, batch_relationships = self._process_aas_json_file_batch(directory, current_file_batch)

            processing_time = time.time() - batch_start_time
            stats.total_processing_time += processing_time
            logger.info(f"Processed {len(current_file_batch)} files in {processing_time:.2f} seconds")

            if not batch_nodes:
                logger.info("No nodes to create in this batch, skipping...")
                continue

            self._upload_nodes_and_relationships(batch_nodes, batch_relationships, stats, db_batch_size=db_batch_size)

            batch_total_time = time.time() - batch_start_time
            logger.info(f"Batch {batch_num + 1} completed in {batch_total_time:.2f} seconds")

        stats.finish()
        return stats

    def upload_aas_json_file(self, file_path: str, db_batch_size: int = 1000):
        nodes, relationships = self._process_aas_json_file(file_path)
        stats = self._upload_nodes_and_relationships(nodes, relationships, db_batch_size=db_batch_size)
        stats.finish()

    def upload_aas_json(self, aas_json_data: Dict[str, Any], db_batch_size: int = 1000):
        nodes, relationships = self._process_aas_json_data(aas_json_data)
        stats = self._upload_nodes_and_relationships(nodes, relationships, db_batch_size=db_batch_size)
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

    def _find_node_clause(self, parent_id: str, id_short_path: Optional[str] = None) -> (str, str):
        found_node = "the_node"

        if not id_short_path:
            return f"MATCH ({found_node}:Identifiable {{id: '{parent_id}'}})\n", found_node

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

        def group_prefixed_props_back_to_list_of_dicts_prop(node_labels: list[str], node_properties: dict):
            props_with_list_of_dicts = self._get_props_to_model_as_multiple_lists(node_labels)
            if not props_with_list_of_dicts:
                return node_properties

            for original_prop in props_with_list_of_dicts:
                original_prop_prefix = original_prop + "_"

                # Find all keys that belong to this original_prop
                part_attr_keys = [key for key in node_properties if key.startswith(original_prop_prefix)]

                if not part_attr_keys:
                    continue

                # Extract lists and strip the prefix from keys
                lists = [node_properties.pop(key) for key in part_attr_keys]
                keys = [key.removeprefix(original_prop_prefix) for key in part_attr_keys]
                node_properties[original_prop] = create_list_of_dicts(*lists, keys=keys)
            return node_properties

        def group_prefixed_props_back_to_dict_prop(node_labels: list[str], node_properties: dict):
            props_with_dicts = self._get_complex_props_to_model_as_multiple_simple_props(node_labels)
            if not props_with_dicts:
                return node_properties

            for original_prop in props_with_dicts:
                original_prop_prefix = original_prop + "_"

                # Find all keys that belong to this original_prop
                part_attr_keys = [key for key in node_properties if key.startswith(original_prop_prefix)]

                if not part_attr_keys:
                    continue

                original_prop_value = {key.removeprefix(original_prop_prefix): node_properties.pop(key) for key in part_attr_keys}
                node_properties[original_prop] = original_prop_value
            return node_properties

        def get_node_properties(node: Dict) -> Dict:
            return {key: value for key, value in node['properties'].items()}

        def create_list_of_dicts(*lists: List[List[any]], keys: List[str]) -> List[Dict]:
            if len(keys) != len(lists):
                raise ValueError("Number of keys must match number of input lists.")

            objs = [dict(zip(keys, values)) for values in zip(*lists)]
            return objs

        def add_relationships(node: Dict, node_dict: Dict, relationships: List[Dict]):
            # Sort relationships based on type and list entries by index
            sorted_relationships = sorted(
                relationships,
                key=lambda x: (
                    x.get("type"),  # Primary sort by type
                    x.get("properties", {}).get("value", {}).get("list_index", float("inf"))  # Secondary sort
                )
            )
            for rel in sorted_relationships:
                rel_type = rel['label']
                if rel['start']['id'] != node['id'] or rel_type in SPECIFIC_RELATIONSHIPS:
                        continue

                related_node = next(n for n in subgraph['nodes'] if n['id'] == rel['end']['id'])
                related_node_properties = get_node_properties(related_node)
                if "properties" in rel and "is_list" in rel['properties'] and rel['properties']["is_list"]:
                    node_dict.setdefault(rel_type, []).append(related_node_properties)
                    if "list_index" in rel['properties']:
                        list_index = rel['properties']["list_index"]
                        if len(node_dict[rel_type])-1 != list_index:
                            logger.warning(f"Index of the submodel element does not match with the saved index in the graph:"
                                           f"{len(node_dict[rel_type])-1} != {list_index}")
                            logger.warning(str(sorted_relationships))
                else:
                    node_dict[rel_type] = related_node_properties

                # Recursively process the related node if it has outgoing relationships
                add_relationships(related_node, related_node_properties,
                                  [r for r in subgraph['relationships'] if r['start']['id'] == related_node['id']])


                # Handle specific keys for certain node types
                related_node_properties = group_prefixed_props_back_to_list_of_dicts_prop(related_node['labels'], related_node_properties)
                related_node_properties = group_prefixed_props_back_to_dict_prop(related_node['labels'], related_node_properties)

        root_node = subgraph['nodes'][0]
        root_node_dict = get_node_properties(root_node)
        root_node_dict = group_prefixed_props_back_to_list_of_dicts_prop(root_node['labels'], root_node_dict)
        root_node_dict = group_prefixed_props_back_to_dict_prop(root_node['labels'], root_node_dict)
        add_relationships(root_node, root_node_dict,
                          [r for r in subgraph['relationships'] if r['start']['id'] == root_node['id']])
        return root_node_dict


def main():
    def optimized_upload_all_submodels(submodels_folder="examples/aas/test_dataset/"):
        # Use the OptimizedAASNeo4JClient for batch processing
        optimized_client = AASUploaderInNeo4J(uri="bolt://localhost:7687", user="neo4j", password="12345678")
        # optimized_client._truncate_db()
        optimized_client._remove_all_indexes_and_constraints()
        optimized_client.optimize_database()
        # set timer
        import time
        start_time = time.time()
        result = optimized_client.upload_all_aas_json_from_dir(submodels_folder, file_batch_size=100, db_batch_size=30000)
        end_time = time.time()
        print(f"Execution time: {end_time - start_time} seconds")

    def get_sm_from_neo4j():
        client = AASNeo4JClient(uri="bolt://localhost:7687", user="neo4j", password="12345678")
        sm = client.get_identifiable('https://smart.festo.com/sm/004/2dcd48b2-88a5-463a-9396-deaece98b4c9/')
        print(sm)


    logger.setLevel(logging.INFO)
    optimized_upload_all_submodels() # submodels_folder="examples/submodels/")


if __name__ == '__main__':
    main()
