import uuid
from enum import Enum

from basyx.aas.adapter.json.json_deserialization import read_aas_json_file

from aas_mapping.settings import NODE_TYPES, RELATIONSHIP_TYPES, ATTRS_TO_IGNORE
from aas_mapping.util_type import isIterable


def _gen_neomodel_code(key, item, rels):
    def_code, variable = gen_neomodel_code(item)
    rels.append((key, variable))
    return def_code


def create_kwargs_def(kwargs):
    kwargs_def = ""
    for key, value in kwargs.items():
        if isinstance(value, str):
            kwargs_def += f"{key}='{value}', "
        elif isinstance(value, (bool, int, float)):
            kwargs_def += f"{key}={value}, "
        elif isinstance(value, Enum):
            kwargs_def += f"{key}='{value.name}', "
    kwargs_def = kwargs_def.strip(", ")
    return kwargs_def


def gen_neomodel_code(obj):
    code = ""
    rels = []
    kwargs = {}

    # generate unique object name with uuid
    variable_name = obj.__class__.__name__.lower() + uuid.uuid4().hex[:6]

    if isinstance(obj, NODE_TYPES):
        for key, value in obj.__dict__.items():
            key = key.strip('_')
            key = "id_" if key == "id" else key

            if key in ATTRS_TO_IGNORE:
                continue
            elif value is None or value == "":
                continue
            elif isinstance(value, NODE_TYPES):
                code += _gen_neomodel_code(key, value, rels)
            elif isIterable(value):
                if len(value) > 0:
                    if isinstance(iter(value).__next__(), NODE_TYPES):
                        for item in value:
                            code += _gen_neomodel_code(key, item, rels)
                    else:
                        kwargs[key] = value
            else:
                kwargs[key] = value

        kwargs_def = create_kwargs_def(kwargs)
        code += f"{variable_name} = {obj.__class__.__name__}Node({kwargs_def}).save()\n"
        for rel in rels:
            code += f"{variable_name}.{rel[0]}.connect({rel[1]})\n"
        code += "\n"
    elif isinstance(obj, RELATIONSHIP_TYPES):
        code += f"{obj.__class__.__name__}Rel()\n\n"

    return code, variable_name

def main():
    with open("example.json", "r") as f:
        obj_store = read_aas_json_file(f)

    import_line = "from aas_neomodel import *"
    code = import_line + "\n\n"

    for obj in obj_store:
        code += gen_neomodel_code(obj)[0]

    # Save the generated code to a file named 'generated_code.py'
    with open('aas_neomodel_deserialization.py', 'w', encoding='utf8') as f:
        f.write(code)

if __name__ == '__main__':
    main()
