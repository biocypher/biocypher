#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the passing of a Neo4j driver from the client to BioCypher
and the modification of the database structure. It is part of the BioCypher 
python package, homepage: TODO.

Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo: 
    - create and update a biocypher info node that stores version and used 
        identifiers
"""

import neo4j

from .create import BioCypherEdge, BioCypherNode
from . import translate


class DatabaseToNeo4j():
    """
    """

    def __init__(self, driver, network = None):
        
        if isinstance(driver, neo4j.Neo4jDriver):
            self.driver = driver

        if network:
            self.network = network

    
    def query(self, query, **kwargs):

        session = self.driver.session()
        response = session.run(query, **kwargs)
        session.close()

        return response


    def init_db(self):

        self.wipe_db()
        self._create_constraints()
        print('Initialising database.')


    def wipe_db(self):

        self.query('MATCH (n) DETACH DELETE n;')

        self._drop_constraints()


    def _drop_constraints(self):

        s = self.driver.session()
        for constraint in s.run("CALL db.constraints"):
            s.run("DROP CONSTRAINT " + constraint[0])
        s.close()


    def _create_constraints(self):

        self.query(
            'CREATE CONSTRAINT protein_id '
            'IF NOT EXISTS ON (n:Protein) '
            'ASSERT n.id IS UNIQUE'
        )
        self.query(
            'CREATE CONSTRAINT complex_id '
            'IF NOT EXISTS ON (n:Complex) '
            'ASSERT n.id IS UNIQUE'
        )
        self.query(
            'CREATE CONSTRAINT mirna_id '
            'IF NOT EXISTS ON (n:miRNA) '
            'ASSERT n.id IS UNIQUE'
        )
        self.query(
            'CREATE CONSTRAINT reference_id '
            'IF NOT EXISTS ON (n:Reference) '
            'ASSERT n.id IS UNIQUE'
        )
        self.query(
            'CREATE CONSTRAINT source_id '
            'IF NOT EXISTS ON (n:Resource) '
            'ASSERT n.id IS UNIQUE'
        )
        self.query(
            'CREATE CONSTRAINT interaction_key '
            'IF NOT EXISTS ON (n:Interaction) '
            'ASSERT n.key IS UNIQUE'
        )


    def add_nodes_to_graph(self, values):
        """
        Generic node adder function to add any kind of input to the graph via
        the BioCypherNode class. Should employ translation functionality (as
        of now, just passing pypath input through).
        """
        
        bn = translate.nodes_from_pypath(values) # replace with check-translate function
        self.add_biocypher_nodes_to_graph(bn)


    def add_edges_to_graph(self, values):
        """
        Generic edge adder function to add any kind of input to the graph via
        the BioCypherEdge class. Should employ translation functionality (as
        of now, just passing pypath input through).
        """
        
        bn = translate.edges_from_pypath(values) # replace with check-translate function
        self.add_biocypher_edges_to_graph(bn)


    def add_biocypher_nodes_to_graph(self, nodes):
        '''
        Accepts a node type handoff class (BioCypherNode) with id, label, and a
        dict of properties (passing on the type of property, ie, int, string
        ...).

        The dict retrieved by the get_dict() method is passed into Neo4j as a
        map of maps, explicitly encoding node id and label, and adding all other
        properties from the 'properties' key of the dict. The merge is performed
        via APOC, matching only on node id to prevent duplicates. The same
        properties are set on match and on create, irrespective of the actual
        event.

        Args: 
            - nodes: a list of BioCypherNode objects

        Returns: 
            - bool: The return value. True for success, False otherwise.
        '''

        if not all(isinstance(n, BioCypherNode) for n in nodes):
            raise TypeError("Nodes must be passed as type NodeFromPypath. "
            "Please use the generic add_edges_to_graph() function.")

        print('Merging %s nodes.' % len(nodes))

        entities = [node.get_dict() for node in nodes]

        entity_query = (
            'UNWIND $entities AS ent \n'
            'CALL apoc.merge.node([ent.node_label], {id: ent.node_id}, ent.properties) '
            'YIELD node \n'
            'RETURN node'
        )

        self.query(entity_query, parameters = {'entities': entities})

        return True


    def add_biocypher_edges_to_graph(self, edges):
        '''
        Accepts an edge type handoff class (BioCypherEdge) with source and
        target ids, label, and a dict of properties (passing on the type of
        property, ie, int, string ...).

        The dict retrieved by the get_dict() method is passed into Neo4j as a
        map of maps, explicitly encoding source and target ids and the
        relationship label, and adding all edge properties from the 'properties'
        key of the dict. The merge is performed via APOC, matching only on
        source and target id to prevent duplicates. The same properties are set
        on match and on create, irrespective of the actual event.

        Args: 
            - edges: a list of BioCypherEdge objects

        Returns: 
            - bool: The return value. True for success, False otherwise.
        '''

        if not all(isinstance(e, BioCypherEdge) for e in edges):
            raise TypeError("Edges must be passed as type EdgeFromPypath. "
            "Please use the generic add_edges_to_graph() function.")

        # relationships
        print('Merging %s edges.' % len(edges))

        rels = [edge.get_dict() for edge in edges]

        # merging only on the ids of the molecules, passing the properties on
        # match and on create; removing the node labels seemed least complicated
        query = (
            'UNWIND $rels AS r \n'
            'MATCH '
            '(src {id: r.source_id}), '
            '(tar {id: r.target_id}) \n'
            'CALL apoc.merge.relationship('
            'src, r.relationship_label, NULL, r.properties, tar, r.properties) '
            'YIELD rel \n'
            'RETURN rel'
        )

        self.query(query, parameters = {'rels': rels})

        return True


        # interaction nodes: required? parallel?
        # nodes = [
        #     {
        #         'directed': rec.directed,
        #         'effect': rec.effect,
        #         'type': rec.type,
        #         'key': self.interaction_key(rec),
        #     }
        #     for rec in self.network.generate_df_records()
        # ]

        # query = (
        #     'UNWIND $nodes AS nod '
        #     'CREATE (i:Interaction) '
        #     'SET i += nod;'
        # )

        # print('Creating Interaction nodes.')
        # self.query(query, parameters = {'nodes': nodes})

