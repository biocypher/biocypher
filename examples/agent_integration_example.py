#!/usr/bin/env python3
"""BioCypher Agent Integration Example

This example demonstrates how LLM agents can use BioCypher to create and
reason with knowledge graphs for various use cases including:
- Reasoning process logging
- Biomedical knowledge representation
- Graph-based reasoning
- Pattern matching and analysis
"""

from biocypher import create_workflow


def example_1_basic_kg_creation():
    """Example 1: Basic knowledge graph creation for reasoning process."""
    print("=== Example 1: Basic Knowledge Graph Creation ===")

    # Define a simple schema for reasoning process
    reasoning_schema = {
        "concept": {
            "represented_as": "node",
            "preferred_id": "concept_id",
            "input_label": "concept",
            "properties": {"name": "str", "description": "str", "confidence": "float"},
        },
        "reasoning_step": {
            "represented_as": "node",
            "preferred_id": "step_id",
            "input_label": "reasoning_step",
            "properties": {"step_type": "str", "description": "str", "timestamp": "str"},
        },
        "supports": {
            "represented_as": "edge",
            "preferred_id": "support_id",
            "input_label": "supports",
            "source": "reasoning_step",
            "target": "concept",
            "properties": {"strength": "float", "evidence": "str"},
        },
        "contradicts": {
            "represented_as": "edge",
            "preferred_id": "contradiction_id",
            "input_label": "contradicts",
            "source": "reasoning_step",
            "target": "concept",
            "properties": {"strength": "float", "evidence": "str"},
        },
    }

    # Initialize workflow with reasoning schema
    workflow = create_workflow("reasoning_process", schema=reasoning_schema)

    # Add reasoning process nodes
    workflow.add_node(
        "cancer",
        "concept",
        name="Cancer",
        description="Disease characterized by uncontrolled cell growth",
        confidence=0.95,
    )
    workflow.add_node("tp53", "concept", name="TP53", description="Tumor suppressor protein", confidence=0.98)
    workflow.add_node("mutation", "concept", name="Mutation", description="Genetic alteration", confidence=0.92)

    workflow.add_node(
        "step1",
        "reasoning_step",
        step_type="observation",
        description="TP53 is frequently mutated in cancer",
        timestamp="2024-01-01T10:00:00",
    )
    workflow.add_node(
        "step2",
        "reasoning_step",
        step_type="inference",
        description="TP53 mutations likely contribute to cancer development",
        timestamp="2024-01-01T10:01:00",
    )

    # Add relationships
    workflow.add_edge("support1", "supports", "step1", "tp53", strength=0.9, evidence="Literature review")
    workflow.add_edge("support2", "supports", "step1", "cancer", strength=0.8, evidence="Clinical data")
    workflow.add_edge("support3", "supports", "step2", "mutation", strength=0.85, evidence="Mechanistic studies")

    # Query the reasoning process
    print("Concepts in reasoning process:")
    concepts = workflow.query_nodes("concept")
    for concept in concepts:
        print(f"  - {concept['properties']['name']}: {concept['properties']['description']}")

    print("\nReasoning steps:")
    steps = workflow.query_nodes("reasoning_step")
    for step in steps:
        print(f"  - {step['properties']['step_type']}: {step['properties']['description']}")

    # Get graph statistics
    stats = workflow.get_statistics()
    print(f"\nGraph Statistics: {stats['basic']['nodes']} nodes, {stats['basic']['edges']} edges")

    return workflow


def example_2_biomedical_knowledge_graph():
    """Example 2: Biomedical knowledge graph for drug discovery."""
    print("\n=== Example 2: Biomedical Knowledge Graph ===")

    # Define biomedical schema
    biomedical_schema = {
        "protein": {
            "represented_as": "node",
            "preferred_id": "uniprot",
            "input_label": "protein",
            "properties": {"name": "str", "sequence": "str", "function": "str"},
        },
        "disease": {
            "represented_as": "node",
            "preferred_id": "doid",
            "input_label": "disease",
            "properties": {"name": "str", "description": "str", "symptoms": "str"},
        },
        "drug": {
            "represented_as": "node",
            "preferred_id": "drugbank",
            "input_label": "drug",
            "properties": {"name": "str", "mechanism": "str", "status": "str"},
        },
        "interaction": {
            "represented_as": "edge",
            "preferred_id": "interaction_id",
            "input_label": "interaction",
            "source": "protein",
            "target": "protein",
            "properties": {"type": "str", "confidence": "float"},
        },
        "targets": {
            "represented_as": "edge",
            "preferred_id": "target_id",
            "input_label": "targets",
            "source": "drug",
            "target": "protein",
            "properties": {"affinity": "float", "mechanism": "str"},
        },
        "causes": {
            "represented_as": "edge",
            "preferred_id": "causes_id",
            "input_label": "causes",
            "source": "protein",
            "target": "disease",
            "properties": {"evidence": "str", "strength": "float"},
        },
        "treats": {
            "represented_as": "edge",
            "preferred_id": "treats_id",
            "input_label": "treats",
            "source": "drug",
            "target": "disease",
            "properties": {"efficacy": "float", "clinical_trial": "str"},
        },
    }

    # Initialize workflow
    workflow = create_workflow("biomedical_knowledge", schema=biomedical_schema)

    # Add proteins
    workflow.add_node(
        "P04637",
        "protein",
        name="TP53",
        sequence="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPRVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLYPEYLEDRQTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD",
        function="Tumor suppressor",
    )
    workflow.add_node(
        "P15056",
        "protein",
        name="BRAF",
        sequence="MSSDDIGAGGAEEMERTVLGKGRYGKVFLVRKVTGHDAGQLYTCKIFGTKQLGQPVFVVKELKQTVRVQMWFKRHPNILHGIGQKLLGSSEDTPPPVLVLFLTQCDMAFQIVHRDLKSDNILLDGIGTKLGDFGLATVKEGPLYTVCGTPTYVAPEIILSKGYNSAVDWWSLGILLYEMLTGKPPFKGNSQKDIENIENMVLSLVKDARLRLPNAEDWLRDPSLLDIGLLQKDFFKLLVKDPKKRPTASELLNDPWLVS",
        function="Serine/threonine kinase",
    )

    # Add diseases
    workflow.add_node(
        "DOID:162",
        "disease",
        name="Cancer",
        description="Disease characterized by uncontrolled cell growth",
        symptoms="Tumor formation, metastasis",
    )
    workflow.add_node(
        "DOID:0111253", "disease", name="Melanoma", description="Skin cancer", symptoms="Dark skin lesions"
    )

    # Add drugs
    workflow.add_node("DB08896", "drug", name="Vemurafenib", mechanism="BRAF inhibitor", status="Approved")
    workflow.add_node("DB01254", "drug", name="Cisplatin", mechanism="DNA crosslinker", status="Approved")

    # Add relationships
    workflow.add_edge("int1", "interaction", "P04637", "P15056", type="regulates", confidence=0.8)
    workflow.add_edge("cause1", "causes", "P15056", "DOID:0111253", evidence="Mutation studies", strength=0.9)
    workflow.add_edge("target1", "targets", "DB08896", "P15056", affinity=0.95, mechanism="Competitive inhibition")
    workflow.add_edge("treat1", "treats", "DB08896", "DOID:0111253", efficacy=0.7, clinical_trial="NCT00949702")

    # Use advanced querying
    print("Finding paths between BRAF and Cancer:")
    paths = workflow.find_paths("P15056", "DOID:162", max_length=3)
    for i, path in enumerate(paths):
        print(f"  Path {i+1}:")
        for edge in path:
            print(f"    {edge.source} --[{edge.type}]--> {edge.target}")

    print("\nGraph statistics:")
    stats = workflow.get_statistics()
    print(f"  - Nodes: {stats['basic']['nodes']}")
    print(f"  - Edges: {stats['basic']['edges']}")
    print(f"  - Node types: {stats['node_types']}")
    print(f"  - Edge types: {stats['edge_types']}")

    return workflow


def example_3_reasoning_process_logging():
    """Example 3: Logging a complex reasoning process."""
    print("\n=== Example 3: Reasoning Process Logging ===")

    # Create agent for reasoning process
    workflow = create_workflow("reasoning_process")

    # Simulate an LLM agent's reasoning process
    reasoning_steps = [
        {
            "step_id": "step1",
            "type": "observation",
            "description": "Patient has symptoms X, Y, Z",
            "confidence": 0.9,
            "timestamp": "2024-01-01T10:00:00",
        },
        {
            "step_id": "step2",
            "type": "hypothesis",
            "description": "Symptoms suggest condition A",
            "confidence": 0.7,
            "timestamp": "2024-01-01T10:01:00",
        },
        {
            "step_id": "step3",
            "type": "evidence_gathering",
            "description": "Lab results confirm condition A",
            "confidence": 0.85,
            "timestamp": "2024-01-01T10:02:00",
        },
        {
            "step_id": "step4",
            "type": "conclusion",
            "description": "Diagnosis: condition A",
            "confidence": 0.95,
            "timestamp": "2024-01-01T10:03:00",
        },
    ]

    # Add reasoning steps
    for step in reasoning_steps:
        workflow.add_node(
            step["step_id"],
            "reasoning_step",
            step_type=step["type"],
            description=step["description"],
            confidence=step["confidence"],
            timestamp=step["timestamp"],
        )

    # Add logical connections between steps
    workflow.add_edge("sup1", "supports", "step2", "step1", strength=0.8)
    workflow.add_edge("sup2", "supports", "step3", "step2", strength=0.9)
    workflow.add_edge("sup3", "supports", "step4", "step3", strength=0.95)

    # Add some concepts
    workflow.add_node("symptoms", "concept", name="Symptoms X, Y, Z", description="Patient symptoms")
    workflow.add_node("condition_a", "concept", name="Condition A", description="Diagnosed condition")
    workflow.add_node("lab_results", "concept", name="Lab Results", description="Laboratory findings")

    # Connect concepts to reasoning steps
    workflow.add_edge("men1", "mentions", "step1", "symptoms", relevance=0.9)
    workflow.add_edge("men2", "mentions", "step2", "condition_a", relevance=0.8)
    workflow.add_edge("men3", "mentions", "step3", "lab_results", relevance=0.9)
    workflow.add_edge("men4", "mentions", "step4", "condition_a", relevance=0.95)

    # Export reasoning process
    workflow.to_json()  # Export for demonstration
    print("Reasoning process exported to JSON format")
    print(
        f"Process contains {workflow.get_statistics()['basic']['nodes']} steps and "
        f"{workflow.get_statistics()['basic']['edges']} connections",
    )

    # Demonstrate querying the reasoning process
    print("\nReasoning process analysis:")
    summary = workflow.get_summary()
    print(f"  - Total steps: {summary['total_nodes']}")
    print(f"  - Logical connections: {summary['total_edges']}")
    print(f"  - Top step types: {summary['top_node_types']}")

    return workflow


def example_4_graph_analysis():
    """Example 4: Advanced graph analysis for LLM agents."""
    print("\n=== Example 4: Advanced Graph Analysis ===")

    # Create a more complex graph for analysis
    workflow = create_workflow("analysis_graph")

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
    ]

    # Add concepts
    for concept_id, name, description in concepts:
        workflow.add_node(concept_id, "concept", name=name, description=description, category="technology")

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
        ("CV", "CNN", "uses"),
        ("DL", "CNN", "uses"),
        ("DL", "RNN", "uses"),
    ]

    # Add relationships
    for i, (source, target, rel_type) in enumerate(relationships):
        workflow.add_edge(f"rel_{i}", "relationship", source, target, type=rel_type, strength=0.8)

    # Perform graph analysis
    print("Graph Analysis Results:")

    # Basic statistics
    stats = workflow.get_statistics()
    print("\nGraph Statistics:")
    print(f"  - Nodes: {stats['basic']['nodes']}")
    print(f"  - Edges: {stats['basic']['edges']}")
    print(f"  - Node types: {stats['node_types']}")
    print(f"  - Edge types: {stats['edge_types']}")

    # Path analysis
    print("\nShortest path from AI to BERT:")
    paths = workflow.find_paths("AI", "BERT", max_length=4)
    if paths:
        for i, path in enumerate(paths):
            print(f"  Path {i+1}: AI", end="")
            for edge in path:
                print(f" --[{edge.type}]--> {edge.target}", end="")
            print()

    # Neighbor analysis
    print("\nNeighbors of AI:")
    ai_neighbors = workflow.get_neighbors("AI")
    for neighbor_id in ai_neighbors:
        neighbor = workflow.get_node(neighbor_id)
        print(f"  - {neighbor.properties['name']}: {neighbor.properties['description']}")

    return workflow


def main():
    """Run all examples."""
    print("BioCypher Agent Integration Examples")
    print("=" * 50)

    # Run examples
    example_1_basic_kg_creation()
    example_2_biomedical_knowledge_graph()
    example_3_reasoning_process_logging()
    example_4_graph_analysis()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")
    print("\nKey benefits for LLM agents:")
    print("1. Simplified API for knowledge graph creation")
    print("2. In-memory graph representation (no external dependencies)")
    print("3. Advanced querying and analysis capabilities")
    print("4. JSON export/import for persistence")
    print("5. Schema-driven approach for domain-specific knowledge")
    print("6. Graph traversal and pattern matching")
    print("7. Centrality analysis and community detection")


if __name__ == "__main__":
    main()
