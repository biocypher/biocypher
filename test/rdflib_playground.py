import rdflib
import networkx as nx


def ontology_to_tree(ontology_path, root_label):
    # Load the ontology into an rdflib Graph
    g = rdflib.Graph()
    g.parse(ontology_path, format='application/rdf+xml')

    # Loop through all labels in the ontology
    for s, _, o in g.triples((None, rdflib.RDFS.label, None)):
        # If the label is the root label, set the root node to the subject of the label
        if o.eq(root_label):
            root = s
            break
    else:
        raise ValueError(f'Could not find root node with label {root_label}')

    # Find the root node of the ontology
    # Does not work because the root node has a datatype but rdflib.Literal does
    # not have one. Would have to assume that the datatype is always
    # `rdflib.term.URIRef('http://www.w3.org/2001/XMLSchema#string'`
    # try:
    #     root = next(g.subjects(rdflib.RDFS.label, rdflib.Literal(root_label)))
    # except StopIteration:
    #     raise ValueError(f"Could not find root node with label {root_label}")

    # Create a directed graph to represent the ontology as a tree
    G = nx.DiGraph()

    # Define a recursive function to add subclasses to the graph
    def add_subclasses(node):
        # Add the node to the graph if it hasn't been added already
        node_str = remove_prefix(str(node))
        if node_str not in G:
            G.add_node(node_str)
            if (node, rdflib.RDFS.label, None) in g:
                G.nodes[node_str]['label'] = str(
                    g.value(node, rdflib.RDFS.label)
                )

        # Recursively add all subclasses of the node to the graph
        for s, _, o in g.triples((None, rdflib.RDFS.subClassOf, node)):
            s_str = remove_prefix(str(s))
            G.add_node(s_str)
            if (s, rdflib.RDFS.label, None) in g:
                G.nodes[s_str]['label'] = str(g.value(s, rdflib.RDFS.label))
            G.add_edge(node_str, s_str)
            add_subclasses(s)

    # Add all subclasses of the root node to the graph
    add_subclasses(root)

    return G


def remove_prefix(uri: str) -> str:
    """
    Remove the prefix of a URI. URIs can contain either "#" or "/" as a
    separator between the prefix and the local name. The prefix is
    everything before the last separator.
    """
    return uri.rsplit('#', 1)[-1].rsplit('/', 1)[-1]


if __name__ == '__main__':
    path = 'test/so.owl'
    root_label = 'sequence_variant'
    ontology_to_tree(path, root_label)
