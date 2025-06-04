import datetime
import re

class AASQuery2Cypher:
    """
    AASQuery2Cypher is a class that converts AAS queries into Cypher queries.

    It contains the following methods:
    """

    logical_operations = {"$and", "$or", "$not"}
    match_operations = {"$match"}

    comparison_operations = {"$eq", "$ne", "$lt", "$le", "$gt", "$ge"}
    string_operations = {"contains", "starts-with", "ends-with", "regex"}

    casting_operands = {"$strCast", "$numCast", "$hexCast", "$boolCast", "$dateTimeCast", "$timeCast"}
    value_operands = {"$strVal", "$numVal", "$hexVal", "$dateTimeVal", "$timeVal", "$dayOfWeek", "$dayOfMonth", "$month", "$year"}
    field_operands = {"$field"}

    value_to_casting = {
        "$strVal": "$strCast",
        "$numVal": "$numCast",
        "$hexVal": "$hexCast",
        "$dateTimeVal": "$dateTimeCast",
        "$timeVal": "$timeCast",
        "$dayOfWeek": "$numCast",
        "$dayOfMonth": "$numCast",
        "$month": "$numCast",
        "$year": "$numCast"
    }

    comparison_operations_to_cypher = {
        "$eq": "=",
        "$ne": "<>",
        "$lt": "<",
        "$le": "<=",
        "$gt": ">",
        "$ge": ">="
    }

    string_operations_to_cypher = {
        "contains": "CONTAINS",
        "starts-with": "STARTS WITH",
        "ends-with": "ENDS WITH",
        "regex": "=~"
    }

    def __init__(self, aas_json_query: dict):
        self.aas_json_query = aas_json_query
        self.cypher_query = ""

        self.match_clauses = set()
        self.where_clauses = []
        self.return_clauses = []

        self.aas_vars = {}
        self.sm_vars = {}
        self.sme_vars = {}
        self.cd_vars = {}
        self.semantic_id_vars = {}

    @property
    def vars(self):
        """
        Get all variables used in the query.
        """
        return {**self.aas_vars, **self.sm_vars, **self.sme_vars, **self.cd_vars}

    def convert(self):
        """
        Convert the AAS query to a Cypher query.
        """
        condition = self.aas_json_query.get("$condition")
        condition_type = list(condition.keys())[0]
        if condition_type in self.logical_operations:
            self._convert_logical_operation(condition)
        elif condition_type in self.match_operations:
            self._convert_match_operation(condition)
        elif condition_type in self.comparison_operations or condition_type in self.string_operations:
            self._convert_comparison_or_string_operation(condition)
        else:
            raise ValueError(f"Unsupported operation: {condition_type}")
        return self.cypher_query

    def _convert_logical_operation(self, condition: dict):
        pass

    def _convert_match_operation(self, condition: dict):
        pass

    def _convert_comparison_or_string_operation(self, condition: dict):
        """
        Build the Cypher query for a given operation.

        EXAMPLE:
           {
            "$eq": [
              { "$field": "$sm#idShort" },
              { "$strVal": "TechnicalData" }
            ]
          }
        """
        operands: list
        operation, operands = condition.popitem()
        operand_type_0, operand_val_0 = operands[0].popitem()
        operand_type_1, operand_val_1 = operands[1].popitem()

        comparison_cypher_operator = self._convert_comparison_operator(operation)

        cypher_operand_0, cypher_match_clause_0 = self._convert_comparison_operand(operand_type_0, operand_val_0)
        cypher_operand_1, cypher_match_clause_1 = self._convert_comparison_operand(operand_type_1, operand_val_1)

        if cypher_operand_0.endswith("[]"):
            # One operand is a list, operator is "IN" or "CONTAINS" or ...
            # TODO: Implement logic for list operands
            pass
        elif cypher_operand_1.endswith("[]"):
            pass

        if cypher_match_clause_0 is None or cypher_match_clause_1 is None:
            # One operand is a value, the other is a field
            if cypher_match_clause_0:
                self.match_clauses.add(cypher_match_clause_0)
            if cypher_match_clause_1:
                self.match_clauses.add(cypher_match_clause_1)
        elif cypher_match_clause_0 and cypher_match_clause_1:
            # Both operands are fields
            self._merge_match_clauses(cypher_match_clause_0, cypher_match_clause_1)

        comparison = f"{cypher_operand_0} {comparison_cypher_operator} {cypher_operand_1}".format(**self.vars)

    def _convert_comparison_operator(self, operator: str) -> str:
        """
        Convert a comparison operator to Cypher equivalent.
        """
        if operator in self.comparison_operations:
            cypher_operator = self.comparison_operations_to_cypher[operator]
        elif operator in self.string_operations:
            cypher_operator = self.string_operations_to_cypher[operator]
        else:
            raise ValueError(f"Unsupported comparison operator: {operator}")
        return cypher_operator

    def _convert_comparison_operand(self, operand_type: str, operand_val: [str, dict]) -> tuple[str, [None, str]]:
        """
        Convert an operand to Cypher equivalent.
        """
        if operand_type in self.value_operands:
            cypher_operand = self._convert_comparison_value_operand(operand_type, operand_val)
            return cypher_operand, None
        elif operand_type in self.casting_operands:
            cypher_operand, match_pattern = self._convert_comparison_cast_operand(operand_type, operand_val)
            return cypher_operand, match_pattern
        elif operand_type in self.field_operands:
            cypher_operand, match_pattern, variables = self._convert_field_operand(operand_type, operand_val)
            return cypher_operand, match_pattern

    def _convert_comparison_value_operand(self, operand_type: str, operand_val: str) -> str:
        if operand_type == "$strVal":
            return f"'{operand_val}'"
        elif operand_type in ("$numVal", "$hexVal"):
            return str(operand_val)
        elif operand_type == "$boolVal":
            return 'true' if operand_val else 'false'
        elif operand_type == "$dateTimeVal":
            return f"'datetime({operand_val})'"
        elif operand_type == "$timeVal":
            return f"'time({operand_val})'"
        elif operand_type in ("$dayOfWeek", "$dayOfMonth", "$month", "$year"):
            # Assuming operand_val is a date or datetime isoformat string
            datetime_obj = datetime.datetime.fromisoformat(operand_val)
            if operand_type == "$dayOfWeek":
                return str(datetime_obj.weekday())
            elif operand_type == "$dayOfMonth":
                return str(datetime_obj.day)
            elif operand_type == "$month":
                return str(datetime_obj.month)
            elif operand_type == "$year":
                return str(datetime_obj.year)
        else:
            raise ValueError(f"Unsupported operand type: {operand_type}")

    def _convert_comparison_cast_operand(self, operand_type: str, operand_val: [str, dict]) -> tuple[str, str]:
        pass
        # TODO: Implement casting logic, after clarification of the casting operations
        raise NotImplementedError(f"Unsupported operand type: {operand_type}")
        # elif operand_type == "$strCast":
        #     return f"'{operand_val}'"
        # elif operand_type == "$numCast":
        #     return str(operand_val)
        # elif operand_type == "$hexCast":
        #     return f"'{operand_val}'"
        # elif operand_type == "$boolCast":
        #     return 'true' if operand_val else 'false'
        # elif operand_type == "$dateTimeCast":
        #     return f"'{operand_val}'"
        # elif operand_type == "$timeCast":
        #     return f"'{operand_val}'"
        # else:
        #     raise ValueError(f"Unsupported operand type: {operand_type}")

    def _convert_field_operand(self, operand_type: str, operand_val: str):
        # Examples:
        # "$sme.ProductClassifications.ProductClassificationItem.ProductClassId#value"
        # < FieldIdentifierAAS >: := "$aas#"("idShort" | "id" | "assetInformation.assetKind" | "assetInformation.assetType" | "assetInformation.globalAssetId" | "assetInformation." < SpecificAssetIdsClause > | "submodels." < ReferenceClause > )
        # < FieldIdentifierSM >: := "$sm#"( < SemanticIdClause > | "idShort" | "id" )
        # < FieldIdentifierSME >: := "$sme"("." < idShortPath >)? "#"( < SemanticIdClause > | "idShort" | "value" | "valueType" | "language" )
        # < FieldIdentifierCD >: := "$cd#"("idShort" | "id") < ws >
        if operand_val.startswith("$aas#"):
            return self._convert_field_operand_aas(operand_val)
        elif operand_val.startswith("$sm#"):
            return self._convert_field_operand_sm(operand_val)
        elif operand_val.startswith("$sme#"):
            return self._convert_field_operand_sme(operand_val)
        elif operand_val.startswith("$cd#"):
            return self._convert_field_operand_cd(operand_val)
        else:
            raise ValueError(f"Unsupported operand type: {operand_type}")

    def _convert_field_operand_cd(self, operand_val: str) -> tuple[str, str, list[str]]:
        # Define the field variable for ConceptDescription and use it in the match pattern
        field_var = f"cd{len(self.cd_vars)}"
        self.cd_vars[field_var] = field_var

        match_pattern = f"({{{field_var}}}:ConceptDescription)"
        attribute = operand_val.split("#")[-1]
        if attribute in ("idShort", "id"):
            cypher_operand = f"{{{field_var}}}.{attribute}"
        else:
            raise ValueError(f"Unsupported field operand value: {operand_val}")
        variables = [field_var]
        return cypher_operand, match_pattern, variables

    def _convert_field_operand_sm(self, operand_val: str) -> tuple[str, str, list[str]]:
        field_var = f"sm{len(self.cd_vars)}"
        self.sm_vars[field_var] = field_var
        variables = [field_var]

        match_pattern = f"({field_var}:Submodel)"

        attr_path = operand_val.split("#")[-1]
        attr_path_items = self._itemize_attr_path(attr_path)

        curr_attr = attr_path_items.pop(0)
        if curr_attr in ("idShort", "id"):
            cypher_operand = f"{{{field_var}}}.{curr_attr}"
        elif curr_attr == "semanticId":
            if not attr_path_items:
                attr_path_items.extend(["keys", "[0]", "value"])

            semantic_id_var = f"semanticId{len(self.semantic_id_vars)}"
            self.semantic_id_vars[semantic_id_var] = semantic_id_var
            variables.append("semanticId")

            match_pattern = f"({{{field_var}}}:Submodel)-[:semanticId]->({{{semantic_id_var}}}:Reference)"

            curr_attr = attr_path_items.pop(0)
            if curr_attr == "type":
                cypher_operand = f"{{{semantic_id_var}}}.type"
            elif curr_attr == "keys":
                index = attr_path_items.pop(0).strip("[]")
                curr_attr = attr_path_items.pop(0)
                if curr_attr == "value":
                    cypher_operand = f"{{{semantic_id_var}}}.keys_value[{index}]"
                elif curr_attr == "type":
                    cypher_operand = f"{{{semantic_id_var}}}.keys_type[{index}]"
                else:
                    raise ValueError(f"Unsupported field operand value: {operand_val}")
        else:
            raise ValueError(f"Unsupported field operand value: {operand_val}")

        if attr_path_items:
            raise ValueError(f"Unsupported field operand value: {operand_val}")

        return cypher_operand, match_pattern, variables

    def _itemize_attr_path(self, attr_path: str) -> list[str]:
        """Split the field into a list of fields. Dot separated or brackets with index."""
        pattern = r'([a-zA-Z_]\w*)|(\[\d*\])'
        matches = re.findall(pattern, attr_path)
        result = [match[0] if match[0] else match[1] for match in matches]
        return result

    def _merge_match_clauses(self, cypher_match_clause_0, cypher_match_clause_1, operation):
        # Example:
        # (sm0:Submodel)-[:child]->(sme1:SubmodelElement {idShort:"FileVersion"})-[:child]->(sme2:SubmodelElement {idShort:"FileVersionId"}),
        # (sm1:Submodel)-[:child]->(sme3:SubmodelElement {idShort:"FileVersion"})-[:child]->(sme4:SubmodelElement {idShort:"FileName"})
