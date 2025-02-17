# SQLite

When setting the `dbms` parameter in the `biocypher_config.yaml` to `sqlite`, the BioCypher Knowledge Graph is written to a SQLite database.
[SQLite](https://www.sqlite.org/) is a lightweight relational database management system.
It is suitable for fast prototyping and development. For more mature applications have a look at [PostgreSQL](postgres).

<!--## Install SQLite

TODO-->

## SQLite settings

To overwrite the standard settings of SQLite, add a `sqlite` section to the `biocypher_config.yaml` file.
The following settings are possible:

```{code-block} yaml
:caption: biocypher_config.yaml

sqlite:
  ### SQLite configuration ###

  database_name: sqlite.db # DB name

  # SQLite import batch writer settings
  quote_character: '"'
  delimiter: '\t'
  # import_call_bin_prefix: '' # path to "sqlite3"
  # import_call_file_prefix: '/path/to/files'
```

## Offline mode

### Running BioCypher

After running BioCypher with the ``offline`` parameter set to ``true`` and the ``dbms`` set to ``sqlite``,
the output folder contains:

- ``entity-create_table.sql``: The SQL scripts to create the tables for the nodes/edges. Entity is replaced by your nodes and edges and for each node and edge type an own SQL script is generated.
- ``entity-part000.csv``: The CSV file containing the data for the entity.
- ``sqlite-import-call.sh``: The import script to create a database with the SQL scripts and insert the data from the CSV files.

```{note}
If the ``sqlite-import-call.sh`` is missing, you can create it by running ``bc.write_import_call()``.
```

### Create the SQLite database

To create the SQLite database, run the import script ``sqlite-import-call.sh``.
In the default case (without any changes to the ``database_name``in the configuration), the file containing the database is created with the name ``sqlite.db``.

```{note}
The import script expects, that the sqlite3 command line tool is installed on your system.
```

### Access the SQLite database

Now you can access the created SQLite database.
This can be done with the sqlite3 command line tool.
For example, you can list all tables in the database by running the following command in the terminal:
```bash
sqlite3 sqlite.db "SELECT name FROM sqlite_master WHERE type='table';"
```
