# LLM Integration Guide

<div style="text-align: center; margin: 2em 0;">
    <blockquote style="font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 300; font-size: 1.2em; max-width: 800px; margin: 0 auto;">
        AI coding assistants can accelerate BioCypher development.<br>
        These guides help LLMs understand BioCypher's patterns and conventions.
    </blockquote>
</div>

The easiest way to integrate specific BioCypher instructions into your AI-assisted workflow is to connect your software to our dedicated MCP server at https://mcp.biocypher.org/mcp (not human-readable). The copilot can help you use our [cookiecutter template](https://github.com/biocypher/biocypher-cookiecutter-template) to get started (this one is also human-usable).

!!! note

    This functionality is currently experimental and does not cover all BioCypher
    functionality yet. Use with caution.

The MCP server gives AI coding assistants (Copilot, Cursor, Claude, etc.) step-by-step guidance for building a BioCypher pipeline and serves the [LLM guides](#llm-guides) below through its `get_biocypher_docs` tool. For Cursor or VSCode, add it like this (see also [Connect the MCP to your IDE](learn/guides/mcp.md)):

```json
{
  "mcpServers": {
    "biocypher-mcp": {
      "url": "https://mcp.biocypher.org/mcp",
      "transport": "http"
    }
  }
}
```

You can then ask for guidance in building your knowledge representation. For instance:

```
Using the CSVs in the `data` directory, how do I build a BioCypher knowledge graph?
```

## LLM guides

BioCypher follows patterns and conventions that AI assistants do not reliably know, and models often suggest functions that do not exist. The LLM guides state the conventions, the silent failure modes and the known bugs of the current release in plain Markdown, one topic per file, checked against the BioCypher code. The MCP server serves them to models, and you can also give them to your assistant directly.

| Guide | Contents |
| --- | --- |
| [llms.txt](agents/llms.txt) | Index, core facts and a minimal pipeline. Start here. |
| [llms-adapters.txt](agents/llms-adapters.txt) | Node and edge tuple formats, how BioCypher filters and deduplicates them, downloading and caching, testing an adapter |
| [llms-schema-config.txt](agents/llms-schema-config.txt) | `schema_config.yaml` fields, class naming, list-valued fields, relationships as nodes, strict mode |
| [llms-biocypher-config.txt](agents/llms-biocypher-config.txt) | `biocypher_config.yaml` loading and merging, output backends, offline and online mode, headless mode |
| [llms-pitfalls.txt](agents/llms-pitfalls.txt) | Known bugs with workarounds, silent data loss, configuration surprises, APIs that do not exist |
| [llms-example-adapter.txt](agents/llms-example-adapter.txt) | A complete runnable project with its verified output |

The guides are served as plain text at `https://biocypher.org/BioCypher/agents/<file>`; `llms.txt` follows the [llms.txt](https://llmstxt.org/) format. Their sources are in [`docs/agents/`](https://github.com/biocypher/biocypher/tree/main/docs/agents) in the BioCypher repository.

## How the guides get into the MCP

The MCP server does not fetch the guides at runtime. It ships a copy of them, taken from this repository at a pinned commit, so it works without network access and gives the same content on every run. Because of the pin, the MCP can lag behind the guides published here.

- The MCP serves `llms.txt`, `llms-adapters.txt`, `llms-schema-config.txt`, `llms-biocypher-config.txt` and `llms-pitfalls.txt` as the topics `index`, `adapters`, `schema_config`, `biocypher_config` and `pitfalls`. It rewrites links between these guides into `get_biocypher_docs` calls.
- It does not serve `llms-example-adapter.txt`. With the MCP, the project generated from the cookiecutter template is the working example.
- After changing a guide in `docs/agents/`, update the pin in [biocypher-mcp](https://github.com/biocypher/biocypher-mcp): set `BIOCYPHER_DOCS_REF` in `src/biocypher_mcp/biocypher_docs.py` to the new commit, run `scripts/sync_biocypher_docs.py`, and commit the updated snapshot. The change reaches users of https://mcp.biocypher.org/mcp once the server is redeployed.
- Keep the file names stable, and when you add or rename a guide, update the topic list in `biocypher_docs.py` as well.

## Using the guides without the MCP

1. Give your assistant the URL of `llms.txt`, or of the guide that fits your task.
2. Tell it which schema configuration you use, or let it read your `config/schema_config.yaml`.
3. Ask it to check its code against the guides, in particular the pitfalls.

Example prompt:

```
I'm writing a BioCypher adapter for the CSV files in data/. Follow
https://biocypher.org/BioCypher/agents/llms-adapters.txt and check the result
against https://biocypher.org/BioCypher/agents/llms-pitfalls.txt.
The schema is in config/schema_config.yaml. Yield 3-tuples
(node_id, input_label, properties) for nodes and 5-tuples
(edge_id, source_id, target_id, input_label, properties) for edges, and write
tests for the tuples the adapter yields.
```

## Related Resources

- [BioCypher + LLMs](biocypher-project/biochatter-integration.md) - Integration with BioChatter
- [Adapters](learn/explanation/adapters.md) - Human-focused explanation of adapters
- [Schema Configuration](reference/schema-config.md) - Schema configuration reference
