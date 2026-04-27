from fastmcp import FastMCP
import subprocess
import sys
import os

# Initialize FastMCP server
mcp = FastMCP("gtdev")

@mcp.tool()
def sync_ms_teams(token_max_age: int = 60, limit: int = 100) -> str:
    """
    Synchronizes MS Teams chat messages.
    
    This tool:
    1. Checks if the current skypetoken is fresh (less than token_max_age minutes old).
    2. If not, attempts to auto-extract a new token from the latest .har file in Downloads.
    3. Fetches messages for all configured rooms and merges them into the local JSON database.
    
    Args:
        token_max_age: Max age of the token in minutes before attempting re-extraction.
        limit: Number of messages to fetch per room.
    """
    try:
        # We invoke the 'teams sync' command directly to ensure we use the same logic and configuration
        cmd = [
            "teams", "sync",
            "--token-max-age", str(token_max_age),
            "--limit", str(limit)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"Sync successful:\n{result.stdout}"
        else:
            return f"Sync failed (exit code {result.returncode}):\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"Error executing sync: {str(e)}"

def main():
    """Entry point for the gtdev-mcp stdio server."""
    mcp.run()

if __name__ == "__main__":
    main()
