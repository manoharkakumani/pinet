"""Knowledge Graph Tool wrapper for use in Pinet tools registry"""

from pinet.memory.knowledge_graph import KnowledgeGraphMemory

# Shared knowledge graph instance
kg_tools = KnowledgeGraphMemory("shared_kg")

def add_fact(payload):
    triplet = payload.get("triplet")
    if isinstance(triplet, list) and len(triplet) == 3:
        kg_tools.add_triplet(*triplet)
        return {"status": "added", "triplet": triplet}
    return {"error": "Invalid triplet format"}

def query_kg(payload):
    subject = payload.get("subject")
    predicate = payload.get("predicate")
    obj = payload.get("object")
    return kg_tools.query(subject, predicate, obj)

def reset_kg(_: dict = None):
    kg_tools.graph.clear()
    return {"status": "cleared"}

def get_all_facts(_: dict = None):
    return kg_tools.to_facts()


def visualize_kg(_: dict = None):
        return kg_tools.visualize()

__all__ = ["kg_tools", "add_fact", "query_kg", "reset_kg", "get_all_facts", "visualize_kg"]
