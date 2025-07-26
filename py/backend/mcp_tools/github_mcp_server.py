## import sh
## import shlex
## from mcp.server.fastmcp import FastMCP
## 
## mcp = FastMCP("GitHub CLI Tools", "Tools for interacting with GitHub through the gh CLI")
## 
## @mcp.tool()
## def gh(args: str) -> str:
##     """gh tool. See https://cli.github.com/manual/"""
##     try:
##         # Parse the args string and execute the gh command
##         parsed_args = shlex.split(args)
##         result = sh.gh(*parsed_args)
##         return str(result)
##     except sh.ErrorReturnCode as e:
##         return f"Error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
##     except Exception as e:
##         return f"Error: {str(e)}"
## 
## if __name__ == "__main__":
##     mcp.run()
