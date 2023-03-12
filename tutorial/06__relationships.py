from biocypher import BioCypher
from tutorial.data_generator import (
    EntrezProtein,
    InteractionGenerator,
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

    # Simulate edges
    ppi = InteractionGenerator(
        interactors=[p.get_id() for p in proteins],
        interaction_probability=0.05,
    ).generate_interactions()

    # Extract id, source, target, label, and property dictionary
    def edge_generator():
        for interaction in ppi:
            yield (
                interaction.get_id(),
                interaction.get_source_id(),
                interaction.get_target_id(),
                interaction.get_label(),
                interaction.get_properties(),
            )

    # Create BioCypher driver
    bc = BioCypher(
        biocypher_config_path='tutorial/06_biocypher_config.yaml',
        schema_config_path='tutorial/06_schema_config.yaml',
    )
    # Run the import
    bc.write_nodes(node_generator())
    bc.write_edges(edge_generator())

    # Write command line call
    bc.write_import_call()

    # Visualise ontology schema
    bc.show_ontology_structure()


if __name__ == '__main__':
    main()
