import os
from typing import Any

import requests

class ScrapeWebsiteTool:

    def __init__(self, api_url=None,):
        self.api_url = api_url or os.getenv("WEB_SCRAPE_TOOL_API_URL") or "https://dev-aion.onefin.app/api/v1/tools/web-scrape"

    def run(self, website_url: str) -> Any:

        try:
            response = requests.post(
                self.api_url,
                json={"website_url": website_url},
                timeout=30,
            )
            response.raise_for_status()
            data = response.text
            return data
        except Exception as e:
            return f"Error calling website scrape API: {e}"

if __name__ == "__main__":
    result = ScrapeWebsiteTool().run(website_url="https://www.investopedia.com/terms/p/peer-to-peer-lending.asp")
    print(result)
