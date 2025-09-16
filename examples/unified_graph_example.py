#!/usr/bin/env python3
"""Unified Graph Example - Simplified Knowledge Representation

This example demonstrates how the unified Graph class streamlines knowledge
representation for LLM agents, eliminating the complexity of multiple
in-memory formats.
"""

from biocypher import create_workflow


def example_1_basic_usage():
    """Example 1: Basic usage of the unified Graph approach."""
    print("=== Example 1: Basic Usage ===")

    # Create a knowledge graph - no complex configuration needed!
    kg = create_workflow("biomedical_knowledge")

    # Add nodes with properties using keyword arguments
    kg.add_node(
        "TP53",
        "protein",
        name="TP53",
        function="tumor_suppressor",
        sequence="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPRVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLYPEYLEDRQTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD",
    )

    kg.add_node(
        "BRAF",
        "protein",
        name="BRAF",
        function="serine_threonine_kinase",
        sequence="MSSDDIGAGGAEEMERTVLGKGRYGKVFLVRKVTGHDAGQLYTCKIFGTKQLGQPVFVVKELKQTVRVQMWFKRHPNILHGIGQKLLGSSEDTPPPVLVLFLTQCDMAFQIVHRDLKSDNILLDGIGTKLGDFGLATVKEGPLYTVCGTPTYVAPEIILSKGYNSAVDWWSLGILLYEMLTGKPPFKGNSQKDIENIENMVLSLVKDARLRLPNAEDWLRDPSLLDIGLLQKDFFKLLVKDPKKRPTASELLNDPWLVS",
    )

    kg.add_node(
        "Cancer",
        "disease",
        name="Cancer",
        description="Disease characterized by uncontrolled cell growth",
        symptoms="tumor_formation, metastasis",
    )

    kg.add_node("Melanoma", "disease", name="Melanoma", description="Skin cancer", symptoms="dark_skin_lesions")

    # Add edges with properties
    kg.add_edge("interaction_1", "regulates", "TP53", "BRAF", confidence=0.8, evidence="literature_review")

    kg.add_edge("causes_1", "causes", "BRAF", "Melanoma", evidence="mutation_studies", strength=0.9)

    kg.add_edge("is_a_1", "is_a", "Melanoma", "Cancer", confidence=1.0)

    # Query the knowledge graph
    print("Proteins in the knowledge graph:")
    proteins = kg.query_nodes("protein")
    for protein in proteins:
        print(f"  - {protein['properties']['name']}: {protein['properties']['function']}")

    print("\nDiseases in the knowledge graph:")
    diseases = kg.query_nodes("disease")
    for disease in diseases:
        print(f"  - {disease['properties']['name']}: {disease['properties']['description']}")

    print("\nAll interactions:")
    interactions = kg.query_edges("regulates")
    for interaction in interactions:
        print(
            f"  - {interaction['source']} regulates {interaction['target']} "
            f"(confidence: {interaction['properties']['confidence']})",
        )

    # Get graph statistics
    stats = kg.get_statistics()
    print(f"\nGraph Statistics: {stats['basic']['nodes']} nodes, {stats['basic']['edges']} edges")

    return kg


def example_2_reasoning_process_logging():
    """Example 2: Logging a reasoning process using the unified Graph."""
    print("\n=== Example 2: Reasoning Process Logging ===")

    # Create a reasoning graph
    reasoning = create_workflow("reasoning_process")

    # Add reasoning steps
    reasoning.add_node(
        "observation_1",
        "reasoning_step",
        step_type="observation",
        description="Patient has symptoms X, Y, Z",
        confidence=0.9,
        timestamp="2024-01-01T10:00:00",
    )

    reasoning.add_node(
        "hypothesis_1",
        "reasoning_step",
        step_type="hypothesis",
        description="Symptoms suggest condition A",
        confidence=0.7,
        timestamp="2024-01-01T10:01:00",
    )

    reasoning.add_node(
        "evidence_1",
        "reasoning_step",
        step_type="evidence_gathering",
        description="Lab results confirm condition A",
        confidence=0.85,
        timestamp="2024-01-01T10:02:00",
    )

    reasoning.add_node(
        "conclusion_1",
        "reasoning_step",
        step_type="conclusion",
        description="Diagnosis: condition A",
        confidence=0.95,
        timestamp="2024-01-01T10:03:00",
    )

    # Add concepts
    reasoning.add_node("symptoms_xyz", "concept", name="Symptoms X, Y, Z", description="Patient symptoms")

    reasoning.add_node("condition_a", "concept", name="Condition A", description="Diagnosed condition")

    reasoning.add_node("lab_results", "concept", name="Lab Results", description="Laboratory findings")

    # Add logical connections between reasoning steps
    reasoning.add_edge("supports_1", "supports", "hypothesis_1", "observation_1", strength=0.8)

    reasoning.add_edge("supports_2", "supports", "evidence_1", "hypothesis_1", strength=0.9)

    reasoning.add_edge("supports_3", "supports", "conclusion_1", "evidence_1", strength=0.95)

    # Connect concepts to reasoning steps
    reasoning.add_edge("mentions_1", "mentions", "observation_1", "symptoms_xyz", relevance=0.9)

    reasoning.add_edge("mentions_2", "mentions", "hypothesis_1", "condition_a", relevance=0.8)

    reasoning.add_edge("mentions_3", "mentions", "evidence_1", "lab_results", relevance=0.9)

    reasoning.add_edge("mentions_4", "mentions", "conclusion_1", "condition_a", relevance=0.95)

    # Find the reasoning chain
    print("Reasoning chain from observation to conclusion:")
    paths = reasoning.find_paths("observation_1", "conclusion_1", max_length=4)

    for i, path in enumerate(paths):
        print(f"  Path {i+1}:")
        for edge in path:
            source_step = reasoning.get_node(edge.source)
            target_step = reasoning.get_node(edge.target)
            print(
                f"    {source_step.properties['step_type']} -> {target_step.properties['step_type']} "
                f"({edge.properties.get('strength', 'N/A')})",
            )

    # Get reasoning summary
    summary = reasoning.get_summary()
    print("\nReasoning Process Summary:")
    print(f"  - Total steps: {summary['total_nodes']}")
    print(f"  - Logical connections: {summary['total_edges']}")
    print(f"  - Top step types: {summary['top_node_types']}")

    return reasoning


def example_3_hypergraph_representation():
    """Example 3: Using hyperedges for complex relationships."""
    print("\n=== Example 3: Hypergraph Representation ===")

    # Create a knowledge graph for protein complexes
    complexes = create_workflow("protein_complexes")

    # Add proteins
    proteins = ["TP53", "MDM2", "CDKN1A", "BAX", "BCL2", "CASP3", "CASP9"]
    for protein in proteins:
        complexes.add_node(protein, "protein", name=protein)

    # Add diseases
    diseases = ["Cancer", "Apoptosis", "Cell_Cycle_Arrest"]
    for disease in diseases:
        complexes.add_node(disease, "disease", name=disease)

    # Add protein complexes as hyperedges
    complexes.add_hyperedge(
        "complex_1",
        "protein_complex",
        {"TP53", "MDM2"},
        name="TP53-MDM2_complex",
        function="protein_degradation",
    )

    complexes.add_hyperedge(
        "complex_2",
        "protein_complex",
        {"TP53", "CDKN1A"},
        name="TP53-CDKN1A_complex",
        function="cell_cycle_control",
    )

    complexes.add_hyperedge(
        "complex_3",
        "protein_complex",
        {"BAX", "BCL2", "CASP3", "CASP9"},
        name="apoptosis_complex",
        function="programmed_cell_death",
    )

    # Add regulatory relationships
    complexes.add_edge("regulates_1", "regulates", "TP53", "BAX", mechanism="transcriptional_activation")

    complexes.add_edge("regulates_2", "regulates", "TP53", "BCL2", mechanism="transcriptional_repression")

    complexes.add_edge("regulates_3", "regulates", "TP53", "CASP3", mechanism="transcriptional_activation")

    # Query hyperedges
    print("Protein complexes in the knowledge graph:")
    protein_complexes = complexes.query_hyperedges("protein_complex")
    for complex_edge in protein_complexes:
        print(f"  - {complex_edge['properties']['name']}: {complex_edge['properties']['function']}")
        print(f"    Proteins: {', '.join(complex_edge['nodes'])}")

    # Find connected components around TP53
    print("\nTP53 interaction network:")
    tp53_network = complexes.find_connected_components("TP53", max_depth=2)
    print(f"  - Connected nodes: {len(tp53_network['nodes'])}")
    print(f"  - Connected edges: {len(tp53_network['edges'])}")
    print(f"  - Connected hyperedges: {len(tp53_network['hyperedges'])}")

    return complexes


def example_4_graph_analysis():
    """Example 4: Advanced graph analysis capabilities."""
    print("\n=== Example 4: Graph Analysis ===")

    # Create a complex knowledge graph
    analysis = create_workflow("analysis_graph")

    # Add a network of concepts and relationships
    concepts = [
        ("AI", "Artificial Intelligence", "Technology field"),
        ("ML", "Machine Learning", "AI subset"),
        ("DL", "Deep Learning", "ML subset"),
        ("NLP", "Natural Language Processing", "AI application"),
        ("CV", "Computer Vision", "AI application"),
        ("RL", "Reinforcement Learning", "ML technique"),
        ("NN", "Neural Networks", "DL component"),
        ("CNN", "Convolutional Neural Networks", "NN type"),
        ("RNN", "Recurrent Neural Networks", "NN type"),
        ("BERT", "Bidirectional Encoder Representations", "NLP model"),
        ("GPT", "Generative Pre-trained Transformer", "NLP model"),
        ("ResNet", "Residual Networks", "CNN architecture"),
    ]

    # Add concepts
    for concept_id, name, description in concepts:
        analysis.add_node(concept_id, "concept", name=name, description=description)

    # Add hierarchical relationships
    relationships = [
        ("AI", "ML", "contains"),
        ("AI", "NLP", "contains"),
        ("AI", "CV", "contains"),
        ("ML", "DL", "contains"),
        ("ML", "RL", "contains"),
        ("DL", "NN", "contains"),
        ("NN", "CNN", "type_of"),
        ("NN", "RNN", "type_of"),
        ("NLP", "BERT", "uses"),
        ("NLP", "GPT", "uses"),
        ("CV", "CNN", "uses"),
        ("CV", "ResNet", "uses"),
        ("DL", "CNN", "uses"),
        ("DL", "RNN", "uses"),
        ("CNN", "ResNet", "implements"),
    ]

    # Add relationships
    for i, (source, target, rel_type) in enumerate(relationships):
        analysis.add_edge(f"rel_{i}", rel_type, source, target, strength=0.8)

    # Perform graph analysis
    print("Graph Analysis Results:")

    # Basic statistics
    stats = analysis.get_statistics()
    print(f"  - Total nodes: {stats['basic']['nodes']}")
    print(f"  - Total edges: {stats['basic']['edges']}")
    print(f"  - Node types: {stats['node_types']}")
    print(f"  - Edge types: {stats['edge_types']}")

    # Connectivity analysis
    connectivity = stats["connectivity"]
    print(f"  - Connected nodes: {connectivity['connected_nodes']}")
    print(f"  - Isolated nodes: {connectivity['isolated_nodes']}")

    # Path analysis
    print("\nShortest path from AI to BERT:")
    paths = analysis.find_paths("AI", "BERT", max_length=4)
    for i, path in enumerate(paths):
        print(f"  Path {i+1}: AI", end="")
        for edge in path:
            print(f" --[{edge.type}]--> {edge.target}", end="")
        print()

    # Neighbor analysis
    print("\nNeighbors of AI:")
    ai_neighbors = analysis.get_neighbors("AI")
    for neighbor_id in ai_neighbors:
        neighbor = analysis.get_node(neighbor_id)
        print(f"  - {neighbor.properties['name']}: {neighbor.properties['description']}")

    return analysis


def example_5_serialization_and_persistence():
    """Example 5: Serialization and persistence capabilities."""
    print("\n=== Example 5: Serialization and Persistence ===")

    # Create a knowledge graph
    kg = create_workflow("serialization_test")

    # Add some data
    kg.add_node("node1", "concept", name="Concept 1", description="First concept")
    kg.add_node("node2", "concept", name="Concept 2", description="Second concept")
    kg.add_edge("edge1", "relates_to", "node1", "node2", strength=0.8)

    # Export to JSON
    json_data = kg.to_json()
    print("Graph exported to JSON format")
    print(f"JSON size: {len(json_data)} characters")

    # Create a new graph from JSON
    new_kg = create_workflow("restored_graph")
    new_kg.from_json(json_data)

    print("Graph restored from JSON")
    print(f"Restored graph: {new_kg}")

    # Verify data integrity
    original_nodes = kg.query_nodes()
    restored_nodes = new_kg.query_nodes()

    print(f"Original nodes: {len(original_nodes)}")
    print(f"Restored nodes: {len(restored_nodes)}")

    # Save to file
    kg.save("examples/example_graph.json")
    print("Graph saved to 'examples/example_graph.json'")

    # Load from file
    loaded_kg = create_workflow("loaded_graph")
    loaded_kg.load("examples/example_graph.json")
    print("Graph loaded from file")
    print(f"Loaded graph: {loaded_kg}")

    return kg


def example_6_comparison_with_original_approach():
    """Example 6: Comparison with the original complex approach."""
    print("\n=== Example 6: Comparison with Original Approach ===")

    print("Original BioCypher approach requires:")
    print("  1. Complex YAML configuration files")
    print("  2. Multiple in-memory formats (NetworkX, Pandas, CSV)")
    print("  3. Schema validation and translation layers")
    print("  4. Complex initialization with many parameters")
    print("  5. Separate query interfaces for different formats")

    print("\nUnified Graph approach provides:")
    print("  1. Simple initialization: create_workflow()")
    print("  2. Single unified representation")
    print("  3. Direct property assignment with **kwargs")
    print("  4. Built-in serialization (JSON)")
    print("  5. Consistent query interface")
    print("  6. Support for hypergraphs and complex relationships")
    print("  7. Optional schema and ontology support")
    print("  8. No external dependencies for basic operations")

    # Demonstrate the simplicity
    print("\nSimple usage example:")
    print(
        """
# Create graph
kg = create_workflow("my_knowledge")

# Add nodes with properties
kg.add_node("protein_1", "protein", name="TP53", function="tumor_suppressor")

# Add edges with properties
kg.add_edge("interaction_1", "interaction", "protein_1", "protein_2", confidence=0.8)

# Query
proteins = kg.query_nodes("protein")
paths = kg.find_paths("protein_1", "protein_2")

# Export
kg.save("examples/knowledge.json")
    """,
    )


def main():
    """Run all examples."""
    print("Unified Graph Examples - Simplified Knowledge Representation")
    print("=" * 60)

    # Run examples
    example_1_basic_usage()
    example_2_reasoning_process_logging()
    example_3_hypergraph_representation()
    example_4_graph_analysis()
    example_5_serialization_and_persistence()
    example_6_comparison_with_original_approach()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nKey benefits of the unified Graph approach:")
    print("1. Simplified API - no complex configuration needed")
    print("2. Single representation - no format confusion")
    print("3. Direct property assignment - no translation layers")
    print("4. Built-in serialization - easy persistence")
    print("5. Support for hypergraphs - complex relationships")
    print("6. Consistent querying - same interface for all operations")
    print("7. No external dependencies - pure Python implementation")
    print("8. Extensible design - easy to add new features")


if __name__ == "__main__":
    main()
