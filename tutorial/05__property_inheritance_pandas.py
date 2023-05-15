from biocypher import BioCypher
from tutorial.data_generator import (
    EntrezProtein,
    RandomPropertyProtein,
    RandomPropertyProteinIsoform,
)


def main():
    # Setup: create a list of proteins to be imported
    proteins = [
        p for sublist in zip(
            [RandomPropertyProtein() for _ in range(10)],
            [RandomPropertyProteinIsoform() for _ in range(10)],
            [EntrezProtein() for _ in range(10)],
        ) for p in sublist
    ]

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
        biocypher_config_path='tutorial/05_biocypher_config.yaml',
        schema_config_path='tutorial/05_schema_config.yaml',
    )
    # Run the import
    bc.add(node_generator())

    for name, df in bc.to_df().items():
        print(name)
        print(df)


if __name__ == '__main__':
    main()
