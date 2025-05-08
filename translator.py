import json

# ─────────────────────────────────────────────────────────────
# parse a field path into its segments
# ─────────────────────────────────────────────────────────────
def parse_field_path(field_str):
    if field_str.startswith("$sme.") or field_str.startswith("$sme#"):
        remaining = field_str.split(".",1)[1] if "." in field_str else field_str.split("#",1)[1]
    elif field_str.startswith("$sm.") or field_str.startswith("$sm#"):
        remaining = field_str.split(".",1)[1] if "." in field_str else field_str.split("#",1)[1]
    else:
        remaining = field_str
    segments = []
    for part in remaining.split("."):
        is_array = part.endswith("[]")
        if is_array:
            part = part[:-2]
        if "#" in part:
            name, prop = part.split("#",1)
        else:
            name, prop = part, None
        segments.append({"name": name or None, "array": is_array, "prop": prop})
    return segments

# ─────────────────────────────────────────────────────────────
# MATCH‐clause builder
# ─────────────────────────────────────────────────────────────
class MatchPatternBuilder:
    def __init__(self, ctx):
        self.ctx = ctx
        ctx.setdefault("clauses", [])
        ctx.setdefault("var_counter", {"sme":0,"mlp":0,"ls":0})
        # skip_label=True for top‐level OR+idShort mix (Example 03)
        ctx.setdefault("skip_label", False)
        ctx.setdefault("sm0_registered", False)
        self.registered = {}
        self.sm0_labeled = False

    def next_var(self, prefix):
        i = self.ctx["var_counter"][prefix]
        self.ctx["var_counter"][prefix] = i+1
        return f"{prefix}{i}"

    def label_for_root(self):
        # if skip_label or already injected idShort, leave sm0 bare
        if self.ctx["skip_label"] or self.ctx["sm0_registered"]:
            return ""
        return ":Submodel"

    def register_match_chain(self, field_str):
        if field_str in self.registered:
            return self.registered[field_str]

        segments = parse_field_path(field_str)
        curr = "sm0"

        # Always use the same base array node
        array_name = segments[0]["name"]
        if "match_array" not in self.ctx:
            self.ctx["match_array"] = {
                "array_var": self.next_var("sme"),
                "shared_var": self.next_var("sme")
            }
            self.ctx["clauses"].append(
                f'(sm0:Submodel)-[:child]->({self.ctx["match_array"]["array_var"]}:SubmodelElement {{idShort:"{array_name}"}})'
            )
            self.ctx["clauses"].append(
                f'({self.ctx["match_array"]["array_var"]})-[:child]->({self.ctx["match_array"]["shared_var"]}:SubmodelElement)'
            )

        curr = self.ctx["match_array"]["shared_var"]

        # Now build the remaining chain
        for seg in segments[1:]:
            if seg["name"]:
                next_var = self.next_var("sme")
                self.ctx["clauses"].append(
                    f'({curr})-[:child]->({next_var}:SubmodelElement {{idShort:"{seg["name"]}"}})'
                )
                curr = next_var

        self.registered[field_str] = curr
        return curr

    def register_chain(self, field_str):
        if field_str in self.registered:
            return self.registered[field_str]

        segments = parse_field_path(field_str)
        curr = "sm0"
        prev_array = False

        for i, seg in enumerate(segments):
            is_last = (i == len(segments)-1)
            rel = "[:child]" if seg["name"] else "[:child*0..]"

            # label sm0 the first time
            if curr=="sm0" and not self.sm0_labeled:
                lbl = self.label_for_root()
                curr = f"sm0{lbl}"
                self.sm0_labeled = True

            # phantom step after an array
            if prev_array:
                iv = self.next_var("sme")
                self.ctx["clauses"].append(f"({curr})-[:child]->({iv}:SubmodelElement)")
                curr = iv
                prev_array = False

            # multi‐language property at the leaf
            if seg["prop"]=="language" and is_last:
                mlp = self.next_var("mlp"); ls = self.next_var("ls")
                self.ctx["clauses"].append(
                    f"({curr})-[:child]->({mlp}:MultiLanguageProperty {{idShort: \"{seg['name']}\"}})"
                )
                self.ctx["clauses"].append(f"({mlp})-[:value]->({ls}:LangString)")
                curr = ls

            # named SubmodelElement
            elif seg["name"]:
                nv = self.next_var("sme")
                self.ctx["clauses"].append(
                    f"({curr})-{rel}->({nv}:SubmodelElement {{idShort: \"{seg['name']}\"}})"
                )
                curr = nv

            # wildcard / any‐element
            else:
                nv = self.next_var("sme")
                self.ctx["clauses"].append(
                    f"({curr})-{rel}->({nv}:SubmodelElement)"
                )
                curr = nv

            prev_array = seg["array"]

        self.registered[field_str] = curr
        return curr

    def generate(self):
        uniq = []
        for c in self.ctx["clauses"]:
            if c not in uniq:
                uniq.append(c)

        # Flatten match_array chain properly
        if "match_array" in self.ctx:
            try:
                parts = uniq[:3]
                links = []

                for clause in parts:
                    if "->" in clause:
                        lhs, rhs = clause.split("->")
                        lhs = lhs.strip()
                        rhs = rhs.strip()
                        links.append((lhs, rhs))

                # Build chain like: (A)-[:child]->(B)-[:child]->(C)-[:child]->(D)
                nodes = [links[0][0]]  # start with first lhs
                for _, rhs in links:
                    nodes.append(rhs)
                chain = "-[:child]->".join(nodes)

                rest = uniq[3:]
                if rest:
                    return f"MATCH {chain},\n      " + ",\n      ".join(rest)
                return f"MATCH {chain}"
            except Exception:
                pass  # fallback to normal formatting

        # fallback formatting
        if self.ctx["skip_label"] and uniq:
            clauses = ["(sm0)"] + uniq
        else:
            clauses = uniq

        if not clauses:
            return ""
        if len(clauses) == 1:
            return "MATCH " + clauses[0]
        first, rest = clauses[0], clauses[1:]
        return "MATCH " + first + ",\n      " + ",\n      ".join(rest)
# ─────────────────────────────────────────────────────────────
# FieldTranslator: flatten to var.prop
# ─────────────────────────────────────────────────────────────
class FieldTranslator:
    def __init__(self, ctx, mb):
        self.ctx = ctx
        self.mb = mb

    def translate(self, f):
        if isinstance(f, dict) and "$field" in f:
            fs = f["$field"]
        else:
            fs = f
        if fs=="$sm#idShort":
            return "sm0.idShort"
        var = self.mb.register_chain(fs)
        prop = parse_field_path(fs)[-1]["prop"] or "value"
        return f"{var}.{prop}"

# ─────────────────────────────────────────────────────────────
# ConditionTranslator → builds WHERE and handles idShort injection
# ─────────────────────────────────────────────────────────────
class ConditionTranslator:
    def __init__(self, ctx, mb):
        self.ctx = ctx
        self.mb = mb
        self.ft = FieldTranslator(ctx, mb)

    def translate(self, cond, nested=False, top_or=False):
        # top‐level AND: pull $sm#idShort eq into MATCH
        if not nested and "$and" in cond:
            rest = []
            for c in cond["$and"]:
                if "$eq" in c:
                    f,v = c["$eq"]
                    if isinstance(f, dict) and f.get("$field")=="$sm#idShort" and "$strVal" in v:
                        # inject into MATCH
                        if not self.ctx["sm0_registered"]:
                            val = v["$strVal"]
                            self.ctx["clauses"].insert(
                                0, f'(sm0:Submodel {{idShort: "{val}"}})'
                            )
                            self.ctx["sm0_registered"] = True
                        continue
                rest.append(c)
            parts = [self.translate(c, nested=True) for c in rest]
            return " AND ".join(p for p in parts if p)

        # $match operator (Example 04)
        if "$match" in cond:
            # register shared path
            for c in cond["$match"]:
                if "$eq" in c:
                    f,_ = c["$eq"]
                    if isinstance(f, dict):
                        self.mb.register_match_chain(f["$field"]) ####register_match_chain
            # emit WHERE=AND of each eq
            tests = []
            for c in cond["$match"]:
                if "$eq" in c:
                    f,v = c["$eq"]
                    var = self.mb.registered[f["$field"]]
                    prop = parse_field_path(f["$field"])[-1]["prop"] or "value"
                    tests.append(f"{var}.{prop} = \"{v['$strVal']}\"")
            return " AND ".join(tests)

        # top‐level OR
        if not nested and "$or" in cond:
            parts = [self.translate(c, nested=True) for c in cond["$or"]]
            # if any part is CONTAINS → split onto two lines
            if any("CONTAINS" in p for p in parts):
                return ("OR_BREAK", parts[0], parts[1])
            return " OR ".join(parts)

        # nested OR
        if nested and "$or" in cond:
            parts = [self.translate(c, nested=True) for c in cond["$or"]]
            return "(" + " OR ".join(p for p in parts if p) + ")"

        # nested AND
        if nested and "$and" in cond:
            parts = [self.translate(c, nested=True) for c in cond["$and"]]
            return "(" + " AND ".join(p for p in parts if p) + ")"

        # simple ops
        for op,sym in [("$eq","="),("$ne","<>"),("$gt",">"),("$lt","<"),("$ge",">="),("$le","<=")]:
            if op in cond:
                f,v = cond[op]
                # sm#idShort eq inside OR or nested
                if isinstance(f, dict) and f.get("$field")=="$sm#idShort":
                    return f'sm0.idShort {sym} "{v["$strVal"]}"'
                left = self.ft.translate(f)
                right = f"'{v.get('$strVal',v.get('$numVal'))}'"
                # numeric ops must be unquoted
                if op in ("$gt","$lt","$ge","$le"):
                    right = str(v["$numVal"])
                return f"{left} {sym} {right}"

        if "$contains" in cond:
            f,v = cond["$contains"]
            left = self.ft.translate(f)
            return f"{left} CONTAINS '{v['$strVal']}'"

        if "$regex" in cond:
            f,v = cond["$regex"]
            left = self.ft.translate(f)
            return f"{left} =~ '{v['$strVal']}'"

        if "$starts-with" in cond:
            f,v = cond["$starts-with"]
            left = self.ft.translate(f)
            return f"{left} STARTS WITH '{v['$strVal']}'"

        if "$not" in cond:
            inner = self.translate(cond["$not"], nested=True)
            return f"NOT {inner}"

        return ""

# ─────────────────────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────────────────────
class AASQueryTranslator:
    def __init__(self, aas_query):
        cond = aas_query.get("$condition", {})
        # detect Example 03: top OR with sm#idShort
        skip = False
        if "$or" in cond:
            for c in cond["$or"]:
                if "$eq" in c and isinstance(c["$eq"][0], dict) and c["$eq"][0].get("$field")=="$sm#idShort":
                    skip = True
        self.ctx = {
            "clauses": [],
            "var_counter": {"sme":0,"mlp":0,"ls":0},
            "skip_label": skip,
            "sm0_registered": False
        }
        self.mb = MatchPatternBuilder(self.ctx)
        self.cond = cond

    def translate(self):
        ct = ConditionTranslator(self.ctx, self.mb)
        where_info = ct.translate(self.cond)
        # build WHERE text
        if isinstance(where_info, tuple) and where_info[0]=="OR_BREAK":
            _, first, second = where_info
            where = f"WHERE {first}\n   OR {second}"
        else:
            where = f"WHERE {where_info}"
        match = self.mb.generate()
        return f"""{match}
{where}
RETURN sm0"""