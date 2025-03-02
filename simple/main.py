#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "mcp",
# ]
# ///

from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp = FastMCP("SimpleDemo")

# Define a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: The first number
        b: The second number

    Returns:
        The sum of a and b
    """
    return a + b

# Define a simple text resource
@mcp.resource("greeting://welcome")
def welcome_message() -> str:
    """Return a welcome message."""
    return "Welcome to your first MCP server! This is a simple resource."

# Define a resource with a parameter
@mcp.resource("greeting://{name}")
def personalized_greeting(name: str) -> str:
    """Return a personalized greeting.

    Args:
        name: The name to include in the greeting
    """
    return f"Hello, {name}! This is a dynamic resource."

# Run the server when this file is executed directly
if __name__ == "__main__":
    mcp.run()
