# API Reference

## The main BioCypher interface

Create a BioCypher instance by running:

```python
from biocypher import BioCypher
bc = BioCypher()
```

Most of the settings should be configured by [YAML files](../../reference/biocypher-config.md). See [BioCypher](biocypher.md) for details of the BioCypher class.

## Database creation by file

Using the BioCypher instance, you can create a database by writing files by using the `write_nodes` and `write_edges` methods, which accept collections of nodes and edges either as [tuples](../../learn/tutorials/tutorial001_basics.md) or as `BioCypherNode` and `BioCypherEdge` [objects](#base-classes-for-node-and-edge-representations-in-biocypher). For example:

```python
# given lists of nodes and edges
bc.write_nodes(node_list)
bc.write_edges(edge_list)
```

!!! note
    To facilitate the interaction with the various database management systems (DBMSs), BioCypher provides utility functions, such as writing a Neo4j admin import statement to be used for creating a Neo4j database (`write_import_call`). The most commonly used utility functions are also available in the wrapper function `summary`. See the [BioCypher class](biocypher.md) for more information.

Details about the output writing modules responsible for these methods can be found [here](output-write.md).

## In-memory Pandas knowledge graph

BioCypher provides a wrapper around the `pandas.DataFrame` class to facilitate the creation of a knowledge graph in memory. This is useful for testing, small datasets, and for workflows that should remain purely in Python. Example usage:

```python
from biocypher import BioCypher
bc = BioCypher()
# given lists of nodes and edges
bc.add(node_list)
bc.add(edge_list)
# show list of dataframes (one per node/edge type)
dfs = bc.to_df()
```

Details about the in-memory module responsible for these methods can be found [here](output-in-memory.md).

## Database creation and manipulation by Driver

BioCypher also provides a driver for each of the supported DBMSs. The driver can be used to create a database and to write nodes and edges to it, as well as allowing more subtle manipulation usually not encountered in creating a database from scratch as in the [file-based workflow](#database-creation-by-file). This includes merging (creation of entities only if they don't exist) and deletion. For example:

```python
from biocypher import BioCypher
bc = BioCypher()
# given lists of nodes and edges
bc.merge_nodes(node_set_1)
bc.merge_edges(edge_set_1)
bc.merge_nodes(node_set_2)
bc.merge_edges(edge_set_2)
```

Details about the connector module responsible for these methods can be found [here](output-driver.md).

## Download and cache functionality

BioCypher provides a download and cache functionality for resources. Resources are defined via the abstract `Resource` class, which have a name, a (set of) URL(s), and a lifetime (in days, set to 0 for infinite). Two classes inherit from the `Resource` class, the `FileDownload` class and `APIRequest` class. The `Downloader` can deal with single files, lists of files, compressed files, and directories (which needs to be indicated using the `is_dir` parameter of the `FileDownload`). It uses [Pooch](https://www.fatiando.org/pooch/latest/) under the hood to handle the downloading of files and Python's [requests](https://pypi.org/project/requests/) library to perform API requests. Example usage:

```python
from biocypher import BioCypher, FileDownload, APIRequest
bc = BioCypher()

resource1 = FileDownload(
    name="file_list_resource",
    url_s=[
        "https://example.com/file_download1.txt",
        "https://example.com/file_download2.txt"
    ],
    lifetime=1
)
resource2 = FileDownload(
    name="zipped_resource",
    url_s="https://example.com/file_download3.zip",
    lifetime=7
)
resource3 = FileDownload(
    name="directory_resource",
    url_s="https://example.com/file_download4/",
    lifetime=7,
    is_dir=True,
)
resource4 = APIRequest(
    name="list_api_request",
    url_s=[
        "https://api.example.org/api_request1",
        "https://api.example.org/api_request2",
    ],
    life_time=7,
)
resource5 = APIRequest(
    name="api_request",
    url_s="https://api.example.org/api_request1",
    life_time=7,
)
resource_list = [resource1, resource2, resource3, resource4, resource5]
paths = bc.download(resource_list)
```

The files and API requests will be stored in the cache directory, in subfolders
according to the names of the resources, and additionally determined by Pooch
(e.g., extraction of zip files can result in multiple new files). All paths of
downloaded files are returned by the `download` method. The `Downloader` class
can also be used directly, without the BioCypher instance. You can set the cache
directory in the configuration file; if not set, it will use the
`TemporaryDirectory.name()` method from the `tempfile` module. More details
about the `Resource`, `FileDownload`, `APIRequest` and `Downloader` classes can
be found [here](download-cache.md).

## Ontology ingestion, parsing, and manipulation

BioCypher has dedicated modules for processing ontologies, details
[here](ontology.md).

## Base classes for node and edge representations in BioCypher

BioCypher has abstract graph handling for internal use, details
[here](graph-handling.md).

## Translation functionality for implemented types of representation

BioCypher translates between input data types and the ontology-mapped internal
representation of the graph, details [here](translation.md).
