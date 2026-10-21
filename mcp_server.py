from mcp.server.fastmcp import FastMCP

from tools import get_account, get_ticket_status, create_ticket
from document_search import search_documents

mcp = FastMCP(
    "Servicing Tools",
    host="127.0.0.1",
    port=8002,
)

mcp.tool()(get_account)
mcp.tool()(get_ticket_status)
mcp.tool()(create_ticket)
mcp.tool()(search_documents)
if __name__ == "__main__":
    mcp.run(transport="streamable-http")