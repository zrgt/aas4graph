from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, jsonify

ELASTIC_PASSWORD = "PASSWORD"
CERT_FINGERPRINT = "CERT"


def format_response(response):
        results = []
        for hit in response.get("hits", {}).get("hits", []):
            results.append(hit)
        return results

class SearchApp:

    def __init__(self):
        self.client = Elasticsearch(
            "https://localhost:9200",
            ssl_assert_fingerprint=CERT_FINGERPRINT,
            basic_auth=("elastic", ELASTIC_PASSWORD),
        )

    def search_index(self, index, query, size):
        try:
            return self.client.search(index=index, query=query, size=size)
        except Exception as e:
            print(f"Fehler bei der Suche: {e}")
            return {"error": str(e)}
        

    def semantic_search(self, data, size):
        results = []
        responds = self.search_index("neo4j_node", {"match": {"keys_value": data}}, size+100)
        for r in responds.get("hits", {}).get("hits", []):
            if len(results) == size:
                break
            check = self.search_index(
                "neo4j_relationship",
                {
                    "bool": {
                        "must": [
                            {"match": {"type": "semanticId"}},
                            {"match": {"target": r["_source"]["neo4j_id"]}},
                        ]
                    }
                },
                size=1,
            )
            if check.get("hits", {}).get("total", {}).get("value", 0) == 1:
                ref = self.search_index(
                    "neo4j_node",
                    {"match": {"neo4j_id": check["hits"]["hits"][0]["_source"]["source"]}},
                    size=1,
                )
                if ref.get("hits", {}).get("total", {}).get("value", 0) == 1:
                    results.append(ref["hits"]["hits"][0])
        return results
    
    def description_search(self, data, size):
        results = []
        responds = self.search_index("neo4j_node", {"match": {"text": data}}, size+100)
        for r in responds.get("hits", {}).get("hits", []):
            if len(results) == size:
                break
            check = self.search_index(
                "neo4j_relationship",
                {
                    "bool": {
                        "must": [
                            {"match": {"type": "description"}},
                            {"match": {"target": r["_source"]["neo4j_id"]}},
                        ]
                    }
                },
                size=1,
            )
            if check.get("hits", {}).get("total", {}).get("value", 0) == 1:
                ref = self.search_index(
                    "neo4j_node",
                    {"match": {"neo4j_id": check["hits"]["hits"][0]["_source"]["source"]}},
                    size=1,
                )
                if ref.get("hits", {}).get("total", {}).get("value", 0) == 1:
                    results.append(ref["hits"]["hits"][0])
        return results

    def field_search(self, field, data, size):
        result = self.search_index(["neo4j_node", "neo4j_relationship"], {"match": {field: data}}, size)
        return format_response(result)

    def specific_value_search(self, data, size):
        result =  self.search_index(
            "neo4j_node",
            {
                "bool": {
                    "must": [
                        {"match": {"value": data}},
                        {"match": {"labels": "SubmodelElement"}},
                    ]
                }
            },
            size,
        )
        return format_response(result)


# Flask-Anwendung
app = Flask(__name__)
search_app = SearchApp()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    body = request.json
    value = body.get("main_query")
    field = body.get("secondary_query")
    size = int(body.get("searchSize", 10))
    free_field = body.get("freeField")

    try:
        match field:
            case "semanticId":
                return jsonify(search_app.semantic_search(value, size))
            case "description":
                return jsonify(search_app.description_search(value, size))
            case "id" | "idShort":
                return jsonify(search_app.field_search(field, value, size))
            case "values":
                return jsonify(search_app.specific_value_search(value, size))
            case "free":
                result = jsonify(search_app.field_search(free_field, value, size))
                return result
            case _:
                return jsonify({"error": "Ungültiges Feld"}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler bei der Verarbeitung der Anfrage: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
