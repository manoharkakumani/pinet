import networkx as nx
from typing import List, Tuple, Optional, Union, Dict

class KnowledgeGraphMemory:
    def __init__(self, name: str):
        self.name = name
        self.graph = nx.DiGraph()

    def load(self):
        return self  # Placeholder for compatibility

    def add_triplet(self, subject: str, predicate: str, obj: str):
        self.graph.add_node(subject, type="entity")
        self.graph.add_node(obj, type="entity")
        self.graph.add_edge(subject, obj, predicate=predicate)

    def bulk_add(self, triplets: List[Tuple[str, str, str]]):
        for s, p, o in triplets:
            self.add_triplet(s, p, o)

    def query(self, subject: Optional[str] = None, predicate: Optional[str] = None, obj: Optional[str] = None) -> List[str]:
        results = []
        for u, v, attrs in self.graph.edges(data=True):
            if ((subject is None or u == subject) and
                (obj is None or v == obj) and
                (predicate is None or attrs.get("predicate") == predicate)):
                results.append(f"{u} --[{attrs['predicate']}]--> {v}")
        return results

    def visualize(self) -> str:
        return "\n".join([f"{u} --[{d['predicate']}]--> {v}" for u, v, d in self.graph.edges(data=True)])

    def append(self, item: Union[str, dict]):
        if isinstance(item, dict) and 'role' in item and 'content' in item:
            self.add_triplet("user", "says", item['content'])

    def get_messages(self):
        triples = self.graph.get_all_facts()
        return [{"role": "assistant", "content": f"{u} --[{d['predicate']}]--> {v}"} for u,v,d in triples]

    def to_facts(self) -> List[Dict[str, str]]:
        return [{"subject": u, "predicate": d["predicate"], "object": v} for u, v, d in self.graph.edges(data=True)]

# Tool functions
KG_INSTANCE = KnowledgeGraphMemory("shared_kg")

def add_fact(payload):
    triplet = payload.get("triplet")
    if isinstance(triplet, list) and len(triplet) == 3:
        KG_INSTANCE.add_triplet(*triplet)
        return {"status": "added", "triplet": triplet}
    return {"error": "Invalid triplet format"}

def query_kg(payload):
    subject = payload.get("subject")
    predicate = payload.get("predicate")
    obj = payload.get("object")
    return KG_INSTANCE.query(subject, predicate, obj)

def get_all_facts(_: dict = None):
    return KG_INSTANCE.to_facts()
