import math

class WorldGraph:
    """
    Manages the non-Euclidean connectivity of the world.
    Connections represent travel routes, political influence, or narrative links.
    """
    def __init__(self, nodes=None):
        self.nodes = nodes or []
        self.adj = {} # Node ID -> List of (Neighbor ID, weight)
        self._build_adjacency()

    def _build_adjacency(self):
        """Calculates initial edges based on proximity (Euclidean fallback) or defined routes."""
        for node in self.nodes:
            self.adj[node['id']] = []
            for other in self.nodes:
                if node['id'] == other['id']: continue
                
                dist = self._get_dist(node, other)
                # Link if within 'Travel Range' (e.g., 200 units)
                if dist < 200:
                    self.adj[node['id']].append({
                        "id": other['id'],
                        "weight": dist,
                        "type": "ROAD"
                    })

    def _get_dist(self, n1, n2):
        return math.sqrt((n1['x'] - n2['x'])**2 + (n1['y'] - n2['y'])**2)

    def get_neighbors(self, node_id):
        return self.adj.get(node_id, [])

    def trigger_event(self, node_id, event_type, magnitude):
        """Propagates an event through the graph edges."""
        # e.g., Famine on one node reduces trade value on neighbors
        print(f"[GRAPH] Event '{event_type}' triggered on {node_id}")
        impacted = self.get_neighbors(node_id)
        for neighbor in impacted:
            # Decay magnitude over distance/weight
            decayed_magnitude = magnitude * (100 / (100 + neighbor['weight']))
            print(f"  -> Propagating to {neighbor['id']} with magnitude {decayed_magnitude:.2f}")

    def find_nearest_node(self, x, y):
        best_node = None
        min_dist = float('inf')
        for node in self.nodes:
            d = math.sqrt((node['x'] - x)**2 + (node['y'] - y)**2)
            if d < min_dist:
                min_dist = d
                best_node = node
        return best_node
