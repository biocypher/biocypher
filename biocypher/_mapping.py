"""
BioCypher 'mapping' module. Handles the mapping of user-defined schema to the
underlying ontology.
"""

import re
import warnings

from typing import Optional
from urllib.request import urlopen

import yaml

from . import _misc
from ._logger import logger

logger.debug(f"Loading module {__name__}.")


class OntologyMapping:
    """
    Class to store the ontology mapping and extensions.
    """

    def __init__(self, config_file: str = None):
        self.schema = self._read_config(config_file)

        self.extended_schema = self._extend_schema()

    def _read_config(self, config_file: str = None):
        """
        Read the configuration file and store the ontology mapping and extensions.
        """
        if config_file is None:
            schema_config = {}

        # load yaml file from web
        elif config_file.startswith("http"):
            with urlopen(config_file) as f:
                schema_config = yaml.safe_load(f)

        # get graph state from config (assume file is local)
        else:
            with open(config_file, "r") as f:
                schema_config = yaml.safe_load(f)

        return schema_config

    def _extend_schema(self, d: Optional[dict] = None) -> dict:
        """
        Get leaves of the tree hierarchy from the data structure dict
        contained in the `schema_config.yaml`. Creates virtual leaves
        (as children) from entries that provide more than one preferred
        id type (and corresponding inputs).

        Args:
            d:
                Data structure dict from yaml file.

        """

        d = d or self.schema

        extended_schema = dict()

        # first pass: get parent leaves with direct representation in ontology
        for k, v in d.items():
            # k is not an entity
            if "represented_as" not in v:
                continue

            # `namespace` is the preferred field name; `preferred_id` is deprecated
            if v.get("namespace") is not None:
                v["preferred_id"] = v.pop("namespace")
            elif v.get("preferred_id") is not None:
                warnings.warn(
                    f"The 'preferred_id' field in schema config entry '{k}' is "
                    "deprecated. Please use 'namespace' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            else:
                v["preferred_id"] = "id"

            # `input_label` is the preferred field name; `label_in_input` is deprecated
            if v.get("input_label") is None and v.get("label_in_input") is not None:
                warnings.warn(
                    f"The 'label_in_input' field in schema config entry '{k}' is "
                    "deprecated. Please use 'input_label' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                v["input_label"] = v.pop("label_in_input")

            # k is an entity that is present in the ontology
            if "is_a" not in v:
                extended_schema[k] = v

        # second pass: "vertical" inheritance
        d = self._vertical_property_inheritance(d)
        for k, v in d.items():
            if "is_a" in v:
                # prevent loops
                if k == v["is_a"]:
                    logger.warning(
                        f"Loop detected in ontology mapping: {k} -> {v}. "
                        "Removing item. Please fix the inheritance if you want "
                        "to use this item."
                    )
                    continue

                extended_schema[k] = v

        # "horizontal" inheritance: create siblings for multiple identifiers or
        # sources -> virtual leaves or implicit children
        mi_leaves = {}
        ms_leaves = {}
        for k, v in d.items():
            # k is not an entity
            if "represented_as" not in v:
                continue

            if isinstance(v.get("preferred_id"), list):
                mi_leaves = self._horizontal_inheritance_pid(k, v)
                extended_schema.update(mi_leaves)

            elif isinstance(v.get("source"), list):
                ms_leaves = self._horizontal_inheritance_source(k, v)
                extended_schema.update(ms_leaves)

        return extended_schema

    def _vertical_property_inheritance(self, d):
        """
        Inherit properties from parents to children and update `d` accordingly.
        """
        for k, v in d.items():
            # k is not an entity
            if "represented_as" not in v:
                continue

            # k is an entity that is present in the ontology
            if "is_a" not in v:
                continue

            # "vertical" inheritance: inherit properties from parent
            if v.get("inherit_properties", False):
                # get direct ancestor
                if isinstance(v["is_a"], list):
                    parent = v["is_a"][0]
                else:
                    parent = v["is_a"]

                # ensure child has properties and exclude_properties
                if "properties" not in v:
                    v["properties"] = {}
                if "exclude_properties" not in v:
                    v["exclude_properties"] = {}

                # update properties of child
                parent_props = self.schema[parent].get("properties", {})
                if parent_props:
                    v["properties"].update(parent_props)

                parent_excl_props = self.schema[parent].get("exclude_properties", {})
                if parent_excl_props:
                    v["exclude_properties"].update(parent_excl_props)

                # update schema (d)
                d[k] = v

        return d

    def _horizontal_inheritance_pid(self, key, value):
        """
        Create virtual leaves for multiple preferred id types or sources.

        If we create virtual leaves, input_label always has to be a list.
        """

        leaves = {}

        preferred_id = value["preferred_id"]
        input_label = value.get("input_label")
        represented_as = value["represented_as"]

        # adjust lengths
        max_l = max(
            [
                len(_misc.to_list(preferred_id)),
                len(_misc.to_list(input_label)),
                len(_misc.to_list(represented_as)),
            ],
        )

        # adjust pid length if necessary
        if isinstance(preferred_id, str):
            pids = [preferred_id] * max_l
        else:
            pids = preferred_id

        # adjust rep length if necessary
        if isinstance(represented_as, str):
            reps = [represented_as] * max_l
        else:
            reps = represented_as

        for pid, lab, rep in zip(pids, input_label, reps):
            skey = pid + "." + key
            svalue = {
                "preferred_id": pid,
                "input_label": lab,
                "represented_as": rep,
                # mark as virtual
                "virtual": True,
            }

            # inherit is_a if exists
            if "is_a" in value.keys():
                # treat as multiple inheritance
                if isinstance(value["is_a"], list):
                    v = list(value["is_a"])
                    v.insert(0, key)
                    svalue["is_a"] = v

                else:
                    svalue["is_a"] = [key, value["is_a"]]

            else:
                # set parent as is_a
                svalue["is_a"] = key

            # inherit everything except core attributes
            for k, v in value.items():
                if k not in [
                    "is_a",
                    "preferred_id",
                    "input_label",
                    "represented_as",
                ]:
                    svalue[k] = v

            leaves[skey] = svalue

        return leaves

    def _horizontal_inheritance_source(self, key, value):
        """
        Create virtual leaves for multiple sources.

        If we create virtual leaves, input_label always has to be a list.
        """

        leaves = {}

        source = value["source"]
        input_label = value.get("input_label")
        represented_as = value["represented_as"]

        # adjust lengths
        src_l = len(source)

        # adjust label length if necessary
        if isinstance(input_label, str):
            labels = [input_label] * src_l
        else:
            labels = input_label

        # adjust rep length if necessary
        if isinstance(represented_as, str):
            reps = [represented_as] * src_l
        else:
            reps = represented_as

        for src, lab, rep in zip(source, labels, reps):
            skey = src + "." + key
            svalue = {
                "source": src,
                "input_label": lab,
                "represented_as": rep,
                # mark as virtual
                "virtual": True,
            }

            # inherit is_a if exists
            if "is_a" in value.keys():
                # treat as multiple inheritance
                if isinstance(value["is_a"], list):
                    v = list(value["is_a"])
                    v.insert(0, key)
                    svalue["is_a"] = v

                else:
                    svalue["is_a"] = [key, value["is_a"]]

            else:
                # set parent as is_a
                svalue["is_a"] = key

            # inherit everything except core attributes
            for k, v in value.items():
                if k not in [
                    "is_a",
                    "source",
                    "input_label",
                    "represented_as",
                ]:
                    svalue[k] = v

            leaves[skey] = svalue

        return leaves

    @staticmethod
    def _graphql_pascal_case(name: str) -> str:
        """Convert a BioCypher schema key into a GraphQL type name."""
        parts = re.split(r"[\s_.:-]+", str(name))
        return "".join(part[:1].upper() + part[1:] for part in parts if part)

    @classmethod
    def _graphql_camel_case(cls, name: str) -> str:
        """Convert a BioCypher schema key into a GraphQL field name."""
        pascal = cls._graphql_pascal_case(name)
        return pascal[:1].lower() + pascal[1:] if pascal else ""

    @staticmethod
    def _graphql_property_type(prop_type) -> str:
        """Map BioCypher/Python-like property types to GraphQL scalar types."""
        if isinstance(prop_type, dict):
            prop_type = prop_type.get("type", "str")

        prop_type = str(prop_type).lower()

        mapping = {
            "str": "String",
            "string": "String",
            "int": "Int",
            "integer": "Int",
            "float": "Float",
            "double": "Float",
            "bool": "Boolean",
            "boolean": "Boolean",
        }

        return mapping.get(prop_type, "String")

    @staticmethod
    def _graphql_relationship_type(name: str) -> str:
        """Convert a BioCypher edge name into a Neo4j relationship type."""
        return re.sub(r"[\s_.:-]+", "_", str(name)).upper()

    @staticmethod
    def _first(value):
        """Return the first item if value is a list, otherwise return value."""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def to_graphql_schema(self) -> str:
        """
        Generate a Neo4j GraphQL Library compatible schema from the BioCypher
        ontology mapping.

        This method supports a minimal first implementation for nodes, edges,
        scalar properties, @node directives, @relationship directives, and
        @relationshipProperties interfaces.
        """
        nodes = {
            key: value
            for key, value in self.extended_schema.items()
            if value.get("represented_as") == "node"
        }

        edges = {
            key: value
            for key, value in self.extended_schema.items()
            if value.get("represented_as") == "edge"
        }

        relationship_fields = {}
        relationship_property_interfaces = []

        for edge_name, edge_value in edges.items():
            source = self._first(edge_value.get("source"))
            target = self._first(edge_value.get("target"))

            if source not in nodes or target not in nodes:
                continue

            source_type = self._graphql_pascal_case(source)
            target_type = self._graphql_pascal_case(target)
            field_name = self._graphql_camel_case(edge_name)
            rel_type = self._graphql_relationship_type(edge_name)
            props_type = f"{self._graphql_pascal_case(edge_name)}Props"

            relationship_fields.setdefault(source_type, []).append(
                f'  {field_name}: [{target_type}!]! '
                f'@relationship(type: "{rel_type}", direction: OUT, '
                f'properties: "{props_type}")'
            )

            properties = edge_value.get("properties", {})
            if properties:
                interface_lines = [
                    f"interface {props_type} @relationshipProperties {{"
                ]

                for prop_name, prop_type in properties.items():
                    gql_name = self._graphql_camel_case(prop_name)
                    gql_type = self._graphql_property_type(prop_type)
                    interface_lines.append(f"  {gql_name}: {gql_type}")

                interface_lines.append("}")
                relationship_property_interfaces.append("\n".join(interface_lines))

        schema_blocks = []

        for node_name, node_value in nodes.items():
            type_name = self._graphql_pascal_case(node_name)
            label = type_name

            block_lines = [f'type {type_name} @node(labels: ["{label}"]) {{']

            preferred_id = self._first(node_value.get("preferred_id", "id"))
            if preferred_id == "id":
                id_field = "id"
            else:
                id_field = f"{self._graphql_camel_case(preferred_id)}Id"

            block_lines.append(f"  {id_field}: ID!")

            for prop_name, prop_type in node_value.get("properties", {}).items():
                gql_name = self._graphql_camel_case(prop_name)
                gql_type = self._graphql_property_type(prop_type)
                block_lines.append(f"  {gql_name}: {gql_type}")

            block_lines.extend(relationship_fields.get(type_name, []))
            block_lines.append("}")

            schema_blocks.append("\n".join(block_lines))

        schema_blocks.extend(relationship_property_interfaces)

        return "\n\n".join(schema_blocks)