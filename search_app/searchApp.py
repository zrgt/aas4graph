from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, jsonify
from os import getenv
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

ELASTIC_URL = getenv("ELASTIC_URL")
ELASTIC_USER = getenv("ELASTIC_USER")
ELASTIC_PASSWORD = getenv("ELASTIC_PASSWORD")


class SearchApp:
    def __init__(self, elastic_url, elastic_user, elastic_password):
        for i in range(5):
            try:
                self.client = Elasticsearch(
                    elastic_url,
                    basic_auth=(elastic_user, elastic_password),
                )
                return
            except Exception as e:
                logger.warning(f"Attempt {i + 1} failed: {e}")
                if i == 4:
                    raise ConnectionError("Could not connect to Elasticsearch after 5 attempts")

    def search_index(self, index, query, size, category=None, filtering=None):
        try:
            if category and filtering:
                query["bool"]["filter"] = {
                    "term": {f"{category}.keyword": filtering}
                }
            response = self.client.search(index=index, query=query, size=size)
            return response.get("hits", {}).get("hits", [])
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def advanced_search(self, catagory, data, size, category, filtering):
        results = []
        if category == "semanticId":
            nodes = self.search_index("neo4j_node", {"match": {"key_value": data}}, 10000)
        else:
            nodes = self.search_index("neo4j_node", {"match": {"text": data}}, 10000)
        for node in nodes:
            if len(results) >= size:
                break
            node_id = node["_source"]["neo4j_id"]
            rel_check = self.search_index("neo4j_relationship", {
                "bool": {"must": [{"match": {"type": catagory}}, {"match": {"target": node_id}}]}}, 1)
            if rel_check:
                ref = self.search_index("neo4j_node", {
                    "bool": {"must": {"match": {"neo4j_id": rel_check[0]["_source"].get("source")}}}}, 1, category,
                                        filtering)
                if ref:
                    results.append(ref[0])
        return results

    def description_search(self, data, size, category, filtering):
        return self.advanced_search("description", data, size, category, filtering)

    def semantic_search(self, data, size, category, filtering):
        return self.advanced_search("semanticId", data, size, category, filtering)

    def field_search(self, field, data, size, category=None, filtering=None):
        return self.search_index(["neo4j_node", "neo4j_relationship"], {"bool": {"must": {"match": {field: data}}}},
                                 size, category, filtering)

    def specific_value_search(self, data, size, category=None, filtering=None):
        return self.search_index("neo4j_node", {
            "bool": {"must": [{"match": {"value": data}}, {"term": {"labels.keyword": "SubmodelElement"}}]}}, size,
                                 category, filtering)


app = Flask(__name__)
search_app = SearchApp(ELASTIC_URL, ELASTIC_USER, ELASTIC_PASSWORD)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    try:
        body = request.json
        main_query = body.get("main_query")
        secondary_query = body.get("secondary_query")
        free_field = body.get("freeField")
        size = body.get("searchSize")
        if size == "":
            size = 10
        size = int(size)
        if size > 10000:
            size = 10000
        category = body.get("category")
        filtering = body.get("filter")

        match secondary_query:
            case "semanticId":
                return jsonify(search_app.semantic_search(main_query, size, category, filtering))
            case "description":
                return jsonify(search_app.description_search(main_query, size, category, filtering))
            case "id" | "idShort":
                return jsonify(search_app.field_search(secondary_query, main_query, size, category, filtering))
            case "values":
                return jsonify(search_app.specific_value_search(main_query, size, category, filtering))
            case "free":
                return jsonify(search_app.field_search(free_field, main_query, size, category, filtering))
            case _:
                return jsonify({"error": "Invalid field specified"}), 400
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0")
