import uvicorn
from mcp.server.fastmcp import FastMCP
from tools.web_search.web_search import WebTrustedSearchTool
from tools.context_fusion_tool import ContextFusionTool
from tools.qdrant_tool import QdrantTool
from tools.scrape_website_tool import ScrapeWebsiteTool

mcp = FastMCP("PR/FAQ Generation Tools")

try:
    @mcp.tool(name="trusted_web_search", description="Searches financial data across trusted domains")
    def trusted_web_search(query: str, trust: bool = True, read_content: bool = False, top_k: int = 10, onef_search:bool=False) -> dict:
        tool = WebTrustedSearchTool()
        return tool._run(query=query, trust=trust, read_content=read_content, top_k=top_k, onef_search=onef_search)

    @mcp.tool(name="context_fusion_tool", description="Combines information from the 1 Finance company's internal knowledge base and web search")
    def context_fusion_tool(question:str, use_websearch:bool=True) -> dict:
        tool = ContextFusionTool()
        return tool.get_context_for_question(question=question, use_websearch=use_websearch)

    @mcp.tool(name="qdrant_tool", description="Searches for information in the 1 Finance company's internal knowledge base")
    def qdrant_tool(question: str, top_k: int = 3) -> dict:
        tool = QdrantTool()
        return tool._run(question=question, top_k=top_k)
    
    @mcp.tool(name="scrape_website_tool", description="Scrapes content from a specified website URL")
    def scrape_website_tool(website_url: str) -> dict:
        tool = ScrapeWebsiteTool()
        return tool._run(website_url=website_url)
except Exception as tool_reg_err:
    raise
app = mcp.sse_app()

if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8000, reload=True)
