class GraphQLSchemaGenerator:
    """
    Generates a Neo4j GraphQL Library compatible schema from a BioCypher schema dictionary.
    """
    def __init__(self, schema: dict):
        self.schema = schema

    def _format_property_type(self, prop_type: str) -> str:
        """Map Python types to GraphQL types."""
        type_mapping = {
            "str": "String",
            "string": "String",
            "int": "Int",
            "integer": "Int",
            "float": "Float",
            "bool": "Boolean",
            "boolean": "Boolean",
        }
        return type_mapping.get(str(prop_type).lower(), "String")

    def _pascal_case(self, name: str) -> str:
        """Convert snake_case or space-separated name to PascalCase."""
        name = name.replace("-", " ").replace("_", " ")
        return "".join(word.capitalize() for word in name.split())

    def _screaming_snake_case(self, name: str) -> str:
        """Convert space-separated name to SCREAMING_SNAKE_CASE."""
        return name.replace(" ", "_").replace("-", "_").upper()

    def generate(self) -> str:
        """Generate the GraphQL schema as a string."""
        graphql_lines = []
        nodes = {}
        edges = {}

        # Separate nodes and edges
        for key, config in self.schema.items():
            if not isinstance(config, dict):
                continue
            rep = config.get("represented_as", "node")
            if rep == "node":
                nodes[key] = config
            elif rep == "edge":
                edges[key] = config

        # Generate Node Types
        for node_name, config in nodes.items():
            type_name = self._pascal_case(node_name)
            labels = config.get("labels_in_db", [type_name])
            label_str = '", "'.join(labels)
            
            graphql_lines.append(f'type {type_name} @node(labels: ["{label_str}"]) {{')
            
            # IDs
            pref_id = config.get("preferred_id", "id")
            graphql_lines.append(f'  {pref_id}: ID!')
            
            # Properties
            props = config.get("properties", {})
            for prop_name, prop_type in props.items():
                if prop_name != pref_id:
                    gql_type = self._format_property_type(prop_type)
                    graphql_lines.append(f'  {prop_name}: {gql_type}')
            
            # Relationships targeting this node (or originating from it)
            for edge_name, edge_config in edges.items():
                source = edge_config.get("source")
                target = edge_config.get("target")
                
                # If relationship involves this node
                if source == node_name:
                    rel_type = self._screaming_snake_case(edge_name)
                    target_pascal = self._pascal_case(target)
                    props_interface = self._pascal_case(edge_name) + "Props"
                    
                    if edge_config.get("properties"):
                        graphql_lines.append(
                            f'  {self._pascal_case(edge_name).lower()}: [{target_pascal}!]! @relationship(type: "{rel_type}", direction: OUT, properties: "{props_interface}")'
                        )
                    else:
                        graphql_lines.append(
                            f'  {self._pascal_case(edge_name).lower()}: [{target_pascal}!]! @relationship(type: "{rel_type}", direction: OUT)'
                        )

            graphql_lines.append("}\n")

        # Generate Relationship Interfaces
        for edge_name, config in edges.items():
            props = config.get("properties", {})
            if props:
                interface_name = self._pascal_case(edge_name) + "Props"
                graphql_lines.append(f'interface {interface_name} @relationshipProperties {{')
                for prop_name, prop_type in props.items():
                    gql_type = self._format_property_type(prop_type)
                    graphql_lines.append(f'  {prop_name}: {gql_type}')
                graphql_lines.append("}\n")

        return "\n".join(graphql_lines)
