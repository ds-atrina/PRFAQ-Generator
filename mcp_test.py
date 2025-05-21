import sys
from mcp.server.fastmcp import FastMCP
# print("[INFO] Imported FastMCP")
from tools.web_search.web_search import WebTrustedSearchTool
# print("[INFO] Imported WebTrustedSearchTool")
from tools.context_fusion_tool import ContextFusionTool
# print("[INFO] Imported ContextFusionTool")
from tools.qdrant_tool import QdrantTool
    # print("[INFO] Imported QdrantTool")

mcp = FastMCP("PR/FAQ Generation Tools")

try:
    @mcp.tool(name="trusted_web_search", description="Searches financial data across trusted domains")
    def trusted_web_search(query: str, trust: bool = True, read_content: bool = False, top_k: int = 10) -> dict:
        tool = WebTrustedSearchTool()
        return tool._run(query=query, trust=trust, read_content=read_content, top_k=top_k)

    @mcp.tool(name="context_fusion_tool", description="Combines information from internal knowledge base and web search")
    def context_fusion_tool(internal: list, external: list, use_websearch: bool = False, topic: str = "") -> dict:
        tool = ContextFusionTool()
        return tool._run(internal=internal, external=external, use_websearch=use_websearch, topic=topic)

    @mcp.tool(name="qdrant_tool", description="Searches for information in the internal knowledge base")
    def qdrant_tool(question: str, top_k: int = 3) -> dict:
        tool = QdrantTool()
        return tool._run(question=question, top_k=top_k)
except Exception as tool_reg_err:
    # print(f"[ERROR] Tool registration failed: {tool_reg_err}", file=sys.stderr)
    raise

# if __name__ == "__main__":
#     # print("[INFO] MCP server starting: PR/FAQ Generation Tools")
#     try:
#         mcp.run()
#     except Exception as run_err:
#         # print(f"[ERROR] MCP server crashed during run(): {run_err}", file=sys.stderr)
#         raise
