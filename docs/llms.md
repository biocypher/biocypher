# LLM Integration Guide

<div style="text-align: center; margin: 2em 0;">
    <blockquote style="font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 300; font-size: 1.2em; max-width: 800px; margin: 0 auto;">
        AI coding assistants can accelerate BioCypher development.<br>
        These guides help LLMs understand BioCypher's patterns and conventions.
    </blockquote>
</div>

The easiest way to integrate specific BioCypher instructions into your AI-assisted workflow is to connect your software to our dedicated MCP server at [https://mcp.biocypher.org](https://mcp.biocypher.org). You can use our [MCP-ready template](https://github.com/biocypher/mcp-template) to get started. Set up your own repository using the template, load it in your favourite co-programmer, and connect to the MCP to get started on your pipeline.

!!! note

    This functionality is currently experimental and does not cover all BioCypher
    functionality yet. Use with caution.

This section provides specialized documentation for AI coding assistants (Copilot, Cursor, Claude, etc.) to help them understand BioCypher's architecture and create high-quality code that follows our conventions.

## Why LLM-Specific Documentation?

BioCypher follows specific patterns and conventions that may not be immediately obvious to AI assistants. These guides provide:

- **Clear architectural patterns** for common tasks
- **Concrete examples** with expected input/output formats
- **Validation rules** to ensure code quality
- **Best practices** specific to BioCypher's domain

## Available Guides

For AI assistants, the following `.txt` files are available in the root of this documentation:

- **[llms.txt](llms.txt)** - Comprehensive functionality index and quick reference
- **[llms-adapters.txt](llms-adapters.txt)** - Adapter creation guide with patterns and examples
- **[llms-example-adapter.txt](llms-example-adapter.txt)** - Complete working GEO adapter example

## How to Use These Guides

When working with an AI assistant on BioCypher code:

1. **Reference the specific guide** for your task (e.g., adapter creation)
2. **Provide the guide content** in your prompt for context
3. **Specify the schema configuration** you're working with
4. **Request validation** against the patterns described

## Example Prompt

```
I'm creating a BioCypher adapter for NCBI GEO data. Please follow the adapter creation guide at llms-adapters.txt.

My schema configuration defines these node types:
- geo_sample (input_label: "geo_sample")
- geo_series (input_label: "geo_series")

And these edge types:
- HAS_SAMPLE (input_label: "HAS_SAMPLE")

Please create an adapter that follows the 3-tuple (node_id, node_label, attributes_dict) and 5-tuple (edge_id, source_id, target_id, edge_label, attributes_dict) patterns described in the guide.
```

## Contributing

If you find patterns or conventions that would benefit from LLM documentation, please contribute by:

1. Creating a new guide file following the naming convention `llms-*.txt`
2. Updating the main `llms.txt` index
3. Adding the guide to this overview page

## Related Resources

- [BioCypher + LLMs](biocypher-project/biochatter-integration.md) - Integration with BioChatter
- [Adapter Tutorial](learn/tutorials/tutorial003_adapters.md) - Human-focused adapter tutorial
- [Schema Configuration](reference/schema-config.md) - Schema configuration reference
