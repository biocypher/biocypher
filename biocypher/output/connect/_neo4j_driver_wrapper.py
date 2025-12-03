"""
Neo4j connection management and Cypher interface.

A wrapper around the Neo4j driver which handles the DBMS connection and
provides basic management methods. This module is only used when BioCypher
is configured for online mode with Neo4j.
"""

from __future__ import annotations

import contextlib
import itertools
import os
import re
import warnings

from typing import Literal

import appdirs
import yaml

from biocypher._logger import logger
from biocypher._misc import to_list

__all__ = ["CONFIG_FILES", "DEFAULT_CONFIG", "Neo4jDriver"]

# Try to import Neo4j driver, but don't fail if not available
try:
    import neo4j
    import neo4j.exceptions as neo4j_exc

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    neo4j = None
    neo4j_exc = None

CONFIG_FILES = Literal["neo4j.yaml", "neo4j.yml"]
DEFAULT_CONFIG = {
    "user": "neo4j",
    "passwd": "neo4j",
    "db": "neo4j",
    "uri": "neo4j://localhost:7687",
    "fetch_size": 1000,
    "raise_errors": False,
    "fallback_db": ("system", "neo4j"),
    "fallback_on": ("TransientError",),
}


def _to_tuple(value):
    """Ensure that value is a tuple."""
    return tuple(to_list(value))


def _to_set(value):
    """Ensure that value is a set."""
    return set(to_list(value))


def _if_none(*values):
    """Use the first item from values that is not None."""
    for v in values:
        if v is not None:
            return v
    return None


def _pretty_profile(d, lines=None, indent=0):
    """
    Pretty format a Neo4j profile dict.

    Takes Neo4j profile dictionary and an optional header as
    list and creates a list of strings to be printed.

    Args:
        d: Profile dictionary or list
        lines: Optional list to append to
        indent: Indentation level

    Returns:
        List of formatted strings
    """
    if lines is None:
        lines = []

    # ANSI color codes for terminal output
    OKBLUE = "\033[94m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"

    # if more items, branch
    if d:
        if isinstance(d, list):
            for sd in d:
                _pretty_profile(sd, lines, indent)
        elif isinstance(d, dict):
            typ = d.pop("operatorType", None)
            if typ:
                lines.append(("\t" * indent) + "|" + "\t" + f"{OKBLUE}Step: {typ} {ENDC}")

            # buffer children
            chi = d.pop("children", None)

            for key, value in d.items():
                if key == "args":
                    _pretty_profile(value, lines, indent)
                # both are there for some reason, sometimes
                # both in the same process
                elif key == "Time" or key == "time":
                    lines.append(
                        ("\t" * indent) + "|" + "\t" + str(key) + ": " + f"{WARNING}{value:,}{ENDC}".replace(",", " ")
                    )
                else:
                    lines.append(("\t" * indent) + "|" + "\t" + str(key) + ": " + str(value))

            # now the children
            _pretty_profile(chi, lines, indent + 1)

    return lines


def _get_neo4j_version(driver) -> str | None:
    """
    Get Neo4j version from the database.

    Args:
        driver: Neo4j driver instance

    Returns:
        Version string or None if unavailable
    """
    if not NEO4J_AVAILABLE or not driver:
        return None

    try:
        with driver.session() as session:
            result = session.run(
                """
                CALL dbms.components()
                YIELD name, versions, edition
                UNWIND versions AS version
                RETURN version AS version
                """
            )
            data = result.data()
            if data:
                return data[0]["version"]
    except Exception as e:
        logger.warning(f"Error detecting Neo4j version: {e}")
    return None


class Neo4jDriver:
    """
    Manage the connection to the Neo4j server.

    A wrapper around the Neo4j driver that handles database connections
    and provides convenient methods for querying and managing the database.
    """

    _connect_essential = ("uri", "user", "passwd")

    def __init__(
        self,
        driver: neo4j.Driver | Neo4jDriver | None = None,
        db_name: str | None = None,
        db_uri: str | None = None,
        db_user: str | None = None,
        db_passwd: str | None = None,
        config: CONFIG_FILES | None = None,
        fetch_size: int = 1000,
        raise_errors: bool | None = None,
        wipe: bool = False,
        offline: bool = False,
        fallback_db: str | tuple[str] | None = None,
        fallback_on: str | set[str] | None = None,
        multi_db: bool | None = None,
        force_enterprise: bool = False,
        **kwargs,
    ):
        """
        Create a Driver object with database connection and runtime parameters.

        Args:
            driver:
                A neo4j.Driver instance, created by neo4j.GraphDatabase.driver.
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
            raise_errors:
                Raise the errors instead of turning them into log messages
                and returning None.
            config:
                Path to a YAML config file which provides the URI, user
                name and password.
            wipe:
                Wipe the database after connection, ensuring the data is
                loaded into an empty database.
            offline:
                Disable any interaction to the server. Queries won't be
                executed. The config will be still stored in the object
                and it will be ready to go online by its go_online method.
            fallback_db:
                Arbitrary number of fallback databases. If a query fails
                to run against the current database, it will be attempted
                against the fallback databases.
            fallback_on:
                Switch to the fallback databases upon these errors.
            multi_db:
                Whether to use multi-database mode (Neo4j 4.0+).
            kwargs:
                Ignored.
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver is not installed. Install it with: " "pip install neo4j>=5.0")

        self.driver = getattr(driver, "driver", driver)
        self._db_config = {
            "uri": db_uri,
            "user": db_user,
            "passwd": db_passwd,
            "db": db_name,
            "fetch_size": fetch_size,
            "raise_errors": raise_errors,
            "fallback_db": fallback_db,
            "fallback_on": fallback_on,
        }
        self._config_file = config
        self._drivers = {}
        self._queries = {}
        self._offline = offline
        self.multi_db = multi_db
        self._neo4j_version_cache = None
        self._force_enterprise = force_enterprise

        if self.driver:
            logger.info("Using the driver provided.")
            self._config_from_driver()
            self._register_current_driver()
        else:
            logger.info("No driver provided, initialising it from local config.")
            self.db_connect()

        # Detect Community Edition and adjust settings accordingly
        # Default to Community Edition (safer for CI) unless explicitly overridden
        self._detect_and_handle_community_edition()

        self.ensure_db()

        if wipe:
            self.wipe_db()

    def db_connect(self):
        """Connect to the database server."""
        if not self._connect_param_available:
            self.read_config()

        con_param = f"uri={self.uri}, auth=(user, ***)"
        logger.info(f"Attempting to connect: {con_param}")

        if self.offline:
            self.driver = None
            logger.info("Offline mode, not connecting to database.")
        else:
            self.driver = neo4j.GraphDatabase.driver(
                uri=self.uri,
                auth=self.auth,
            )
            logger.info("Opened database connection.")

        self._register_current_driver()

    def _detect_and_handle_community_edition(self):
        """
        Detect Community Edition and adjust settings for compatibility.

        Community Edition doesn't support multi-database, so we:
        1. Convert neo4j:// to bolt:// to avoid routing issues
        2. Disable multi_db mode
        3. Use default database 'neo4j' if a custom database was requested
        """
        if not self.driver or self.offline:
            return

        # If Enterprise Edition is forced, skip detection
        if self._force_enterprise:
            logger.info("Enterprise Edition mode forced. Skipping Community Edition detection.")
            return

        # Check if multi-database is supported (Enterprise Edition)
        # Use bolt:// for detection to avoid routing table issues
        original_uri = self.uri
        detection_uri = original_uri
        if original_uri.startswith("neo4j://"):
            detection_uri = original_uri.replace("neo4j://", "bolt://", 1)
        elif original_uri.startswith("neo4j+s://"):
            detection_uri = original_uri.replace("neo4j+s://", "bolt+s://", 1)

        # Create a temporary driver with bolt:// for detection
        temp_driver = None
        supports_multi_db = False
        try:
            temp_driver = neo4j.GraphDatabase.driver(uri=detection_uri, auth=self.auth)
            with temp_driver.session(database="neo4j") as session:
                result = session.run(
                    """
                    CALL dbms.components()
                    YIELD edition
                    RETURN edition CONTAINS 'enterprise' AS is_enterprise
                    """
                )
                data = result.data()
                supports_multi_db = data[0].get("is_enterprise", False) if data else False
        except Exception as e:
            logger.debug(f"Error detecting Neo4j edition: {e}. Assuming Community Edition.")
            # If detection fails, assume Community Edition (safer)
            supports_multi_db = False
        finally:
            if temp_driver:
                temp_driver.close()

        # If Community Edition or detection failed, adjust settings
        if not supports_multi_db:
            logger.info(
                "Neo4j Community Edition detected (or detection failed). "
                "Multi-database features are not available. "
                "Adjusting configuration for compatibility."
            )

            # Convert neo4j:// to bolt:// to avoid routing table issues
            # (already converted for detection, but need to update main driver)
            try:
                if original_uri.startswith("neo4j://"):
                    bolt_uri = original_uri.replace("neo4j://", "bolt://", 1)
                    self._db_config["uri"] = bolt_uri
                    logger.info(f"Converted URI from {original_uri} to {bolt_uri} for Community Edition compatibility.")
                    # Reconnect with bolt://
                    self.driver.close()
                    self.db_connect()
                elif original_uri.startswith("neo4j+s://"):
                    bolt_uri = original_uri.replace("neo4j+s://", "bolt+s://", 1)
                    self._db_config["uri"] = bolt_uri
                    logger.info(f"Converted URI from {original_uri} to {bolt_uri} for Community Edition compatibility.")
                    # Reconnect with bolt+s://
                    self.driver.close()
                    self.db_connect()
            except Exception as e:
                logger.warning(f"Failed to convert URI and reconnect: {e}. Continuing with original URI.")

            # Disable multi_db mode
            if self.multi_db:
                logger.info("Disabling multi-database mode for Community Edition.")
                self.multi_db = False

            # Use default database if a custom database was requested
            current_db = self.current_db
            if current_db and current_db.lower() != "neo4j":
                logger.warning(
                    f"Requested database '{current_db}' is not supported in Community Edition. "
                    f"Falling back to default database 'neo4j'."
                )
                self._db_config["db"] = "neo4j"
                self._register_current_driver()

    @property
    def _connect_param_available(self) -> bool:
        """Check for essential connection parameters."""
        return all(self._db_config.get(k, None) for k in self._connect_essential)

    @property
    def status(
        self,
    ) -> Literal[
        "no driver",
        "no connection",
        "db offline",
        "db online",
        "offline",
    ]:
        """State of this driver object and its current database."""
        if self.offline:
            return "offline"

        if not self.driver:
            return "no driver"

        db_status = self.db_status()
        return f"db {db_status}" if db_status else "no connection"

    @property
    def uri(self) -> str:
        """Database server URI (from config or built-in default)."""
        return self._db_config.get("uri") or DEFAULT_CONFIG["uri"]

    @property
    def auth(self) -> tuple[str, str]:
        """Database server user and password (from config or built-in default)."""
        auth_tuple = self._db_config.get("auth")
        if auth_tuple:
            return tuple(auth_tuple)
        return (
            self._db_config.get("user") or DEFAULT_CONFIG["user"],
            self._db_config.get("passwd") or DEFAULT_CONFIG["passwd"],
        )

    def read_config(self, section: str | None = None):
        """Read the configuration from a YAML file."""
        config_key_synonyms = {
            "password": "passwd",
            "pw": "passwd",
            "username": "user",
            "login": "user",
            "host": "uri",
            "address": "uri",
            "server": "uri",
            "graph": "db",
            "database": "db",
            "name": "db",
        }

        if not self._config_file or not os.path.exists(self._config_file):
            confdirs = (".", appdirs.user_config_dir("biocypher", "biocypher"))
            conffiles = ("neo4j.yaml", "neo4j.yml")

            for config_path_t in itertools.product(confdirs, conffiles):
                config_path_s = os.path.join(*config_path_t)
                if os.path.exists(config_path_s):
                    self._config_file = config_path_s

        if self._config_file and os.path.exists(self._config_file):
            logger.info(f"Reading config from `{self._config_file}`.")

            with open(self._config_file) as fp:
                conf = yaml.safe_load(fp.read())

            for k, v in conf.get(section, conf).items():
                k = k.lower()
                k = config_key_synonyms.get(k, k)

                if not self._db_config.get(k, None):
                    self._db_config[k] = v

        elif not self._connect_param_available:
            logger.warning("No config available, falling back to defaults.")

        self._config_from_defaults()

    def _config_from_driver(self):
        """Extract configuration from an existing driver."""
        from_driver = {
            "uri": self._uri(
                host=getattr(self.driver, "default_host", None),
                port=getattr(self.driver, "default_port", None),
            ),
            "db": self.current_db,
            "fetch_size": getattr(
                getattr(self.driver, "_default_workspace_config", None),
                "fetch_size",
                None,
            ),
            "user": self.user,
            "passwd": self.passwd,
        }

        for k, v in from_driver.items():
            self._db_config[k] = self._db_config.get(k, v) or v

        self._config_from_defaults()

    def _config_from_defaults(self):
        """Populate missing config items by their default values."""
        for k, v in DEFAULT_CONFIG.items():
            if self._db_config.get(k, None) is None:
                self._db_config[k] = v

    def _register_current_driver(self):
        """Register the current driver for the current database."""
        self._drivers[self.current_db] = self.driver

    @staticmethod
    def _uri(
        host: str = "localhost",
        port: str | int = 7687,
        protocol: str = "neo4j",
    ) -> str:
        """Construct a Neo4j URI."""
        return f"{protocol}://{host}:{port}/"

    def close(self):
        """Close the Neo4j driver if it exists and is open."""
        if hasattr(self, "driver") and hasattr(self.driver, "close"):
            self.driver.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

    @property
    def current_db(self) -> str:
        """Name of the current database."""
        return self._db_config["db"] or self._driver_con_db or self.home_db or neo4j.DEFAULT_DATABASE

    @current_db.setter
    def current_db(self, name: str):
        """Set the database currently in use."""
        self._db_config["db"] = name
        self.db_connect()

    @property
    def _driver_con_db(self) -> str | None:
        """Get the database from the driver connection."""
        if not self.driver:
            return None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                driver_con = self.driver.verify_connectivity()
            except neo4j_exc.ServiceUnavailable:
                logger.error("Cannot access Neo4j server.")
                return None

        if driver_con:
            first_con = next(iter(driver_con.values()))[0]
            return first_con.get("db", None)

        return None

    @property
    def home_db(self) -> str | None:
        """Home database of the current user."""
        return self._db_name("HOME")

    @property
    def default_db(self) -> str | None:
        """Default database of the server."""
        return self._db_name("DEFAULT")

    def _db_name(self, which: Literal["HOME", "DEFAULT"] = "HOME") -> str | None:
        """Get the HOME or DEFAULT database name."""
        try:
            resp, summary = self.query(
                f"SHOW {which} DATABASE;",
                fallback_db=self._get_fallback_db,
            )
        except (neo4j_exc.AuthError, neo4j_exc.ServiceUnavailable) as e:
            logger.error(f"No connection to Neo4j server: {e}")
            return None

        if resp:
            return resp[0]["name"]
        return None

    @property
    def _get_fallback_db(self) -> tuple[str]:
        """Get fallback database tuple."""
        return _to_tuple(getattr(self, "_fallback_db", None) or self._db_config["fallback_db"])

    @property
    def _get_fallback_on(self) -> set[str]:
        """Get fallback error types."""
        return _to_set(getattr(self, "_fallback_on", None) or self._db_config["fallback_on"])

    def query(
        self,
        query: str,
        db: str | None = None,
        fetch_size: int | None = None,
        write: bool = True,
        explain: bool = False,
        profile: bool = False,
        fallback_db: str | tuple[str] | None = None,
        fallback_on: str | set[str] | None = None,
        raise_errors: bool | None = None,
        parameters: dict | None = None,
        **kwargs,
    ) -> tuple[list[dict] | None, neo4j.work.summary.ResultSummary | None]:
        """
        Run a Cypher query.

        Args:
            query:
                A valid Cypher query.
            db:
                The DB inside the Neo4j server that should be queried.
            fetch_size:
                The Neo4j fetch size parameter.
            write:
                Indicates whether to address write- or read-servers.
            explain:
                Indicates whether to EXPLAIN the Cypher query.
            profile:
                Indicates whether to PROFILE the Cypher query.
            fallback_db:
                If the query fails, try to execute it against a fallback database.
            fallback_on:
                Run queries against the fallback databases in case of these errors.
            raise_errors:
                Raise Neo4j errors instead of only printing them.
            parameters:
                Parameters dictionary for the query.
            **kwargs:
                Additional parameters (deprecated, use parameters dict instead).

        Returns:
            2-tuple:
                - neo4j.Record.data: the Neo4j response to the query
                - neo4j.ResultSummary: information about the result
        """
        if explain:
            query = "EXPLAIN " + query
        elif profile:
            query = "PROFILE " + query

        if self.offline:
            logger.info(f"Offline mode, not running query: `{query}`.")
            return None, None

        if not self.driver:
            if raise_errors:
                raise RuntimeError("Driver is not available. The driver may be closed or in offline mode.")
            logger.error("Driver is not available. Cannot execute query.")
            return None, None

        # Check if driver is closed (Neo4j 5.x driver has _closed attribute)
        if hasattr(self.driver, "_closed") and self.driver._closed:
            if raise_errors:
                raise RuntimeError("Driver is closed. Please reconnect or create a new driver instance.")
            logger.error("Driver is closed. Cannot execute query.")
            return None, None

        db = db or self._db_config["db"] or neo4j.DEFAULT_DATABASE
        fetch_size = fetch_size or self._db_config["fetch_size"]
        raise_errors = self._db_config["raise_errors"] if raise_errors is None else raise_errors

        # Combine parameters dict with kwargs (kwargs for backward compatibility)
        query_params = dict(parameters or {}, **kwargs)

        # Neo4j 5+ uses database parameter, older versions use it conditionally
        session_kwargs = {
            "fetch_size": fetch_size,
            "default_access_mode": (neo4j.WRITE_ACCESS if write else neo4j.READ_ACCESS),
        }

        # For Neo4j 4.0+, use database parameter if multi_db is True
        # For Neo4j 5.0+, always use database parameter
        if self.multi_db or self._is_neo4j_5_plus():
            session_kwargs["database"] = db

        try:
            with self.session(**session_kwargs) as session:
                # Neo4j driver expects parameters via the 'parameters' argument,
                # not unpacked as kwargs. This ensures query parameters are correctly
                # passed to the Cypher query and prevents conflicts with method parameters.
                if query_params:
                    res = session.run(query, parameters=query_params)
                else:
                    res = session.run(query)
                return res.data(), res.consume()

        except (neo4j_exc.Neo4jError, neo4j_exc.DriverError) as e:
            fallback_db = fallback_db or getattr(self, "_fallback_db", ())
            fallback_on = _to_set(_if_none(fallback_on, self._get_fallback_on))

            if self._match_error(e, fallback_on):
                for fdb in _to_tuple(fallback_db):
                    if fdb != db:
                        logger.warning(f"Running query against fallback database `{fdb}`.")
                        return self.query(
                            query=query,
                            db=fdb,
                            fetch_size=fetch_size,
                            write=write,
                            fallback_on=set(),
                            raise_errors=raise_errors,
                            parameters=query_params,
                        )

            logger.error(f"Failed to run query: {e.__class__.__name__}: {e}")
            logger.error(f"The error happened with this query: {query}")

            if e.__class__.__name__ == "AuthError":
                logger.error("Authentication error, switching to offline mode.")
                self.go_offline()

            if raise_errors:
                raise

            return None, None

    def _is_neo4j_5_plus(self) -> bool:
        """Check if Neo4j version is 5.0 or higher."""
        if self._neo4j_version_cache is None:
            version_str = _get_neo4j_version(self.driver)
            if version_str:
                try:
                    major_version = int(version_str.split(".")[0])
                    self._neo4j_version_cache = major_version >= 5
                except (ValueError, IndexError):
                    self._neo4j_version_cache = False
            else:
                self._neo4j_version_cache = False
        return self._neo4j_version_cache

    def explain(self, query, db=None, fetch_size=None, write=True, **kwargs):
        """
        Explain a query and pretty print the output.

        Args:
            query: Cypher query to explain
            db: Database name
            fetch_size: Fetch size
            write: Write access mode
            **kwargs: Query parameters

        Returns:
            2-tuple:
                - dict: the raw plan returned by the Neo4j bolt driver
                - list of str: a list of strings ready for printing
        """
        logger.info("Explaining a query.")
        data, summary = self.query(query, db, fetch_size, write, explain=True, **kwargs)

        if not summary:
            return None, []

        plan = summary.plan
        printout = _pretty_profile(plan)

        return plan, printout

    def profile(self, query, db=None, fetch_size=None, write=True, **kwargs):
        """
        Profile a query and pretty print the output.

        Args:
            query: Cypher query to profile
            db: Database name
            fetch_size: Fetch size
            write: Write access mode
            **kwargs: Query parameters

        Returns:
            2-tuple:
                - dict: the raw profile returned by the Neo4j bolt driver
                - list of str: a list of strings ready for printing
        """
        logger.info("Profiling a query.")
        data, summary = self.query(query, db, fetch_size, write, profile=True, **kwargs)

        if not summary:
            return None, []

        prof = summary.profile
        exec_time = summary.result_available_after + summary.result_consumed_after

        # get print representation
        header = f"Execution time: {exec_time:n}\n"
        printout = _pretty_profile(prof, [header], indent=0)

        return prof, printout

    def db_exists(self, name: str | None = None) -> bool:
        """Check if a database exists."""
        return bool(self.db_status(name=name))

    def db_status(
        self,
        name: str | None = None,
        field: str = "currentStatus",
    ) -> Literal["online", "offline"] | str | dict | None:
        """
        Get the current status or other state info of a database.

        Args:
            name: Name of a database
            field: The field to return

        Returns:
            The status as a string, None if the database does not exist.
            If field is None, a dictionary with all fields will be returned.
        """
        name = name or self.current_db
        query = f'SHOW DATABASES WHERE name = "{name}";'

        # Use fallback context manager like original neo4j_utils
        # This allows query to default to current_db and fallback to system/neo4j on error
        with self.fallback():
            resp, summary = self.query(query)

        if resp:
            return resp[0].get(field, resp[0])
        return None

    def db_online(self, name: str | None = None) -> bool:
        """Check if a database is currently online."""
        return self.db_status(name=name) == "online"

    def create_db(self, name: str | None = None):
        """Create a database if it does not already exist."""
        self._manage_db("CREATE", name=name, options="IF NOT EXISTS")

    def start_db(self, name: str | None = None):
        """Start a database (bring it online) if it is offline."""
        self._manage_db("START", name=name)

    def stop_db(self, name: str | None = None):
        """Stop a database, making sure it's offline."""
        self._manage_db("STOP", name=name)

    def drop_db(self, name: str | None = None):
        """Delete a database if it exists."""
        self._manage_db("DROP", name=name, options="IF EXISTS")

    def _manage_db(
        self,
        cmd: Literal["CREATE", "START", "STOP", "DROP"],
        name: str | None = None,
        options: str | None = None,
    ):
        """Execute a database management command."""
        # Use fallback_db like original neo4j_utils
        # Query defaults to current_db, but fallback mechanism will retry against system/neo4j
        self.query(
            f"{cmd} DATABASE {name or self.current_db} {options or ''};",
            fallback_db=self._get_fallback_db,
        )

    def wipe_db(self):
        """Delete all contents of the current database."""
        if not self.driver:
            raise RuntimeError(
                "Driver is not available. Cannot wipe database. " "The driver may be closed or in offline mode."
            )

        # Check if driver is closed (Neo4j 5.x driver has _closed attribute)
        if hasattr(self.driver, "_closed") and self.driver._closed:
            raise RuntimeError(
                "Driver is closed. Cannot wipe database. " "Please reconnect or create a new driver instance."
            )

        # Ensure database exists before trying to wipe it
        self.ensure_db()

        # For Community Edition, use default database if current_db is not supported
        # Skip this check if Enterprise Edition is forced
        db_to_wipe = self.current_db
        if not self._force_enterprise:
            current_uri = self.uri
            is_neo4j_protocol = current_uri.startswith("neo4j://") or current_uri.startswith("neo4j+s://")
            is_non_default_db = db_to_wipe and db_to_wipe.lower() != "neo4j"
            is_community_edition = not self.multi_db or (is_neo4j_protocol and is_non_default_db)

            if is_community_edition and is_non_default_db:
                logger.warning(
                    f"Cannot wipe database '{db_to_wipe}' in Community Edition. "
                    f"Using default database 'neo4j' instead. "
                    f"Database will remain 'neo4j' for this session."
                )
                # Permanently change to default database for Community Edition
                db_to_wipe = "neo4j"
                self._db_config["db"] = "neo4j"
                self._register_current_driver()

        logger.info(f"Wiping database `{db_to_wipe}`.")
        self.query("MATCH (n) DETACH DELETE n;")
        self.drop_indices_constraints()

    def ensure_db(self):
        """Make sure the database exists and is online."""
        db_name = self.current_db

        # Skip if offline mode
        if self.offline:
            logger.debug(f"Offline mode, skipping database creation for '{db_name}'.")
            return

        # If Enterprise Edition is forced, skip Community Edition checks
        if self._force_enterprise:
            logger.debug(f"Enterprise Edition forced, proceeding with database check for '{db_name}'.")
            # Continue to database existence check below
        else:
            # In Community Edition, multi-database operations are not supported
            # The default database 'neo4j' always exists and is always online
            # Also skip if URI is bolt:// (which indicates Community Edition or direct connection)
            # If URI is still neo4j:// and we're checking a non-default database, assume Community Edition
            current_uri = self.uri
            is_bolt = current_uri.startswith("bolt://") or current_uri.startswith("bolt+s://")
            is_neo4j_protocol = current_uri.startswith("neo4j://") or current_uri.startswith("neo4j+s://")
            is_non_default_db = db_name and db_name.lower() != "neo4j"

            if not self.multi_db or is_bolt or (is_neo4j_protocol and is_non_default_db):
                if not self.multi_db:
                    logger.debug(
                        f"Multi-database mode disabled (Community Edition). "
                        f"Using default database '{db_name}' which always exists."
                    )
                elif is_bolt:
                    logger.debug(
                        f"Using bolt:// connection (direct mode). "
                        f"Using default database '{db_name}' which always exists."
                    )
                else:
                    logger.debug(
                        f"Using neo4j:// protocol with non-default database '{db_name}' - "
                        f"assuming Community Edition and skipping database check."
                    )
                return

        # Check if database exists, create if needed
        try:
            exists = self.db_exists()
            if not exists:
                logger.info(f"Database '{db_name}' does not exist, creating it...")
                self.create_db()
                # Verify creation succeeded
                if not self.db_exists():
                    raise RuntimeError(
                        f"Failed to create database '{db_name}'. " "The database was not created successfully."
                    )
                logger.info(f"Database '{db_name}' created successfully.")
            else:
                logger.debug(f"Database '{db_name}' already exists.")
        except Exception as e:
            logger.error(f"Failed to check/create database '{db_name}': {e}")
            # Re-raise to prevent initialization from continuing with a missing database
            raise RuntimeError(
                f"Failed to ensure database '{db_name}' exists: {e}. "
                "Please check Neo4j permissions and that the database can be created."
            ) from e

        # Check if database is online, start if needed
        try:
            if not self.db_online():
                logger.info(f"Database '{db_name}' is offline, starting it...")
                self.start_db()
                # Verify start succeeded
                if not self.db_online():
                    raise RuntimeError(
                        f"Failed to start database '{db_name}'. " "The database was not started successfully."
                    )
                logger.info(f"Database '{db_name}' started successfully.")
            else:
                logger.debug(f"Database '{db_name}' is already online.")
        except Exception as e:
            logger.error(f"Failed to check/start database '{db_name}': {e}")
            # Re-raise to prevent initialization from continuing with an offline database
            raise RuntimeError(
                f"Failed to ensure database '{db_name}' is online: {e}. "
                "Please check Neo4j permissions and that the database can be started."
            ) from e

    def select_db(self, name: str):
        """Set the current database."""
        current = self.current_db

        if current != name:
            self._register_current_driver()
            self._db_config["db"] = name

            if name in self._drivers:
                self.driver = self._drivers[name]
            else:
                self.db_connect()

    @property
    def indices(self) -> list | None:
        """List of indices in the current database."""
        return self._list_indices("indices")

    @property
    def constraints(self) -> list | None:
        """List of constraints in the current database."""
        return self._list_indices("constraints")

    def drop_indices_constraints(self):
        """Drop all indices and constraints in the current database."""
        # Neo4j 5+ handles constraints and indexes together
        self.drop_constraints()
        # For older versions, also drop indexes separately
        if not self._is_neo4j_5_plus():
            self.drop_indices()

    def drop_constraints(self):
        """Drop all constraints in the current database."""
        self._drop_indices(what="constraints")

    def drop_indices(self):
        """Drop all indices in the current database."""
        self._drop_indices(what="indexes")

    def _drop_indices(
        self,
        what: Literal["indexes", "indices", "constraints"] = "constraints",
    ):
        """Drop indices or constraints.

        Compatible with Neo4j 4.x and 5.x. Uses SHOW syntax which is
        available in both versions.
        """
        what_u = self._idx_cstr_synonyms(what)

        with self.session() as s:
            try:
                # SHOW INDEXES and SHOW CONSTRAINTS work in both Neo4j 4.x and 5.x
                # Neo4j 5.x unified constraints and indexes, but separate commands still work
                if what == "constraints":
                    query = "SHOW CONSTRAINTS"
                elif what in ("indexes", "indices"):
                    query = "SHOW INDEXES"
                else:
                    query = f"SHOW {what_u}S"  # Plural form

                indices = s.run(query)
                indices = list(indices)
                n_indices = len(indices)
                index_names = ", ".join(i["name"] for i in indices)

                for idx in indices:
                    s.run(f"DROP {what_u} `{idx['name']}` IF EXISTS")

                logger.info(f"Dropped {n_indices} {what}: {index_names}.")

            except (neo4j_exc.Neo4jError, neo4j_exc.DriverError) as e:
                logger.error(f"Failed to run query: {e}")

    def _list_indices(
        self,
        what: Literal["indexes", "indices", "constraints"] = "constraints",
    ) -> list | None:
        """List indices or constraints."""
        what_u = self._idx_cstr_synonyms(what)

        with self.session() as s:
            try:
                return list(s.run(f"SHOW {what_u.upper()};"))
            except (neo4j_exc.Neo4jError, neo4j_exc.DriverError) as e:
                logger.error(f"Failed to run query: {e}")
                return None

    @staticmethod
    def _idx_cstr_synonyms(what: str) -> str:
        """Convert index/constraint keyword to Cypher keyword."""
        what_s = {
            "indexes": "INDEX",
            "indices": "INDEX",
            "constraints": "CONSTRAINT",
        }

        what_u = what_s.get(what, None)

        if not what_u:
            msg = f'Allowed keywords are: "indexes", "indices" or "constraints", ' f"not `{what}`."
            logger.error(msg)
            raise ValueError(msg)

        return what_u

    @property
    def node_count(self) -> int | None:
        """Number of nodes in the database."""
        res, summary = self.query("MATCH (n) RETURN COUNT(n) AS count;")
        return res[0]["count"] if res else None

    @property
    def edge_count(self) -> int | None:
        """Number of edges in the database."""
        res, summary = self.query("MATCH ()-[r]->() RETURN COUNT(r) AS count;")
        return res[0]["count"] if res else None

    @property
    def user(self) -> str | None:
        """User for the currently active connection."""
        return self._extract_auth[0]

    @property
    def passwd(self) -> str | None:
        """Password for the currently active connection."""
        return self._extract_auth[1]

    @property
    def _extract_auth(self) -> tuple[str | None, str | None]:
        """Extract authentication data from the Neo4j driver."""
        auth = None, None

        if self.driver:
            opener_vars = self._opener_vars
            if "auth" in opener_vars:
                auth = opener_vars["auth"].cell_contents

        return auth

    @property
    def _opener_vars(self) -> dict:
        """Extract variables from the opener part of the Neo4j driver."""
        return dict(
            zip(
                self.driver._pool.opener.__code__.co_freevars,
                self.driver._pool.opener.__closure__,
            ),
        )

    def __len__(self):
        """Return the number of nodes in the database."""
        return self.node_count or 0

    @contextlib.contextmanager
    def use_db(self, name: str):
        """Context manager where the default database is set to name."""
        used_previously = self.current_db
        self.select_db(name=name)

        try:
            yield None
        finally:
            self.select_db(name=used_previously)

    @contextlib.contextmanager
    def fallback(
        self,
        db: str | tuple[str] | None = None,
        on: str | set[str] | None = None,
    ):
        """
        Context manager that attempts to run queries against a fallback database
        if running against the default database fails.
        """
        prev = {}

        for var in ("db", "on"):
            prev[var] = getattr(self, f"_fallback_{var}", None)
            setattr(
                self,
                f"_fallback_{var}",
                locals()[var] or self._db_config.get(f"fallback_{var}"),
            )

        try:
            yield None
        finally:
            for var in ("db", "on"):
                setattr(self, f"_fallback_{var}", prev[var])

    @contextlib.contextmanager
    def session(self, **kwargs):
        """Context manager with a database connection session."""
        if not self.driver:
            raise RuntimeError("Driver is not available. The driver may be closed or in offline mode.")

        # Check if driver is closed
        if hasattr(self.driver, "_closed") and self.driver._closed:
            raise RuntimeError("Driver is closed. Please reconnect or create a new driver instance.")

        session = self.driver.session(**kwargs)

        try:
            yield session
        finally:
            session.close()

    def __enter__(self):
        """Context manager entry."""
        self._context_session = self.session()
        return self._context_session

    def __exit__(self, *exc):
        """Context manager exit."""
        if hasattr(self, "_context_session"):
            self._context_session.close()
            delattr(self, "_context_session")

    def __repr__(self):
        """String representation."""
        return f"<{self.__class__.__name__} " f"{self._connection_str if self.driver else '[offline]'}>"

    @property
    def _connection_str(self) -> str:
        """Connection string representation."""
        if not self.driver:
            return "unknown://unknown:0/unknown"

        protocol = re.split(
            r"(?<=[a-z])(?=[A-Z])",
            self.driver.__class__.__name__,
        )[0].lower()

        address = self.driver._pool.address if hasattr(self.driver, "_pool") else ("unknown", 0)

        return f"{protocol}://{address[0]}:{address[1]}/{self.user or 'unknown'}"

    @property
    def offline(self) -> bool:
        """Whether the driver is in offline mode."""
        return self._offline

    @offline.setter
    def offline(self, offline: bool):
        """Enable or disable offline mode."""
        self.go_offline() if offline else self.go_online()

    @property
    def apoc_version(self) -> str | None:
        """
        Version of the APOC plugin available in the current database.

        Returns:
            APOC version string or None if APOC is not available
        """
        # Check if driver is available before attempting to query
        if not self.driver or self.offline:
            return None

        # Check if driver is closed
        if hasattr(self.driver, "_closed") and self.driver._closed:
            return None

        db = self._db_config["db"] or neo4j.DEFAULT_DATABASE

        try:
            with self.session(database=db) as session:
                res = session.run("RETURN apoc.version() AS output;")
                data = res.data()
                if data:
                    return data[0]["output"]
        except (neo4j_exc.ClientError, RuntimeError):
            # RuntimeError can be raised if driver is offline/closed
            # ClientError is raised if APOC is not available
            return None
        except Exception:
            # Catch any other exceptions (e.g., connection errors) and return None
            return None
        return None

    @property
    def has_apoc(self) -> bool:
        """
        Check if APOC is available in the current database.

        Returns:
            True if APOC is available, False otherwise
        """
        try:
            return bool(self.apoc_version)
        except Exception:
            # Ensure has_apoc always returns a boolean, even if apoc_version raises
            return False

    def go_offline(self):
        """Switch to offline mode."""
        self._offline = True
        self.close()
        self.driver = None
        self._register_current_driver()
        logger.warning("Offline mode: any interaction to the server is disabled.")

    def go_online(
        self,
        db_name: str | None = None,
        db_uri: str | None = None,
        db_user: str | None = None,
        db_passwd: str | None = None,
        config: CONFIG_FILES | None = None,
        fetch_size: int | None = None,
        raise_errors: bool | None = None,
        wipe: bool = False,
    ):
        """Switch to online mode."""
        self._offline = False

        try:
            for k, current in self._db_config.items():
                self._db_config[k] = _if_none(
                    locals().get(k.replace("db_", ""), None),
                    current,
                    DEFAULT_CONFIG.get(k),
                )

            self._config_file = self._config_file or config

            self.db_connect()
            self.ensure_db()
            logger.info("Online mode: ready to run queries.")

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._offline = True

        if wipe:
            self.wipe_db()

    @staticmethod
    def _match_error(error: Exception | str, errors: set[Exception | str]) -> bool:
        """Check if error is listed in errors."""
        import builtins

        def str_to_exc(e):
            if isinstance(e, Exception):
                return e.__class__
            elif isinstance(e, str):
                return getattr(builtins, e, getattr(neo4j_exc, e, e))
            else:
                return e

        error = str_to_exc(error)
        errors = {str_to_exc(e) for e in _to_set(errors)}

        return error in errors or (
            isinstance(error, type) and any(issubclass(error, e) for e in errors if isinstance(e, type))
        )
