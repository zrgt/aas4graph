from collections import abc


def rm_quotes(s: str):
    return s.replace("'", "")


def add_quotes(s: str):
    return f"'{s}'"


def is_iterable(obj):
    return isinstance(obj, abc.Iterable) and not isinstance(obj, (str, bytes, bytearray))
