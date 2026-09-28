# How-to: Connect the BioCypher MCP to your IDE

!!! note
    This page is a starting point and will be expanded. For the full picture on
    LLM integration, see the [LLM Integration Guide](../../llms.md).

BioCypher provides a dedicated [Model Context Protocol](https://modelcontextprotocol.io/)
(MCP) server that AI coding assistants (GitHub Copilot, Claude, Cursor, etc.) can
use to help you build and debug BioCypher pipelines directly from your IDE.

## 1. Install an IDE with MCP support

Any IDE that supports MCP works, for example [VSCode](https://code.visualstudio.com/)
with the [GitHub Copilot extension](https://code.visualstudio.com/docs/copilot/overview).

## 2. Add the BioCypher MCP server

Add the following to your IDE's MCP configuration (for VSCode or Cursor, this is
usually an `mcp.json` file):

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

## 3. Verify the connection

In your IDE's chat, ask:

```
Show biocypher-mcp tools
```

The agent should respond with a list of available tools (e.g.
`get_cookiecutter_instructions`, `get_adapter_creation_workflow`).

!!! note
    This functionality is currently experimental and does not cover all
    BioCypher functionality yet. Use with caution.

## Next steps

- [Agent-supported hands-on tutorial](../tutorials/tutorial_basic_with_agents/tutorial_basic_with_agents.md) — build a full knowledge graph with the MCP.
- [LLM Integration Guide](../../llms.md) — background and additional LLM-specific documentation.
