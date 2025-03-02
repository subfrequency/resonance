"""
Todoist MCP Server

A simple Model Context Protocol server that provides tools for interacting with Todoist.
"""

import os
from mcp.server.fastmcp import FastMCP
from todoist_api_python.api import TodoistAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Todoist API token
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
if not TODOIST_API_TOKEN:
    raise ValueError("TODOIST_API_TOKEN environment variable is not set")

# Initialize Todoist API client
todoist = TodoistAPI(TODOIST_API_TOKEN)

# Create MCP server
mcp = FastMCP("Todoist")

@mcp.tool()
def list_todos() -> str:
    """List all active todos from Todoist"""
    try:
        tasks = todoist.get_tasks()
        if not tasks:
            return "No active tasks found."

        task_list = []
        for task in tasks:
            due_string = "Not set"
            if hasattr(task, 'due') and task.due:
                due_string = task.due.date if hasattr(task.due, 'date') else str(task.due)

            task_list.append(f"- {task.content} (Due: {due_string})")

        return "\n".join(task_list)
    except Exception as e:
        return f"Error retrieving todos: {str(e)}"

@mcp.tool()
def add_todo(content: str, due_string: str = None) -> str:
    """Add a new todo to Todoist

    Args:
        content: The content of the todo
        due_string: Optional due string (e.g. 'today', 'tomorrow', '2023-12-31')
    """
    try:
        kwargs = {"content": content}
        if due_string:
            kwargs["due_string"] = due_string

        task = todoist.add_task(**kwargs)
        return f"Successfully added todo: {content}"
    except Exception as e:
        return f"Error adding todo: {str(e)}"

if __name__ == "__main__":
    mcp.run()
