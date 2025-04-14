import json
import re

# ─────────────────────────────────────────────────────────────
# Helper: parse a field path string into its parts
# ─────────────────────────────────────────────────────────────
def parse_field_path(field_str):
    """
    Parses a field string like:
      "$sme.FileVersion[].FileVersionId#value"
    into a tuple (prefix, segments) where:
      - prefix is either "sme" or "sm"
      - segments is a list of dicts with keys:
           "name": (e.g., "FileVersion"),
           "array": (True if [] is present),
           "prop": (e.g., "value" from "#value"; if missing, defaults to None)
    For fields without a dot (e.g. "$sme#semanticId") the segment has no name.
    """
    if field_str.startswith("$sme."):
        prefix = "sme"
        remaining = field_str[len("$sme."):]
    elif field_str.startswith("$sme#"):
        prefix = "sme"
        remaining = field_str[len("$sme#"):]
    elif field_str.startswith("$sm."):
        prefix = "sm"
        remaining = field_str[len("$sm."):]
    elif field_str.startswith("$sm#"):
        prefix = "sm"
        remaining = field_str[len("$sm#"):]
    else:
        prefix = ""
        remaining = field_str

    segments = []
    if remaining:
        parts = remaining.split('.')
        for part in parts:
            # Check for array marker "[]" (can appear together with a property indicator)
            is_array = "[]" in part
            part = part.replace("[]", "")
            if "#" in part:
                name, prop = part.split("#", 1)
            else:
                name, prop = part, None
            segments.append({"name": name if name else None, "array": is_array, "prop": prop})
    else:
        # if nothing remains, treat it as a property-only segment
        segments.append({"name": None, "array": False, "prop": remaining})
    return prefix, segments

# ─────────────────────────────────────────────────────────────
# MATCH Pattern Builder class
# ─────────────────────────────────────────────────────────────
class MatchPatternBuilder:
    def __init__(self, context):
        self.context = context
        self.context.setdefault("clauses", [])
        self.context.setdefault("var_counter", {"sme": 0, "mlp": 0, "ls": 0})
        self.registered = {}
        self.sm0_labeled = False

    def get_next_var(self, prefix):
        count = self.context["var_counter"].get(prefix, 0)
        self.context["var_counter"][prefix] = count + 1
        # if prefix == "sme" and count == 0:
        #     return "sme"
        return f"{prefix}{count}"

    def register_chain(self, field_str):
        if field_str in self.registered:
            return self.registered[field_str]

        prefix, segments = parse_field_path(field_str)

        current_var = "sm0"
        prev_was_array = False

        for i, seg in enumerate(segments):
            is_last = (i == len(segments) - 1)

            # Choose rel type
            if seg["name"]:
                rel = "[:child]"
            else:
                rel = "[:child*0..]"

            # Apply label inline on first use of sm0
            if current_var == "sm0" and not self.sm0_labeled:
                current_var = "sm0:Submodel"
                self.sm0_labeled = True

            # If previous was array, insert an intermediate node
            if prev_was_array:
                inter_var = self.get_next_var("sme")
                self.context["clauses"].append(f"({current_var})-[:child]->({inter_var}:SubmodelElement)")
                current_var = inter_var
                prev_was_array = False

            if seg["prop"] == "language" and is_last:
                mlp_var = self.get_next_var("mlp")
                ls_var = self.get_next_var("ls")
                self.context["clauses"].append(
                    f"({current_var})-[:child]->({mlp_var}:MultiLanguageProperty {{idShort: \"{seg['name']}\"}})"
                )
                self.context["clauses"].append(f"({mlp_var})-[:value]->({ls_var}:LangString)")
                current_var = ls_var
            elif seg["name"]:
                next_var = self.get_next_var("sme")
                clause = f"({current_var})-{rel}->({next_var}:SubmodelElement {{idShort: \"{seg['name']}\"}})"
                self.context["clauses"].append(clause)
                current_var = next_var
            else:
                next_var = self.get_next_var("sme")
                clause = f"({current_var})-{rel}->({next_var}:SubmodelElement)"
                self.context["clauses"].append(clause)
                current_var = next_var

            prev_was_array = seg["array"]

        self.registered[field_str] = current_var
        return current_var

    def generate(self):
        if self.context["clauses"]:
            unique_clauses = list(dict.fromkeys(self.context["clauses"]))
            return "MATCH " + ",\n      ".join(unique_clauses)
        return ""

# ─────────────────────────────────────────────────────────────
# Field Translator uses the match builder to determine the final node
# ─────────────────────────────────────────────────────────────
class FieldTranslator:
    def __init__(self, context, match_builder):
        self.context = context
        self.match_builder = match_builder

    def translate(self, field):
        # Expecting field as a dict like { "$field": "$sme.Material#value" }
        if isinstance(field, dict) and "$field" in field:
            field_str = field["$field"]
        else:
            field_str = field

        final_var = self.match_builder.register_chain(field_str)

        # Get property from last segment
        _, segments = parse_field_path(field_str)
        prop = segments[-1]["prop"] if segments[-1]["prop"] else "value"

        return f"{final_var}.{prop}"

# ─────────────────────────────────────────────────────────────
# Condition Translator
# ─────────────────────────────────────────────────────────────
class ConditionTranslator:
    def __init__(self, context, match_builder):
        self.context = context
        self.field_translator = FieldTranslator(context, match_builder)

    def translate(self, condition):
        if "$eq" in condition:
            field, value = condition["$eq"]
            return f"{self.field_translator.translate(field)} = {self.translate_value(value)}"
        elif "$ne" in condition:
            field, value = condition["$ne"]
            return f"{self.field_translator.translate(field)} <> {self.translate_value(value)}"
        elif "$gt" in condition:
            field, value = condition["$gt"]
            return f"{self.field_translator.translate(field)} > {self.translate_value(value)}"
        elif "$lt" in condition:
            field, value = condition["$lt"]
            return f"{self.field_translator.translate(field)} < {self.translate_value(value)}"
        elif "$ge" in condition:
            field, value = condition["$ge"]
            return f"{self.field_translator.translate(field)} >= {self.translate_value(value)}"
        elif "$le" in condition:
            field, value = condition["$le"]
            return f"{self.field_translator.translate(field)} <= {self.translate_value(value)}"
        elif "$contains" in condition:
            # For $contains, the second operand is expected to be a string value.
            field_obj = condition["$contains"][0]
            value_obj = condition["$contains"][1]
            return f"{self.field_translator.translate(field_obj)} CONTAINS {self.translate_value(value_obj)}"
        elif "$and" in condition:
            return " AND ".join([self.translate(cond) for cond in condition["$and"]])
        elif "$or" in condition:
            return " OR ".join([self.translate(cond) for cond in condition["$or"]])
        elif "$match" in condition:
            return " AND ".join([self.translate(cond) for cond in condition["$match"]])
        elif "$regex" in condition:
            field, value = condition["$regex"]
            return f"{self.field_translator.translate(field)} =~ {self.translate_value(value)}"
        elif "$starts-with" in condition:
            field, value = condition["$starts-with"]
            return f"{self.field_translator.translate(field)} STARTS WITH {self.translate_value(value)}"
        return ""

    def translate_value(self, value):
        if isinstance(value, dict):
            if "$numVal" in value:
                return str(value["$numVal"])
            elif "$strVal" in value:
                return f"'{value['$strVal']}'"
            elif "$field" in value:
                return self.field_translator.translate(value)
        return str(value)

# ─────────────────────────────────────────────────────────────
# AAS Query Translator (ties all the pieces together)
# ─────────────────────────────────────────────────────────────
class AASQueryTranslator:
    def __init__(self, aas_query):
        self.aas_query = aas_query
        self.context = {}
        self.match_builder = MatchPatternBuilder(self.context)

    def translate(self):
        condition = self.aas_query.get("$condition", {})
        cond_translator = ConditionTranslator(self.context, self.match_builder)
        where_clause = cond_translator.translate(condition)
        match_clause = self.match_builder.generate()
        return f"""{match_clause}
WHERE {where_clause}
RETURN sm0"""