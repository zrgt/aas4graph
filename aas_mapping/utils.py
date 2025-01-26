import uuid


def gen_unique_obj_name(obj, prefix: str=None):
    if prefix:
        return prefix + uuid.uuid4().hex[:6]
    else:
        return obj.__class__.__name__.lower() + uuid.uuid4().hex[:6]


def rm_quotes(s: str):
    return s.replace("'", "")


def add_quotes(s: str):
    return f"'{s}'"
