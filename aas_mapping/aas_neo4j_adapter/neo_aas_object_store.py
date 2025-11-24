import json
from typing import Generic, Iterator, Iterable

from basyx.aas.adapter.json import AASToJsonEncoder, StrictAASFromJsonDecoder
from basyx.aas.model import AbstractObjectStore, Identifiable, Identifier

from basyx.aas.model.provider import _IT

from aas_mapping.aas_neo4j_adapter.aas_neo4j_client import AASNeo4JClient


class Neo4jObjectStore(AbstractObjectStore[_IT], Generic[_IT]):
    """
    A Neo4j object store that extends the AbstractObjectStore and uses a Neo4j database as the backend.
    It uses the AASNeo4JClient to interact with the Neo4j database.
    """
    def __init__(self, client: AASNeo4JClient, objects: Iterable[_IT] = ()) -> None:
        self._client: AASNeo4JClient = client
        for x in objects:
            self.add(x)

    def add(self, x: _IT) -> None:
        if self._client.identifiable_exists(x.id):
            raise KeyError(f"Identifiable object with same id {x.id} is already stored in this store")
        data = json.dumps(obj=x, cls=AASToJsonEncoder)
        data_dict = json.loads(data)
        self._client.add_identifiable(data_dict)

    def get_identifiable(self, identifier: Identifier) -> _IT:
        try:
            data = self._client.get_identifiable(identifier)
        except KeyError as e:
            raise KeyError(identifier)
        obj = json.loads(json.dumps(data), cls=StrictAASFromJsonDecoder)
        return obj

    def discard(self, x: _IT) -> None:
        self._client.remove_identifiable(x.id)

    def remove(self, x: _IT) -> None:
        if not self._client.identifiable_exists(x.id):
            raise KeyError(f"Identifiable object with id {x.id} not found in Neo4j store")

        result = self._client.remove_identifiable(x.id)
        if result == 0: # Zero nodes were removed
            raise KeyError(f"The Identifiable could not be removed: {x.id}")

    def __contains__(self, x: object) -> bool:
        if isinstance(x, Identifier):
            return self._client.identifiable_exists(x)
        elif isinstance(x, Identifiable):
            # FIXME: We only check if Identifiable with the same ID exists in the store
            # We don't check if these are equal, as the basyx-bython-sdj doesn't implement the equal-operator
            return self._client.identifiable_exists(x.id)
        return False

    def __len__(self):
        return self._client.count_identifiables()

    def __iter__(self) -> Iterator[_IT]:
        """
        Iterates over all Identifiable objects in the Neo4j store.
        """
        clause = "MATCH (r:Identifiable) RETURN r.id AS id"
        result = self._client.execute_clause(clause)
        for record in result:
            yield self.get_identifiable(record["id"])
