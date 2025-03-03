## Simple

![Simple](https://github.com/user-attachments/assets/76ef0d2d-04f5-49d1-ba55-539f9dedc7df)

Add to Claude Desktop's config file:

``` json
{
    "mcpServers": {
        "simple": {
            "command": "uv",
            "args": [
                "--directory",
                "/Users/resonance/projects/subfrequencies/resonance/simple",
                "run",
                "main.py"
            ]
        }
    }
}
```

## To do

- Calendar (Fantastical)
- [Anki](https://github.com/scorzeth/anki-mcp-server)

## See also

- [Model Context Protocol quickstart for server developers](https://modelcontextprotocol.io/quickstart/server)
- [Model Context Protocol example servers](https://modelcontextprotocol.io/examples)
- [Model Context Protocol server implementations](https://github.com/modelcontextprotocol/servers)
- [MCP Server Finder tool](https://www.mcpserverfinder.com/)
- [`lastmile-ai/mcp-agent`](https://github.com/lastmile-ai/mcp-agent)
- [Building agents with Model Context Protocol: Full workshop with Mahesh Murag of Anthropic](https://www.youtube.com/watch?v=kQmXtrmQ5Zg&t=3415s)
- [Claude 3.7 Sonnet starter guide and Claude Code overview](https://www.youtube.com/watch?v=jCVO57fZIfM)
