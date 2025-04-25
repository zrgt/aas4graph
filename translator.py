import json
import re

# ─────────────────────────────────────────────────────────────
# Helper: parse a field path string into its parts
# ─────────────────────────────────────────────────────────────
def parse_field_path(field_str):
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
            is_array = "[]" in part
            part = part.replace("[]", "")
            if "#" in part:
                name, prop = part.split("#", 1)
            else:
                name, prop = part, None
            segments.append({"name": name if name else None, "array": is_array, "prop": prop})
    else:
        segments.append({"name": None, "array": False, "prop": remaining})
    return prefix, segments

# ─────────────────────────────────────────────────────────────
# MATCH Pattern Builder
# ─────────────────────────────────────────────────────────────
class MatchPatternBuilder:
    def __init__(self, context):
        self.context = context
        self.context.setdefault("clauses", [])
        self.context.setdefault("var_counter", {"sme": 0, "mlp": 0, "ls": 0})
        self.registered = {}
        self.sm0_labeled = False
        self.match_groups = {}  # Add this to track match groups

    def get_next_var(self, prefix):
        count = self.context["var_counter"].get(prefix, 0)
        self.context["var_counter"][prefix] = count + 1
        return f"{prefix}{count}"

    def register_chain(self, field_str):
        if field_str in self.registered:
            return self.registered[field_str]

        prefix, segments = parse_field_path(field_str)

        current_var = "sm0"
        prev_was_array = False

        for i, seg in enumerate(segments):
            is_last = (i == len(segments) - 1)
            if seg["name"]:
                rel = "[:child]"
            else:
                rel = "[:child*0..]"

            if current_var == "sm0" and not self.sm0_labeled:
                if not any("sm0:Submodel" in clause and "idShort" in clause for clause in self.context["clauses"]):
                    current_var = "sm0:Submodel"
                else:
                    current_var = "sm0"
                self.sm0_labeled = True

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

    def register_match_chain(self, field_str, match_group=None):
        """Special handling for $match operator chains"""
        if field_str in self.registered and match_group:
            return self.registered[field_str]

        prefix, segments = parse_field_path(field_str)
        current_var = "sm0"
        
        # Handle the first segment (array part)
        if segments[0]["name"]:
            if match_group and segments[0]["name"] in self.match_groups:
                # Use existing array element variable
                current_var = self.match_groups[segments[0]["name"]]
            else:
                # Create new array element variable
                array_var = self.get_next_var("sme")
                self.context["clauses"].append(
                    f'({current_var})-[:child]->({array_var}:SubmodelElement {{idShort:"{segments[0]["name"]}"}})'
                )
                if match_group:
                    self.match_groups[segments[0]["name"]] = array_var
                current_var = array_var

                # Create shared array element variable
                shared_var = self.get_next_var("sme")
                self.context["clauses"].append(
                    f"({current_var})-[:child]->({shared_var}:SubmodelElement)"
                )
                current_var = shared_var
                if match_group:
                    self.match_groups["shared"] = shared_var

        # Handle remaining segments
        for seg in segments[1:]:
            if seg["name"]:
                next_var = self.get_next_var("sme")
                self.context["clauses"].append(
                    f'({current_var})-[:child]->({next_var}:SubmodelElement {{idShort:"{seg["name"]}"}})'
                )
                current_var = next_var

        self.registered[field_str] = current_var
        return current_var

    def generate(self):
        if self.context["clauses"]:
            unique_clauses = list(dict.fromkeys(self.context["clauses"]))
            return "MATCH " + ",\n      ".join(unique_clauses)
        return ""

# ─────────────────────────────────────────────────────────────
# Field Translator
# ─────────────────────────────────────────────────────────────
class FieldTranslator:
    def __init__(self, context, match_builder):
        self.context = context
        self.match_builder = match_builder

    def translate(self, field):
        if isinstance(field, dict) and "$field" in field:
            field_str = field["$field"]
        else:
            field_str = field

        if field_str == "$sm#idShort":
            if not self.context.get("sm0_registered"):
                # If we already have custom idShort match, skip adding plain sm0:Submodel
                existing_clauses = self.context.get("clauses", [])
                if not any("sm0:Submodel" in clause and "idShort" in clause for clause in existing_clauses):
                    self.context["clauses"].insert(0, "(sm0:Submodel)")
                self.context["sm0_registered"] = True
            return "sm0.idShort"

        final_var = self.match_builder.register_chain(field_str)

        _, segments = parse_field_path(field_str)
        prop = segments[-1]["prop"] if segments[-1]["prop"] else "value"

        return f"{final_var}.{prop}"

# ─────────────────────────────────────────────────────────────
# Condition Translator
# ─────────────────────────────────────────────────────────────
class ConditionTranslator:
    def __init__(self, context, match_builder):
        self.context = context
        self.match_builder = match_builder
        self.field_translator = FieldTranslator(context, match_builder)
        self.match_group_counter = 0

    def translate(self, condition, nested=False):
        if "$match" in condition:
            self.match_group_counter += 1
            match_group = f"match_{self.match_group_counter}"
            parts = []
            for match_condition in condition["$match"]:
                part = self.translate(match_condition, nested=True)
                if part:
                    parts.append(part)
            
            # Register all fields with the same match group
            for match_condition in condition["$match"]:
                if "$eq" in match_condition:
                    field = match_condition["$eq"][0]
                    if isinstance(field, dict) and "$field" in field:
                        self.match_builder.register_match_chain(field["$field"], match_group)

            return " AND ".join(parts) if parts else ""
        if "$eq" in condition:
            field, value = condition["$eq"]
            if isinstance(field, dict) and field.get("$field") == "$sm#idShort" and "$strVal" in value:
                idshort_value = value["$strVal"]
                if not self.context.get("sm0_registered"):
                    self.context["clauses"].insert(0, f'(sm0:Submodel {{idShort:"{idshort_value}"}})')
                    self.context["sm0_registered"] = True
                return ""
            else:
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
            field_obj = condition["$contains"][0]
            value_obj = condition["$contains"][1]
            return f"{self.field_translator.translate(field_obj)} CONTAINS {self.translate_value(value_obj)}"
        elif "$regex" in condition:
            field, value = condition["$regex"]
            return f"{self.field_translator.translate(field)} =~ {self.translate_value(value)}"
        elif "$starts-with" in condition:
            field, value = condition["$starts-with"]
            return f"{self.field_translator.translate(field)} STARTS WITH {self.translate_value(value)}"
        elif "$not" in condition:
            inner = self.translate(condition["$not"], nested=True)
            return f"NOT {inner}"
        elif "$and" in condition:
            parts = [self.translate(c, nested=True) for c in condition["$and"]]
            parts = [p for p in parts if p]  # Filter empty
            if not parts:
                return ""
            joined = " AND ".join(parts)
            return f"({joined})" if nested else joined
        elif "$or" in condition:
            parts = [self.translate(c, nested=True) for c in condition["$or"]]
            parts = [p for p in parts if p]
            if not parts:
                return ""
            joined = " OR ".join(parts)
            return f"({joined})" if nested else joined
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
# AAS Query Translator
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
