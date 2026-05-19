import warnings


from biocypher._mapping import OntologyMapping

# TODO migrate as appropriate from test translate


def test_inheritance_loop(ontology_mapping):
    assert "gene to variant association" in ontology_mapping.schema.keys()

    assert "gene to variant association" not in ontology_mapping.extended_schema.keys()


def test_virtual_leaves_node(ontology_mapping):
    assert "wikipathways.pathway" in ontology_mapping.extended_schema


def test_getting_properties_via_config(ontology_mapping):
    assert "name" in ontology_mapping.extended_schema["protein"].get("properties").keys()


def test_preferred_id_optional(ontology_mapping):
    pti = ontology_mapping.extended_schema.get("post translational interaction")

    assert pti.get("preferred_id") == "id"


def test_namespace_accepted_as_preferred_id():
    """Schema entries using 'namespace' are normalised to 'preferred_id' internally."""
    m = OntologyMapping()
    m.schema = {
        "protein": {
            "represented_as": "node",
            "namespace": "uniprot",
            "input_label": "protein",
        }
    }
    extended = m._extend_schema(d=m.schema)
    assert extended["protein"]["preferred_id"] == "uniprot"
    assert "namespace" not in extended["protein"]


def test_preferred_id_in_schema_emits_deprecation_warning():
    """Schema entries still using 'preferred_id' trigger a DeprecationWarning."""
    m = OntologyMapping()
    m.schema = {
        "protein": {
            "represented_as": "node",
            "preferred_id": "uniprot",
            "input_label": "protein",
        }
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        extended = m._extend_schema(d=m.schema)

    dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(dep_warnings) == 1
    assert "preferred_id" in str(dep_warnings[0].message)
    assert "namespace" in str(dep_warnings[0].message)
    assert extended["protein"]["preferred_id"] == "uniprot"
