#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright 2021, Heidelberg University Clinic
#
# File author(s): Sebastian Lobentanzer
#                 ...
#
# Distributed under GPLv3 license, see the file `LICENSE`.
#

"""
A wrapper around the Neo4j driver which handles the DBMS connection and
provides basic management methods.
"""

from .logger import logger
logger.debug(f"Loading module {__name__}.")

from typing import Optional
import os

import neo4j


class DriverBase(object):
    """

    Manages the connection to the Neo4j server. Establishes the
    connection and executes queries. A wrapper around the `Driver`
    object from the :py:mod:`neo4j` module, which is stored in the
    :py:attr:`driver` attribute.

    The connection can be defined in three ways:
        * Providing a ready ``neo4j.Driver`` instance
        * By URI and authentication data
        * By a YAML config file

    Args:
        driver:
            A ``neo4j.Driver`` instance, created by, for example,
            ``neo4j.GraphDatabase.driver``.
        db_name:
            Name of the database (Neo4j graph) to use.
        db_uri:
            Protocol, host and port to access the Neo4j server.
        db_user:
            Neo4j user name.
        db_passwd:
            Password of the Neo4j user.
        fetch_size:
            Optional; the fetch size to use in database transactions.
        config:
            Path to a YAML config file which provides the URI, user name
            and password.
        wipe:
            Wipe the database after connection, ensuring the data is
            loaded into an empty database.

    Todo:
        - remove biocypher-specific init args, possible?
    """

    def __init__(
        self,
        driver: Optional[neo4j.Driver]=None,
        db_name: Optionl[str]=None,
        db_uri: Optionl[str]=None,
        db_user: Optionl[str]=None,
        db_passwd: Optionl[str]=None,
        config: Optional[str]="neo4j.yaml",
        fetch_size: int=1000,
        wipe: bool=False,
    ):

        self.driver = driver
        if self.driver:
            logger.info("Loading from supplied driver.")

        if not self.driver:

            logger.info(
                "No driver supplied, initialising driver "
                "from local configuration."
            )
            self._db_config = {
                "uri": db_uri,
                "user": db_user,
                "passwd": db_passwd,
                "db": db_name,
                "fetch_size": fetch_size,
            }

            self._config_file = config_file

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

        connect_essential = ('uri', 'user', 'passwd')

        if not all(self._db_config.get(k, None) for k in connect_essential):

            self.read_config()

        # check for database running?
        self.driver = neo4j.GraphDatabase.driver(
            uri=self.uri,
            auth=self.auth,
        )

        logger.info("Opened database connection.")

    @property
    def uri(self):

        return self._db_config.get("uri", None) or "neo4j://localhost:7687"

    @property
    def auth(self):

        return (
            tuple(self._db_config.get("auth", ())) or
            (self._db_config["user"], self._db_config["passwd"])
        )

    def read_config(self, section: Optional[str]=None):
        """
        Populates the instance configuration from one section of a YAML
        config file.
        """

        if self._config_file and os.path.exists(self._config_file):

            logger.info("Reading config from `%s`." % self._config_file)

            with open(self._config_file, "r") as fp:

                conf = yaml.safe_load(fp.read())

            for k, v in conf.get(section, conf).items():

                if not self.db_config.get(k, None):

                    self._db_config[k] = v

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
            2-tuple:
                - neo4j.Record.data: the Neo4j response to the query, consumed
                  by the shorthand ``.data()`` method on the ``Result`` object
                - neo4j.ResultSummary: information about the result returned
                  by the ``.consume()`` method on the ``Result`` object

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
            query (str): a valid Cypher query (see :meth:`query()`)
            db (str): the DB inside the Neo4j server that should be queried
            fetch_size (int): the Neo4j fetch size parameter
            write (bool): indicates whether to address write- or read-
                servers
            explain (bool): indicates whether to ``EXPLAIN`` the CYPHER
                query and return the ResultSummary
            explain (bool): indicates whether to ``PROFILE`` the CYPHER
                query and return the ResultSummary
            **kwargs: optional objects used in CYPHER interactive mode,
                for instance for passing a parameter dictionary

        Returns:
            2-tuple:
                - dict: the raw profile returned by the Neo4j bolt driver
                - list of str: a list of strings ready for printing
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
    def user(self) -> str:
        """
        User for the currently active connection.

        Returns:
            The name of the user, `None` if no connection or no
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
