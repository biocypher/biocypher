from biocypher import BioCypher
from tutorial.data_generator import Protein


def main():
    # Setup: create a list of proteins to be imported
    proteins = [Protein() for _ in range(10)]

    # Extract id, label, and property dictionary
    def node_generator():
        for protein in proteins:
            yield (
                protein.get_id(),
                protein.get_label(),
                protein.get_properties(),
            )

    # Create BioCypher driver
    bc = BioCypher(
        biocypher_config_path='tutorial/01_biocypher_config.yaml',
        schema_config_path='tutorial/01_schema_config.yaml',
    )
    # Run the import
    nodes = bc.to_df(node_generator())
    print(nodes)

if __name__ == '__main__':
    main()
