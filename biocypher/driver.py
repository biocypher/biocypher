#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module handles the passing of a Neo4j driver from the client to 
BioCypher and the modification of the database structure. It is part of 
the BioCypher python package, homepage: TODO.

Copyright 2021, Heidelberg University Clinic

File author(s): Sebastian Lobentanzer
                ...

Distributed under GPLv3 license, see LICENSE.txt.

Todo:

"""

import os
import re
import itertools
import importlib as imp
from types import GeneratorType
from typing import List

import yaml
import neo4j


from .create import BioCypherEdge, BioCypherNode
from .translate import BiolinkAdapter, gen_translate_edges, gen_translate_nodes
from .check import MetaEdge, VersionNode, MetaNode
from .utils import pretty
from .logger import get_logger
from .write import BatchWriter

logger = get_logger(__name__)
logger.debug(f"Loading module {__name__}.")


class BaseDriver(object):
    """
    Manages the connection to the Neo4j server. Establishes the
    connection and executes queries. A wrapper around the `Driver`
    object from the :py:mod:`neo4j` module, which is stored in the
    :py:attr:`driver` attribute.

    The connection can be defined in three ways:
        * Providing a ready ``neo4j.Driver`` instance
        * By URI and authentication data
        * By a YML config file

    Args:
        driver (neo4j.Driver): A ``neo4j.Driver`` instance, created by,
            for example, ``neo4j.GraphDatabase.driver``.
        db_name (str): Name of the database (Neo4j graph) to use.
        db_uri (str): Protocol, host and port to access the Neo4j
            server.
        db_auth (tuple): Neo4j server authentication data: tuple of user
            name and password.
        fetch_size (int): Optional; the fetch size to use in database
            transactions.
        config_file (str): Path to a YML config file which provides the
            URI, user name and password.
        wipe (bool): Wipe the database after connection, ensuring the
            data is loaded into an empty database.
        increment_version (bool): Whether to increase version number
            automatically and create a new BioCypher version node in the
            graph.

    Todo:
        - remove biocypher-specific init args, possible?
    """

    def __init__(
        self,
        driver=None,
        db_name=None,
        db_uri="neo4j://localhost:7687",
        db_auth=None,
        fetch_size=1000,
        config_file="config/db_config.yaml",
        wipe=False,
        increment_version=True,
    ):

        self.driver = driver
        if self.driver:
            logger.info("Loading from supplied driver.")

        if not self.driver:
            logger.info(
                "No driver supplied, initialising driver from local configuration."
            )
            self._db_config = {
                "uri": db_uri,
                "auth": db_auth,
                "db": db_name,
                "fetch_size": fetch_size,
            }

            # include to load default yaml from module
            ROOT = os.path.join(
                *os.path.split(os.path.abspath(os.path.dirname(__file__)))
            )
            self._config_file = ROOT + "/../" + config_file

            self.db_connect()

        self.ensure_db()

    def reload(self):
        """
        Reloads the object from the module level.
        """

        modname = self.__class__.__module__
        mod = __import__(modname, fromlist=[modname.split(".")[0]])
        imp.reload(mod)
        new = getattr(mod, self.__class__.__name__)
        setattr(self, "__class__", new)

    def db_connect(self):
        """
        Creates a database connection manager (driver) based on the
        current configuration.
        """

        if not all(self._db_config.values()):

            self.read_config()

        # check for database running?
        self.driver = neo4j.GraphDatabase.driver(
            uri=self.uri,
            auth=self.auth,
        )

        logger.info("Opened database connection.")

    @property
    def uri(self):

        return self._db_config["uri"]

    @property
    def auth(self):

        return self._db_config["auth"]

    def read_config(self, section="default"):
        """
        Populates the instance configuration from one section of a YAML
        config file.
        """

        if self._config_file and os.path.exists(self._config_file):

            logger.info("Reading config from `%s`." % self._config_file)

            with open(self._config_file, "r") as fp:

                conf = yaml.safe_load(fp.read())

            self._db_config.update(conf[section])
            self._db_config["auth"] = tuple(self._db_config["auth"])

        if not self._db_config["db"]:

            self._db_config["db"] = self._default_db

    def close(self):
        """
        Closes the Neo4j driver if it exists and is open.
        """

        if hasattr(self.driver, "close"):

            self.driver.close()

    def __del__(self):

        self.close()

    @property
    def _home_db(self):

        return self._db_name()

    @property
    def _default_db(self):

        return self._db_name("DEFAULT")

    def _db_name(self, which="HOME"):

        resp, summary = self.query("SHOW %s DATABASE;" % which)

        if resp:

            return resp[0]["name"]

    def query(
        self,
        query,
        db=None,
        fetch_size=None,
        write=True,  # route to write server (default)
        explain=False,
        profile=False,
        **kwargs,
    ):
        """
        Creates a session with the driver passed into the class at
        instantiation, runs a CYPHER query and returns the response.

        Args:
            query (str): a valid CYPHER query, can include APOC if the APOC
                plugin is installed in the accessed database
            db (str): the DB inside the Neo4j server that should be queried
            fetch_size (int): the Neo4j fetch size parameter
            write (bool): indicates whether to address write- or read-
                servers
            explain (bool): indicates whether to EXPLAIN the CYPHER
                query and return the ResultSummary
            explain (bool): indicates whether to PROFILE the CYPHER
                query and return the ResultSummary
            **kwargs: optional objects used in CYPHER interactive mode,
                for instance for passing a parameter dictionary

        Returns:
            tuple of two:
                - neo4j.Record.data: the Neo4j response to the query, consumed
                  by the shorthand .data() function on the Result object
                - neo4j.ResultSummary: information about the Result returned
                  by the .consume() function on the Result object

        Todo:

            - generalise? had to create conditionals for profiling, as
              the returns are not equally important. the .data()
              shorthand may not be applicable in all cases. should we
              return the `Result` object directly plus the summary
              object from .consume()?

                - From Docs: "Any query results obtained within a
                  transaction function should be consumed within that
                  function, as connection-bound resources cannot be
                  managed correctly when out of scope. To that end,
                  transaction functions can return values but these
                  should be derived values rather than raw results."

            - use session.run() or individual transactions?

                - From Docs: "Transaction functions are the recommended
                  form for containing transactional units of work.
                  When a transaction fails, the driver retry logic is
                  invoked. For several failure cases, the transaction
                  can be immediately retried against a different
                  server. These cases include connection issues,
                  server role changes (e.g. leadership elections)
                  and transient errors."

            - use write and read distinctions in calling transactions
              ("access mode")?
            - use neo4j `@unit_of_work`?

        """

        db = db or self._db_config["db"] or neo4j.DEFAULT_DATABASE
        fetch_size = fetch_size or self._db_config["fetch_size"]

        if explain:
            query = "EXPLAIN " + query
        elif profile:
            query = "PROFILE " + query

        if write:
            # default case, write acces (route to write server)
            with self.driver.session(
                database=db,
                fetch_size=fetch_size,
            ) as session:
                res = session.run(query, **kwargs)
                return res.data(), res.consume()
        else:
            # route to read server to free up write capacity, only to be
            # used in cases with assured read-only access
            with self.driver.session(
                default_access_mode=neo4j.READ_ACCESS,  # route to read server
                database=db,
                fetch_size=fetch_size,
            ) as session:
                res = session.run(query, **kwargs)
                return res.data(), res.consume()

    def explain(
        self,
        query,
        db=None,
        fetch_size=None,
        write=True,
        **kwargs,
    ):
        """
        Wrapper for EXPLAIN function query to bring summary in
        readable form.

        CAVE: Only handles linear profiles (no branching) as of now.
        TODO include branching as in profile()
        """

        logger.info("Explaining a query.")

        data, summary = self.query(
            query, db, fetch_size, write, explain=True, **kwargs
        )
        plan = summary.plan
        printout = pretty(plan)
        return plan, printout

    def profile(
        self,
        query,
        db=None,
        fetch_size=None,
        write=True,
        **kwargs,
    ):
        """
        Wrapper for PROFILE function query to bring summary in
        readable form.

        Args:
            query (str): a valid Cypher query (see `query()`)
            db (str): the DB inside the Neo4j server that should be queried
            fetch_size (int): the Neo4j fetch size parameter
            write (bool): indicates whether to address write- or read-
                servers
            explain (bool): indicates whether to EXPLAIN the CYPHER
                query and return the ResultSummary
            explain (bool): indicates whether to PROFILE the CYPHER
                query and return the ResultSummary
            **kwargs: optional objects used in CYPHER interactive mode,
                for instance for passing a parameter dictionary

        Returns:
            dict: the raw profile returned by the Neo4j bolt driver
            list of str: a list of strings ready for printing
        """

        logger.info("Profiling a query.")

        data, summary = self.query(
            query, db, fetch_size, write, profile=True, **kwargs
        )

        prof = summary.profile
        exec_time = (
            summary.result_available_after + summary.result_consumed_after
        )

        # get structure
        # TODO (readability may be better when ordered from top to bottom)

        # get print representation
        header = f"Execution time: {exec_time:n}\n"
        printout = pretty(prof, [header], indent=0)

        return prof, printout

    @property
    def current_db(self):
        """
        Name of the database (graph) where the next query would be
        executed.

        Returns:
            (str): Name of a database.
        """

        return self._db_config["db"] or self._home_db

    def db_exists(self, name=None):
        """
        Tells if a database exists in the storage of the Neo4j server.

        Args:
            name (str): Name of a database (graph).

        Returns:
            (bool): `True` if the database exists.
        """

        return bool(self.db_status(name=name))

    def db_status(self, name=None, field="currentStatus"):
        """
        Tells the current status or other state info of a database.

        Args:
            name (str): Name of a database (graph).
            field (str,NoneType): The field to return.

        Returns:
            (str,dict): The status as a string, `None` if the database
                does not exist. If :py:attr:`field` is `None` a
                dictionary with all fields will be returned.
        """

        name = name or self.current_db

        resp, summary = self.query('SHOW DATABASES WHERE name = "%s";' % name)

        if resp:

            return resp[0][field] if field in resp[0] else resp[0]

    def db_online(self, name=None):
        """
        Tells if a database is currently online (active).

        Args:
            name (str): Name of a database (graph).

        Returns:
            (bool): `True` if the database is online.
        """

        return self.db_status(name=name) == "online"

    def create_db(self, name=None):
        """
        Create a database if it does not already exist.

        Args:
            name (str): Name of the database.
        """

        self._manage_db("CREATE", name=name, options="IF NOT EXISTS")

    def start_db(self, name=None):
        """
        Starts a database (brings it online) if it is offline.

        Args:
            name (str): Name of the database.
        """

        self._manage_db("START", name=name)

    def stop_db(self, name=None):
        """
        Stops a database, making sure it's offline.

        Args:
            name (str): Name of the database.
        """

        self._manage_db("STOP", name=name)

    def drop_db(self, name=None):
        """
        Deletes a database if it exists.

        Args:
            name (str): Name of the database.
        """

        self._manage_db("DROP", name=name, options="IF EXISTS")

    def _manage_db(self, cmd, name=None, options=None):
        """
        Executes a database management command.

        Args:
            cmd (str): The command: CREATE, START, STOP, DROP, etc.
            name (str): Name of the database.
            options (str): The optional parts of the command, following
                the database name.
        """

        self.query(
            "%s DATABASE %s %s;"
            % (
                cmd,
                name or self.current_db,
                options or "",
            )
        )

    def wipe_db(self):
        """
        Used in initialisation, deletes all nodes and edges and drops
        all constraints.
        """

        self.query("MATCH (n) DETACH DELETE n;")

        self._drop_constraints()

    def ensure_db(self):
        """
        Makes sure the database used by this instance exists and is
        online. If the database creation or startup is necessary but the
        user does not have the sufficient privileges, an exception will
        be raised.
        """

        if not self.db_exists():

            self.create_db()

        if not self.db_online():

            self.start_db()

    def _drop_constraints(self):
        """
        Drops all constraints in the database. Requires the database to
        be empty.
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

        res, summary = self.query("MATCH (n) RETURN COUNT(n) AS count;")

        return res[0]["count"]

    @property
    def edge_count(self):
        """
        Number of edges in the database.
        """

        res, summary = self.query("MATCH ()-[r]->() RETURN COUNT(r) AS count;")

        return res[0]["count"]

    @property
    def user(self):
        """
        User for the currently active connection.

        Returns:
            (str): The name of the user, `None` if no connection or no
                unencrypted authentication data is available.
        """

        if self.driver:

            opener_vars = dict(
                zip(
                    self.driver._pool.opener.__code__.co_freevars,
                    self.driver._pool.opener.__closure__,
                )
            )

            if "auth" in opener_vars:

                return opener_vars["auth"].cell_contents[0]

    def __len__(self):

        return self.node_count

    def session(self, **kwargs):

        return self.driver.session(**kwargs)

    def __enter__(self):

        self._context_session = self.session()

        return self._context_session

    def __exit__(self, *exc):

        if hasattr(self, "_context_session"):

            self._context_session.close()
            delattr(self, "_context_session")

    def __repr__(self):

        return "<%s %s>" % (
            self.__class__.__name__,
            self._connection_str if self.driver else "[no connection]",
        )

    @property
    def _connection_str(self):

        return "%s://%s:%u/%s" % (
            re.split(
                r"(?<=[a-z])(?=[A-Z])",
                self.driver.__class__.__name__,
            )[0].lower(),
            self.driver._pool.address[0] if self.driver else "unknown",
            self.driver._pool.address[1] if self.driver else 0,
            self.user or "unknown",
        )


class Driver(BaseDriver):
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
        db_uri (str): Protocol, host and port to access the Neo4j
            server.
        db_auth (tuple): Neo4j server authentication data: tuple of user
            name and password.
        fetch_size (int): Optional; the fetch size to use in database
            transactions.
        config_file (str): Path to a YML config file which provides the
            URI, user name and password.
        wipe (bool): Wipe the database after connection, ensuring the
            data is loaded into an empty database.
        increment_version (bool): Whether to increase version number
            automatically and create a new BioCypher version node in the
            graph.
    """

    def __init__(
        self,
        driver=None,
        db_name=None,
        db_uri="neo4j://localhost:7687",
        db_auth=None,
        fetch_size=1000,
        config_file="config/module_config.yaml",
        wipe=False,
        increment_version=True,
    ):

        BaseDriver.__init__(**locals())

        # get database version node ('check' module)
        # immutable variable of each instance (ie, each call from
        # the adapter to BioCypher)
        # checks for existence of graph representation and returns
        # if found, else creates new one
        self.db_meta = VersionNode(self)

        # if db representation node does not exist or explicitly
        # asked for wipe, create new graph representation: default
        # yml, interactive?
        if wipe or self.db_meta.graph_state is None:
            self.init_db()

        if increment_version:
            # set new current version node
            self.update_meta_graph()

    def update_meta_graph(self):
        logger.info("Updating Neo4j meta graph.")
        # add version node
        self.add_biocypher_nodes(self.db_meta)

        # connect version node to previous
        if self.node_count > 1:
            e_meta = BioCypherEdge(
                self.db_meta.graph_state["id"],
                self.db_meta.node_id,
                "PRECEDES",
            )
            self.add_biocypher_edges(e_meta)

        # add structure nodes
        no_l = []
        # leaves of the hierarchy specified in schema yaml
        for entity, params in self.db_meta.leaves.items():
            no_l.append(MetaNode(entity, **params))
        self.add_biocypher_nodes(no_l)

        # remove connection of structure nodes from previous version
        # node(s)
        self.query("MATCH ()-[r:CONTAINS]-()" "DELETE r")

        # connect structure nodes to version node
        ed_v = []
        current_version = self.db_meta.get_id()
        for entity in self.db_meta.leaves.keys():
            ed_v.append(MetaEdge(current_version, entity, "CONTAINS"))
        self.add_biocypher_edges(ed_v)

        # add graph structure between MetaNodes
        ed = []
        for no in no_l:
            id = no.get_id()
            src = no.get_properties().get("source")
            tar = no.get_properties().get("target")
            if not None in [id, src, tar]:
                ed.append(BioCypherEdge(id, src, "IS_SOURCE_OF"))
                ed.append(BioCypherEdge(id, tar, "IS_TARGET_OF"))
        self.add_biocypher_edges(ed)

    def init_db(self):
        """
        Used to initialise a property graph database by deleting
        contents and constraints and setting up new constraints.

        Todo:
            - set up constraint creation interactively depending on the
                need of the database
        """

        self.wipe_db()
        self._create_constraints()
        logger.info("Initialising database.")

    def _create_constraints(self):
        """
        Creates constraints on node types in the graph. Used for
        initial setup.

        Grabs leaves of the schema_config.yaml file and creates
        constraints on the id of all entities represented as nodes.
        """

        logger.info(f"Creating constraints for node types in config.")

        # get structure
        for leaf in self.db_meta.leaves.items():
            label = leaf[0]
            if leaf[1]["represented_as"] == "node":

                s = (
                    f"CREATE CONSTRAINT {label}_id "
                    f"IF NOT EXISTS ON (n:{label}) "
                    "ASSERT n.id IS UNIQUE"
                )
                self.query(s)

    def add_nodes(self, id_type_tuples):
        """
        Generic node adder function to add any kind of input to the
        graph via the BioCypherNode class. Employs translation
        functionality.
        """

        bn = gen_translate_nodes(self.db_meta.schema, id_type_tuples)
        self.add_biocypher_nodes(bn)

    def add_edges(self, src_tar_type_tuples):
        """
        Generic edge adder function to add any kind of input to the
        graph via the BioCypherEdge class. Employs translation
        functionality.
        """

        bn = gen_translate_edges(self.db_meta.schema, src_tar_type_tuples)
        self.add_biocypher_edges(bn)

    def add_biocypher_nodes(self, nodes, explain=False, profile=False):
        """
        Accepts a node type handoff class (BioCypherNode) with id,
        label, and a dict of properties (passing on the type of
        property, ie, int, string ...).

        The dict retrieved by the get_dict() method is passed into Neo4j
        as a map of maps, explicitly encoding node id and label, and
        adding all other properties from the 'properties' key of the
        dict. The merge is performed via APOC, matching only on node id
        to prevent duplicates. The same properties are set on match and
        on create, irrespective of the actual event.

        Args:
            nodes: a list of BioCypherNode objects

        Returns:
            bool: The return value. True for success, False otherwise.

        Todo:
            - use return nodes to implement test?
        """

        # receive generator objects
        if isinstance(nodes, GeneratorType):
            nodes, cnodes = itertools.tee(nodes)
            if not isinstance(next(cnodes), BioCypherNode):
                logger.warn(
                    "It appears that the first node is not a BioCypherNode. "
                    "Nodes must be passed as type BioCypherNode. "
                    "Please use the generic add_edges() function."
                )
                return (False, False)
            else:
                s = sum(1 for _ in cnodes) + 1
                logger.info("Merging %s nodes." % s)

        # receive single nodes or node lists
        else:
            if type(nodes) is not list:
                nodes = [nodes]
            if not all(isinstance(n, BioCypherNode) for n in nodes):
                logger.error("Nodes must be passed as type BioCypherNode.")
                return (False, False)
            else:
                logger.info("Merging %s nodes." % len(nodes))

        entities = [node.get_dict() for node in nodes]

        entity_query = (
            "UNWIND $entities AS ent "
            "CALL apoc.merge.node([ent.node_label], "
            "{id: ent.node_id}, ent.properties, ent.properties) "
            "YIELD node "
            "RETURN node"
        )

        if explain:
            return self.explain(
                entity_query, parameters={"entities": entities}
            )
        elif profile:
            return self.profile(
                entity_query, parameters={"entities": entities}
            )
        else:
            res = self.query(entity_query, parameters={"entities": entities})
            logger.info("Finished merging nodes.")
            return res

    def add_biocypher_edges(self, edges, explain=False, profile=False):
        """
        Accepts an edge type handoff class (BioCypherEdge) with source
        and target ids, label, and a dict of properties (passing on the
        type of property, ie, int, string ...).

        The individual edge is either passed as a singleton, in the case
        of representation as an edge in the graph, or as a 3-tuple, in
        the case of representation as a node (with two edges connecting
        to interaction partners).

        The dict retrieved by the get_dict() method is passed into Neo4j
        as a map of maps, explicitly encoding source and target ids and
        the relationship label, and adding all edge properties from the
        'properties' key of the dict. The merge is performed via APOC,
        matching only on source and target id to prevent duplicates. The
        same properties are set on match and on create, irrespective of
        the actual event.

        Args:
            edges: a list of BioCypherEdge objects

        Returns:
            bool: The return value. True for success, False otherwise.
        """

        tup = False

        # receive generator objects
        if isinstance(edges, GeneratorType):
            # itertools solution is kind of slow and cumbersome
            # however, needs to detect tuples...

            edges, cedges = itertools.tee(edges)
            cedge = next(cedges)

            if type(cedge) == tuple:
                # create one node and two edges
                tup = True
                cedge = cedge[1]
            if not isinstance(cedge, BioCypherEdge):
                # type error
                logger.warn(
                    "It appears that the first edge is not a BioCypherEdge. "
                    "Nodes must be passed as type BioCypherEdge. "
                    "Please use the generic add_edges() function."
                )
                return (False, False)
            else:
                s = "?"  # sum(1 for _ in cedges) + 1  # not very fast
                logger.info("Merging %s nodes." % s)

        # receive single edges or edge lists
        else:
            if type(edges) is not list:
                edges = [edges]

            # flatten
            if any(isinstance(i, list) for i in edges):
                edges = [item for sublist in edges for item in sublist]

            if type(edges[0]) == tuple:
                tup = True
            elif not all(isinstance(e, BioCypherEdge) for e in edges):
                logger.error("Nodes must be passed as type BioCypherEdge.")
                return (False, False)

            logger.info("Merging %s edges." % len(edges))

        if tup:
            # split up tuples in nodes and edges if detected
            z = zip(*((e[0], list(e[1:3])) for e in edges))
            nod, edg = [list(a) for a in z]
            self.add_biocypher_nodes(nod)
            self.add_biocypher_edges(edg)

        # cypher query
        else:
            rels = [edge.get_dict() for edge in edges]

            # merging only on the ids of the entities, passing the
            # properties on match and on create;
            # TODO add node labels?
            node_query = (
                "UNWIND $rels AS r "
                "MERGE (src {id: r.source_id}) "
                "MERGE (tar {id: r.target_id}) "
            )
            self.query(node_query, parameters={"rels": rels})

            edge_query = (
                "UNWIND $rels AS r "
                "MATCH (src {id: r.source_id}) "
                "MATCH (tar {id: r.target_id}) "
                "WITH src, tar, r "
                "CALL apoc.merge.relationship"
                "(src, r.relationship_label, NULL, "
                "r.properties, tar, r.properties) "
                "YIELD rel "
                "RETURN rel"
            )

            if explain:
                return self.explain(edge_query, parameters={"rels": rels})
            elif profile:
                return self.profile(edge_query, parameters={"rels": rels})
            else:
                res = self.query(edge_query, parameters={"rels": rels})
                logger.info("Finished merging edges.")
                return res

    def write_nodes(self, nodes, dirname=None):
        """
        Write BioCypher nodes to disk using the :py:mod:`write` module,
        formatting the CSV to enable Neo4j admin import from the target
        directory.
        """

        # instantiate adapter on demand because it takes time to load
        # the biolink model toolkit
        if not self.bl_adapter:
            self.bl_adapter = BiolinkAdapter(self.db_meta.leaves)

        if not self.batch_writer:
            self.batch_writer = BatchWriter(
                self.db_meta.schema, self.bl_adapter, dirname=dirname
            )

        # write header files
        self.batch_writer.write_nodes()

        # contains types of nodes and edges and
        # their designations in the input data

        # write content (in batches if required)
        nodes  # contains node data with input designations that need to
        # be translated to biocypher designations
        pass

    def write_edges(self, edges):
        pass
