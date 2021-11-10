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

"""

import os
import re
import importlib as imp

import yaml
import neo4j

from .create import BioCypherEdge, BioCypherNode
from . import translate
from .check import MetaEdge, VersionNode, MetaNode


class DriverBase(object):
    """
    Manages the connection to the Neo4j server. Establishes the connection
    and executes queries. A wrapper around the `Driver` object from the
    :py:mod:`neo4j` module, which is stored in the :py:attr:`driver`
    attribute.

    The connection can be defined in three ways:
        * Providing a ready ``neo4j.Driver`` instance
        * By URI and authentication data
        * By a YML config file

    Args:
        driver (neo4j.Driver): A ``neo4j.Driver`` instance, created by,
            for example, ``neo4j.GraphDatabase.driver``.
        db_name (str): Name of the database (Neo4j graph) to use.
        db_uri (str): Protocol, host and port to access the Neo4j server.
        db_auth (tuple): Neo4j server authentication data: tuple of user
            name and password.
        fetch_size (int): Optional; the fetch size to use in database
            transactions.
        config_file (str): Path to a YML config file which provides the URI,
            user name and password.
        wipe (bool): Wipe the database after connection, ensuring the data
            is loaded into an empty database.
    """

    def __init__(
            self,
            driver = None,
            db_name = None,
            db_uri = 'neo4j://localhost:7687',
            db_auth = None,
            fetch_size = 1000,
            config_file = 'config/db_config.yaml',
            wipe = False,
        ):

        self.driver = driver

        if not self.driver:

            self._db_config = {
                'uri': db_uri,
                'auth': db_auth,
                'db': db_name,
                'fetch_size': fetch_size,
            }

            # include to load default yaml from module
            ROOT = os.path.join(
                *os.path.split(
                    os.path.abspath(os.path.dirname(__file__))
                )
            )
            self._config_file = ROOT + "/../" + config_file

            self.db_connect()

        self.ensure_db()

        
    def reload(self):
        """
        Reloads the object from the module level.
        """

        modname = self.__class__.__module__
        mod = __import__(modname, fromlist = [modname.split('.')[0]])
        imp.reload(mod)
        new = getattr(mod, self.__class__.__name__)
        setattr(self, '__class__', new)


    def _log(self, msg = '', level = 0):
        """
        Later we will connect this to a logger.
        """

        pass


    def db_connect(self):
        """
        Creates a database connection manager (driver) based on the current
        configuration.
        """

        if not all(self._db_config.values()):

            self.read_config()

        # check for database running?
        self.driver = neo4j.GraphDatabase.driver(
            uri = self.uri,
            auth = self.auth,
        )

        self._log('Opened database connection.')


    @property
    def uri(self):

        return self._db_config['uri']


    @property
    def auth(self):

        return self._db_config['auth']


    def read_config(self, section = 'default'):
        """
        Populates the instance configuration from one section of a YML config
        file.
        """

        if self._config_file and os.path.exists(self._config_file):

            self._log('Reading config from `%s`.' % self._config_file)
            

            with open(self._config_file, 'r') as fp:

                conf = yaml.safe_load(fp.read())

            self._db_config.update(conf[section])
            self._db_config['auth'] = tuple(self._db_config['auth'])

        if not self._db_config['db']:

            self._db_config['db'] = self._default_db


    def close(self):
        """
        Closes the Neo4j driver if it exists and is open.
        """

        if hasattr(self.driver, 'close'):

            self.driver.close()


    def __del__(self):

        self.close()


    @property
    def _home_db(self):

        return self._db_name()


    @property
    def _default_db(self):

        return self._db_name('DEFAULT')


    def _db_name(self, which = 'HOME'):

        resp = self.query('SHOW %s DATABASE;' % which)

        if resp:

            return resp[0]['name']


    def query(self, query, db = None, fetch_size = None, **kwargs):
        """
        Creates a session with the driver passed into the class at
        instantiation, runs a CYPHER query and returns the response.

        Args:
            query: a valid CYPHER query, can include APOC if the APOC plugin
                is installed in the accessed database
            **kwargs: optional objects used in CYPHER interactive mode, for
                instance for passing a parameter dictionary

        Returns:
            neo4j.Result: the Neo4j response to the query
        """

        db = db or self._db_config['db'] or neo4j.DEFAULT_DATABASE
        fetch_size = fetch_size or self._db_config['fetch_size']

        session = self.driver.session(database = db, fetch_size = fetch_size)
        response = session.run(query, **kwargs).data()
        session.close()

        return response


    @property
    def current_db(self):
        """
        Name of the database (graph) where the next query would be executed.

        Returns:
            (str): Name of a database.
        """

        return self._db_config['db'] or self._home_db


    def db_exists(self, name = None):
        """
        Tells if a database exists in the storage of the Neo4j server.

        Args:
            name (str): Name of a database (graph).

        Returns:
            (bool): `True` if the database exists.
        """

        return bool(self.db_status(name = name))


    def db_status(self, name = None, field = 'currentStatus'):
        """
        Tells the current status or other state info of a database.

        Args:
            name (str): Name of a database (graph).
            field (str,NoneType): The field to return.

        Returns:
            (str,dict): The status as a string, `None` if the database does
                not exist. If :py:arg:`field` is `None` a dictionary with
                all fields will be returned.
        """

        name = name or self.current_db

        resp = self.query('SHOW DATABASES WHERE name = "%s";' % name)

        if resp:

            return resp[0][field] if field in resp[0] else resp[0]


    def db_online(self, name = None):
        """
        Tells if a database is currently online (active).

        Args:
            name (str): Name of a database (graph).

        Returns:
            (bool): `True` if the database is online.
        """

        return self.db_status(name = name) == 'online'


    def create_db(self, name = None):
        """
        Create a database if it does not already exist.

        Args:
            name (str): Name of the database.
        """

        self._manage_db('CREATE', name = name, options = 'IF NOT EXISTS')


    def start_db(self, name = None):
        """
        Starts a database (brings it online) if it is offline.

        Args:
            name (str): Name of the database.
        """

        self._manage_db('START', name = name)


    def stop_db(self, name = None):
        """
        Stops a database, making sure it's offline.

        Args:
            name (str): Name of the database.
        """

        self._manage_db('STOP', name = name)


    def drop_db(self, name = None):
        """
        Deletes a database if it exists.

        Args:
            name (str): Name of the database.
        """

        self._manage_db('DROP', name = name, options = 'IF EXISTS')


    def _manage_db(self, cmd, name = None, options = None):
        """
        Executes a database management command.

        Args:
            cmd (str): The command: CREATE, START, STOP, DROP, etc.
            name (str): Name of the database.
            options (str): The optional parts of the command, following the
                database name.
        """

        self.query(
            '%s DATABASE %s %s;' % (
                cmd,
                name or self.current_db,
                options or '',
            )
        )


    def wipe_db(self):
        """
        Used in initialisation, deletes all nodes and edges and drops all
        constraints.
        """

        self.query('MATCH (n) DETACH DELETE n;')

        self._drop_constraints()


    def ensure_db(self):
        """
        Makes sure the database used by this instance exists and is online.
        If the database creation or startup is necessary but the user does
        not have the sufficient privileges, an exception will be raised.
        """

        if not self.db_exists():

            self.create_db()

        if not self.db_online():

            self.start_db()


    def _drop_constraints(self):
        """
        Drops all constraints in the database. Requires the database to be
        empty.
        """

        s = self.driver.session()

        for constraint in s.run("CALL db.constraints"):

            s.run("DROP CONSTRAINT " + constraint[0])

        s.close()


    @property
    def node_count(self):
        """
        Number of nodes in the database.
        """

        return self.query('MATCH (n) RETURN COUNT(n) AS count;')[0]['count']


    @property
    def edge_count(self):
        """
        Number of edges in the database.
        """

        return self.query(
            'MATCH ()-[r]->() RETURN COUNT(r) AS count;'
        )[0]['count']


    @property
    def user(self):
        """
        User for the currently active connection.

        Returns:
            (str): The name of the user, `None` if no connection or no
                unencrypted authentication data is available.
        """

        if self.driver:

            opener_vars = dict(zip(
                self.driver._pool.opener.__code__.co_freevars,
                self.driver._pool.opener.__closure__,
            ))

            if 'auth' in opener_vars:

                return opener_vars['auth'].cell_contents[0]


    def __len__(self):

        return self.node_count


    def session(self, **kwargs):

        return self.driver.session(**kwargs)


    def __enter__(self):

        self._context_session = self.session()

        return self._context_session


    def __exit__(self, *exc):

        if hasattr(self, '_context_session'):

            self._context_session.close()
            delattr(self, '_context_session')


    def __repr__(self):

        return '<%s %s>' % (
            self.__class__.__name__,
            self._connection_str if self.driver else '[no connection]'
        )


    @property
    def _connection_str(self):

        return '%s://%s:%u/%s' % (
            re.split(
                r'(?<=[a-z])(?=[A-Z])',
                self.driver.__class__.__name__,
            )[0].lower(),
            self.driver._pool.address[0] if self.driver else 'unknown',
            self.driver._pool.address[1] if self.driver else 0,
            self.user or 'unknown',
        )


class Driver(DriverBase):
    """
    Manages a connection to a biocypher database.

    The connection can be defined in three ways:
        * Providing a ready ``neo4j.Driver`` instance
        * By URI and authentication data
        * By a YML config file

    Args:
        driver (neo4j.Driver): A ``neo4j.Driver`` instance, created by,
            for example, ``neo4j.GraphDatabase.driver``.
        db_name (str): Name of the database (Neo4j graph) to use.
        db_uri (str): Protocol, host and port to access the Neo4j server.
        db_auth (tuple): Neo4j server authentication data: tuple of user
            name and password.
        fetch_size (int): Optional; the fetch size to use in database
            transactions.
        config_file (str): Path to a YML config file which provides the URI,
            user name and password.
        wipe (bool): Wipe the database after connection, ensuring the data
            is loaded into an empty database.
    """

    def __init__(
            self,
            driver = None,
            db_name = None,
            db_uri = 'neo4j://localhost:7687',
            db_auth = None,
            fetch_size = 100,
            config_file = 'config/db_config.yaml',
            wipe = False,
        ):

        DriverBase.__init__(**locals())

        # get database version node ('check' module)
        # immutable variable of each instance (ie, each call from the 
        # adapter to BioCypher)
        # checks for existence of graph representation and returns if found,
        # else creates new one
        self.db_meta = VersionNode(self)

        # if db representation node does not exist or explicitly asked for wipe
        # create new graph representation: default yml, interactive?
        if wipe or self.db_meta.graph_state is None:
            self.init_db()

        # then
        self.update_meta_graph()


    def update_meta_graph(self):
        # add version node
        self.add_biocypher_nodes(self.db_meta)

        # connect version node to previous
        e_meta = BioCypherEdge(
            self.db_meta.graph_state['id'],
            self.db_meta.node_id,
            'PRECEDES'
            )
        self.add_biocypher_edges(e_meta)

        # add structure nodes
        n = []
        # append only bottom level key-value pairs
        
        for entity, params in self.db_meta.leaves.items():
            n.append(MetaNode(entity, **params))
        self.add_biocypher_nodes(n)

        # connect structure nodes to version node
        e = []
        current_version = self.db_meta.get_id()
        for entity in [item[0] for item in self.db_meta.leaves]:
            e.append(MetaEdge(current_version, entity, "CONTAINS"))
        self.add_biocypher_edges(e)


    def init_db(self):
        """
        Used to initialise a property graph database by deleting contents and
        constraints and setting up new constraints.

        Todo:
            - set up constraint creation interactively depending on the need
                of the database
        """

        self.wipe_db()
        self._create_constraints()
        self._log('Initialising database.')
        

    def _create_constraints(self):
        """
        Creates constraints on node types in the graph. Used for initial setup.

        Todo:
            - customise to create constraints on the selected structure
            - edges?
            - apoc?
        """

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


    def add_nodes(self, id_type_tuples):
        """
        Generic node adder function to add any kind of input to the graph via
        the BioCypherNode class. Should employ translation functionality (as
        of now, just passing pypath input through).
        """

        bn = translate.translate_nodes(self.db_meta.schema, id_type_tuples)
        self.add_biocypher_nodes(bn)


    def add_edges(self, values):
        """
        Generic edge adder function to add any kind of input to the graph via
        the BioCypherEdge class. Should employ translation functionality (as
        of now, just passing pypath input through).
        """

        bn = translate.edges_from_pypath(values) # replace with check-translate function
        self.add_biocypher_edges(bn)


    def add_biocypher_nodes(self, nodes):
        """
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
            nodes: a list of BioCypherNode objects

        Returns:
            bool: The return value. True for success, False otherwise.

        Todo:
            - use return nodes to implement test?
        """

        if type(nodes) is not list: nodes = [ nodes ]

        if not all(isinstance(n, BioCypherNode) for n in nodes):
            raise TypeError("Nodes must be passed as type NodeFromPypath. "
            "Please use the generic add_edges() function.")

        self._log('Merging %s nodes.' % len(nodes))

        entities = [node.get_dict() for node in nodes]

        entity_query = (
            'UNWIND $entities AS ent \n'
            'CALL apoc.merge.node([ent.node_label], {id: ent.node_id}, ent.properties) '
            'YIELD node \n'
            'RETURN node'
        )
        self.query(entity_query, parameters = {'entities': entities})

        return True


    def add_biocypher_edges(self, edges):
        """
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
            edges: a list of BioCypherEdge objects

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        if type(edges) is not list: edges = [ edges ]

        if not all(isinstance(e, BioCypherEdge) for e in edges):
            raise TypeError("Edges must be passed as type EdgeFromPypath. "
            "Please use the generic add_edges() function.")

        # relationships
        self._log('Merging %s edges.' % len(edges))

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
