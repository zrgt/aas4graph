import json

def translate_condition(condition, context):
    if "$eq" in condition:
        field, value = condition["$eq"]
        cypher_field = translate_field(field, context)
        cypher_value = translate_value(value, context)
        return f"{cypher_field} = {cypher_value}"
    elif "$gt" in condition:
        field, value = condition["$gt"]
        return f"{translate_field(field, context)} > {translate_value(value, context)}"
    elif "$lt" in condition:
        field, value = condition["$lt"]
        return f"{translate_field(field, context)} < {translate_value(value, context)}"
    elif "$contains" in condition:
        field = condition["$contains"][0]["$field"]
        value = condition["$contains"][1].get("$strVal")
        return f"{translate_field({'$field': field}, context)} CONTAINS '{value}'"
    elif "$and" in condition:
        return " AND ".join([translate_condition(cond, context) for cond in condition["$and"]])
    elif "$or" in condition:
        return " OR ".join([translate_condition(cond, context) for cond in condition["$or"]])
    elif "$match" in condition:
        return " AND ".join([translate_condition(cond, context) for cond in condition["$match"]])
    return ""

def translate_field(field, context):
    if isinstance(field, dict) and "$field" in field:
        field = field["$field"]

    if field == "$sm#idShort":
        return "sm0.idShort"
    elif field == "$aas#idShort":
        return "aas.idShort"
    elif field == "$aas#assetInformation.assetType":
        return "assetInformation.assetType"
    elif field == "$sme#semanticId":
        return "sme3.semanticId"
    elif field == "$sme#value":
        return "sme3.value"
    
    if field.startswith("$sme") or field.startswith("$sm"):
        context["paths"].add(field)
        parts = field.split(".")
        leaf = parts[-1]
        if "#" in leaf:
            attr = leaf.split("#")[-1]
        else:
            attr = "value"
        var_name = get_variable_from_field(field, context)
        if attr == "language":
            return "ls0.language"
        return f"{var_name}.{attr}"
    
    return field

def get_variable_from_field(field, context):
    # Extracts the last SubmodelElement name to use the right variable
    parts = field.split(".")
    for part in reversed(parts):
        if "#" not in part:
            idshort = part.replace("[]", "")
            return context["field_var_map"].get(idshort, "sme3")
    return "sme3"

def translate_value(value, context):
    if isinstance(value, dict):
        if "$numVal" in value:
            return str(value["$numVal"])
        elif "$strVal" in value:
            return f"'{value['$strVal']}'"
        elif "$field" in value:
            return translate_field(value, context)
    return str(value)

def generate_match_patterns(context):
    matches = set()
    for path in context["paths"]:
        parts = path.split(".")[1:]  # skip "$sme"
        var_chain = []
        parent = "sm0"
        for i, part in enumerate(parts):
            clean_part = part.replace("[]", "")
            if "#" in clean_part:
                clean_part = clean_part.split("#")[0]
            var = f"sme{i}"
            context["field_var_map"][clean_part] = var
            match = f"({parent})-[:child]->({var}:SubmodelElement {{idShort:'{clean_part}'}})"
            var_chain.append(match)
            parent = var
        matches.add(", ".join(var_chain))
    
    # Handle specific cases for language strings
    if any("language" in p for p in context["paths"]):
        matches.add("(mlp0)-[:value]->(ls0:LangString)")
    return "MATCH " + ",\n      ".join(matches)

def translate_aas_to_cypher(aas_query):
    context = {
        "paths": set(),
        "field_var_map": {}
    }

    # Special case (Query 1)
    condition = aas_query.get("$condition", {})
    if "$eq" in condition:
        eq_cond = condition["$eq"]
        if eq_cond[0].get("$field") == "$aas#idShort" and eq_cond[1].get("$field") == "$aas#assetInformation.assetType":
            return (
                "MATCH (aas:AssetAdministrationShell)-[:assetInformation]->(assetInformation)\n"
                "WHERE aas.idShort = assetInformation.assetType\n"
                "RETURN aas"
            )

    where_clause = translate_condition(aas_query.get("$condition", {}), context)
    match_clause = generate_match_patterns(context)

    return f"""{match_clause}
WHERE {where_clause}
RETURN sm0"""

# Example usage with one of your queries:
if __name__ == "__main__":
    examples = [
        {
            "$condition": {
                "$eq": [
                    {"$field": "$aas#idShort"},
                    {"$field": "$aas#assetInformation.assetType"}
                ]
            }
        },
        {
            "$condition": {
                "$match": [
                    {"$eq": [{"$field": "$sme.FileVersion[].FileVersionId#value"}, {"$strVal": "1.1"}]},
                    {"$eq": [{"$field": "$sme.FileVersion[].FileName#value"}, {"$strVal": "SomeFile"}]}
                ]
            }
        },
        {
            "$condition": {
                "$match": [
                    {"$eq": [{"$field": "$sme.Documents[].DocumentClassification.Class#value"}, {"$strVal": "03-01"}]},
                    {"$eq": [{"$field": "$sme.Documents[].DocumentVersion.SMLLanguages[]#language"}, {"$strVal": "nl"}]}
                ]
            }
        },
        {
            "$condition": {
                "$and": [
                    {"$match": [
                        {"$eq": [{"$field": "$sm#idShort"}, {"$strVal": "TechnicalData"}]},
                        {"$eq": [{"$field": "$sme.ProductClassifications.ProductClassificationItem.ProductClassId#value"}, {"$strVal": "27-37-09-05"}]}
                    ]},
                    {"$match": [
                        {"$eq": [{"$field": "$sm#idShort"}, {"$strVal": "TechnicalData"}]},
                        {"$eq": [{"$field": "$sme#semanticId"}, {"$strVal": "0173-1#02-BAF016#006"}]},
                        {"$lt": [{"$field": "$sme#value"}, {"$numVal": 100}]}
                    ]}
                ]
            }
        }
    ]

    for i, ex in enumerate(examples, 1):
        print(f"\n--- Query {i} ---")
        print(translate_aas_to_cypher(ex))
