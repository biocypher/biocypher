from ._logger import logger

logger.debug(f'Loading module {__name__}.')

from ._create import BioCypherEdge, BioCypherNode

class Deduplicator:
    """
    Singleton class responsible of deduplicating BioCypher inputs. Maintains
    sets/dictionaries of node and edge types and their unique identifiers.

    Nodes identifiers should be globally unique (represented as a set), while
    edge identifiers are only unique per edge type (represented as a dict of
    sets, keyed by edge type).

    Stores collection of duplicate node and edge identifiers and types for
    troubleshooting and to avoid overloading the log.
    """

    def __init__(self):
        self.seen_node_ids = set()  
        self.duplicate_node_ids = set()  
        self.duplicate_node_types = set()  

        self.seen_edges = {}  
        self.duplicate_edge_ids = set()  
        self.duplicate_edge_types = set()  

    def node_seen(self, node: BioCypherNode) -> bool:
        """
        Adds a node to the instance and checks if it has been seen before.

        Args:
            node: BioCypherNode to be added.

        Returns:
            True if the node has been seen before, False otherwise.
        """
        if node.get_id() in self.seen_node_ids:
            self.duplicate_node_ids.add(node.get_id())
            if node.get_label() not in self.duplicate_node_types:
                logger.warning(f"Duplicate node type {node.get_label()} found. ")
                self.duplicate_node_types.add(node.get_label())
            return True
        
        self.seen_node_ids.add(node.get_id())
        return False
    
    def edge_seen(self, edge: BioCypherEdge) -> bool:
        """
        Adds an edge to the instance and checks if it has been seen before.

        Args:
            edge: BioCypherEdge to be added.

        Returns:
            True if the edge has been seen before, False otherwise.
        """
        if edge.get_type() not in self.seen_edges:
            self.seen_edges[edge.get_type()] = set()

        # concatenate source and target if no id is present
        if not edge.get_id():
            _id = f"{edge.get_source_id()}_{edge.get_target_id()}"
        else:
            _id = edge.get_id()

        if _id in self.seen_edges[edge.get_type()]:
            self.duplicate_edge_ids.add(_id)
            if edge.get_type() not in self.duplicate_edge_types:
                logger.warning(f"Duplicate edge type {edge.get_type()} found. ")
                self.duplicate_edge_types.add(edge.get_type())
            return True
        
        self.seen_edges[edge.get_type()].add(_id)
        return False
    
    def get_duplicate_nodes(self):
        """
        Function to return a list of duplicate nodes.

        Returns:
            list: list of duplicate nodes
        """

        if self.duplicate_node_types:
            return (self.duplicate_node_types, self.duplicate_node_ids)
        else:
            return None

    def get_duplicate_edges(self):
        """
        Function to return a list of duplicate edges.

        Returns:
            list: list of duplicate edges
        """

        if self.duplicate_edge_types:
            return (self.duplicate_edge_types, self.duplicate_edge_ids)
        else:
            return None