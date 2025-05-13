from neo4j import GraphDatabase
import neo4j
from elasticsearch import Elasticsearch
from aas_mapping.aasjson2neo import AASNeo4JClient
from os import listdir
from os.path import isfile, join
from os import getenv
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def serialize_neo4j_node(record):
    doc = {
        "labels": record["labels"],
        "neo4j_id": record["id"]
    }

    for key, value in record["props"].items():
        if isinstance(value, (neo4j.time.Date, neo4j.time.DateTime)):
            doc[key] = str(value)
        else:
            doc[key] = value

    return doc


def serialize_neo4j_relationship(record):
    doc = {
        "type": record["type"],
        "source": record["source"],
        "target": record["target"]
    }
    return doc


class Neo4jElasticClient:

    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, elastic_url, cert_fingerprint, elastic_user, elastic_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.es_client = Elasticsearch(elastic_url,
                                        basic_auth=(elastic_user, elastic_password))

    def sync_to_elasticsearch(self):
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props")
                for record in result:
                    doc = serialize_neo4j_node(record)
                    self.es_client.index(index="neo4j_node", id=record["id"], document=doc)
                result = session.run(
                    "MATCH (a)-[r]->(b) RETURN id(r) AS id, type(r) AS type, id(a) AS source, id(b) AS target")
                for record in result:
                    doc = serialize_neo4j_relationship(record)
                    self.es_client.index(index="neo4j_relationship", id=record["id"], document=doc)
            logger.info("Data Synced to Elasticsearch!")
        except Exception as e:
            logger.error(f"Error syncing data to Elasticsearch: {e}")


def upload_neo4j_data(neo4j_uri, neo4j_user, neo4j_password):
    try:
        aas_neo4j_client = AASNeo4JClient(neo4j_uri, user=neo4j_user, password=neo4j_password)
        aas_neo4j_client.remove_all()

        submodel_path = "../aas_mapping/examples/submodels"
        files = [f for f in listdir(submodel_path) if isfile(join(submodel_path, f))]
        for file in files:
            aas_neo4j_client.upload_aas_json(join(submodel_path, file))
        logger.info("Data Uploaded to Neo4j!")
    except Exception as e:
        logger.warning(f"Error uploading data to Neo4j: {e}")


def main():
    load_dotenv()
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "password"

    ELASTIC_URL = getenv("ELASTIC_URL")
    CERT_FINGERPRINT = getenv("CERT_FINGERPRINT")
    ELASTIC_USER = getenv("ELASTIC_USER")
    ELASTIC_PASSWORD = getenv("ELASTIC_PASSWORD")

    neo4j_elastic_client = Neo4jElasticClient(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, ELASTIC_URL, CERT_FINGERPRINT, ELASTIC_USER, ELASTIC_PASSWORD)
    try:
        upload_neo4j_data(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print(neo4j_elastic_client.es_client.indices.exists(index=["neo4j_node", "neo4j_relationship"]))
        neo4j_elastic_client.es_client.indices.delete(index=["neo4j_node", "neo4j_relationship"], ignore=[400, 404])
        neo4j_elastic_client.sync_to_elasticsearch()
    finally:
        neo4j_elastic_client.driver.close()


if __name__ == "__main__":
    main()
