from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any
import requests
import datetime
import re
import os
import time
from langchain_openai import ChatOpenAI
from urllib.parse import urlencode, urlparse
from tools.web_search.whitelisted_sites import whitelisted_domain_list
from dotenv import load_dotenv

load_dotenv() 

llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

class WebSearchQuerySchema(BaseModel):
    query: str = Field(..., description="Search query to find relevant information.")
    trust: bool = Field(True, description="Whether to search on trusted sites more.")
    read_content: bool = Field(False, description="Whether to read top sites' article content or not.")
    top_k: int = Field(20, description="Number of top results to fetch from the search engine.")

class WebTrustedSearchTool(BaseTool):
    name: str = "Web Trusted Search Tool"
    description: str = (
        "Performs smart search on relevant whitelisted financial sites using Web Search"
    )
    args_schema: Type[BaseModel] = WebSearchQuerySchema

    def _choose_relevant_domains(self, query: str) -> List[str]:
        prompt = (
            f"You are helping a researcher identify the most relevant websites to search.\n"
            f"Query: {query}\n"
            f"Here is a list of approved domains:\n{chr(10).join(whitelisted_domain_list)} and their information:\n\n"
            """Below is a list of trusted, whitelisted sources and the types of data they provide:
            ---
            ### SEBI (sebi.gov.in)
            - Mutual Funds (MF): Schemes, Funds Mobilized, Net Assets, AMFI Data
            - Portfolio Management Services (PMS): AUM, Clients, Performance
            - Foreign Portfolio Investments (FPI): Sector-wise, Trade-wise, Custody
            - Alternative Investment Funds (AIF): Fundraising, Investments
            - Corporate Bonds: Trades, Repo, Private Placements
            - Green Bonds & Municipal Bonds: Issuance, Tenure, Coupon
            - IPO Data: Schedule, Red Herring Prospectus, Processing Status
            - REIT/InvIT Fundraising
            - Capital Market Overview & Policy Developments
            - SEBI Circulars & Notifications
            - Licensing & Offer Approvals

            ### NSE (nseindia.com)
            - Macro Factors, Forex Reserves, FII/DII Activity
            - Active Clients, Broker Data
            - IPO & Exchange Performance
            - Mutual Funds: AMC/Scheme-wise, Passive MFs, ETFs
            - Market Cap, Trading Symbols
            - Volume Data

            ### BSE (bseindia.com)
            - Trading Volumes
            - IPO Performance Tracker
            - Market Capitalization & Symbols

            ### RBI (rbi.org.in)
            - CPI, Inflation, GDP, Interest Rates, CRR
            - Bank Credit Data
            - Forex Markets, Public Finance, Debt Markets
            - Economic Ratios
            - RBI Press Releases & Financial Bulletins

            ### Income Tax Dept. (incometaxindia.gov.in)
            - Income Tax Rules & Laws
            - Tax Statistics
            - Circulars and Notifications

            ### GST Portal (gst.gov.in)
            - GST Collections and Data
            - Press Releases

            ### PFRDA (pfrda.org.in)
            - Pension Fund Circulars

            ### AMFI (amfiindia.com)
            - Mutual Fund AUM (Quarterly, Category-wise, Scheme-wise)
            - SIP Contributions (Monthly, Yearly)
            - Commission Data: MFD-wise AUM, Inflows
            - Stock Exchange Mkt Cap, Trading Symbols
            - Passive Funds, Index Funds, ETFs

            ### CMIE (cmie.com)
            - Indian Economic Indicators

            ### IRDAI (irdai.gov.in)
            - Indian Insurance Data

            ### NBFC Registry
            - List of NBFCs permitted/not permitted to accept public deposits

            ### CEIC (ceicdata.com)
            - Global Macro-Economic Indicators by Country

            ### WFE (world-exchanges.org)
            - Global Exchange Data: IPOs, Volume, Listings

            ### FII/DII Daily Tracker
            - Daily FII/DII Trading Activity

            ### IBEF (ibef.org)
            - Sectoral Economic Reports for India

            ### Economic Adviser (eaindustry.nic.in)
            - WPI, Commodities, 8 Core Industries Data

            ### FADA (fada.in)
            - Auto Sales, Market Share

            ### SIAM (siam.in)
            - Auto Industry: Production, Sales, Exports

            ### Ministry of Statistics & Programme Implementation (mospi.gov.in)
            - Statistical Reports, Consumption Data
            - Emerging Industries, Global Comparisons
            - Press Releases

            ### Department of Commerce (commerce.gov.in)
            - Export-Import Trade Data

            ### Department for Promotion of Industry and Internal Trade (dpiit.gov.in)
            - Emerging Industry Data

            ### APMI (apmiindia.org)
            - PMS Performance & Comparisons

            ### US CPI (bls.gov)
            - Consumer Price Index (USA)
            """
            f"Pick the top 3 most likely to contain helpful info for this context. "
            f"Return ONLY the domain names."
        )
        response = llm.invoke(prompt)
        selected = []
        for domain in whitelisted_domain_list:
            if domain.lower() in response.content.lower():
                selected.append(domain)

        return selected

    def calculate_relevance_score(self, result: Dict[str, Any], query: str) -> int:
        try:
            lowercase_content = result['content'].lower()
            lowercase_query = query.lower()
            query_words = [
                re.escape(word)
                for word in lowercase_query.split()
                if len(word) > 2
            ]

            score = 0
            if lowercase_query in lowercase_content:
                score += 30
            for word in query_words:
                word_count = lowercase_content.count(word)
                score += word_count * 3

            lowercase_title = result['title'].lower()
            if lowercase_query in lowercase_title:
                score += 20
            for word in query_words:
                if word in lowercase_title:
                    score += 10

            if "publishedDate" in result:
                publish_date = datetime.datetime.strptime(result['publishedDate'], '%Y-%m-%d')
                days_since = (datetime.datetime.now() - publish_date).days
                if days_since < 30:
                    score += 15
                elif days_since < 90:
                    score += 10
                elif days_since < 365:
                    score += 5

            if len(result['content']) < 200:
                score -= 10
            elif len(result['content']) > 1000:
                score += 5

            highlight_count = result['content'].count("<mark>")
            score += highlight_count * 2

            if "url" in result:
                parsed_url = urlparse(result["url"])
                domain = parsed_url.netloc.lower()
                for whitelisted_domain in whitelisted_domain_list:
                    if whitelisted_domain in domain:
                        score += 30
                        break

            return score
        except Exception:
            return 0

    def _parse_html_response(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.find_all("div", class_="result"):
            title = item.find("h4")
            url = item.find("a", href=True)
            content = item.find("p")
            if title and url and content:
                results.append({
                    "title": title.text.strip(),
                    "url": url['href'],
                    "content": content.text.strip(),
                })
        return results

    def _run(self, query: str, trust:bool, read_content:bool, top_k:int) -> Dict[str, Any]:
        """Search Brave Search with a freeform query and fetch content from top 5 sites."""
        brave_instance = "https://api.search.brave.com"
        selected_domains=[]
        if trust:
            selected_domains = self._choose_relevant_domains(query)
            
        selected_domains.append("")

        results = []
        for domain in selected_domains:
            search_query = f"site:{domain} {query}" if domain else query
            payload = {
                "q": search_query,
                "format": "json",
                "country": "IN",
                "summary": True
            }

            retries = 3  # Maximum number of retries
            backoff = 1  # Initial backoff time in seconds

            while retries > 0:
                try:
                    # Brave Search API URL
                    url = f"{brave_instance}/res/v1/web/search"
                    headers = {
                        "X-Subscription-Token": os.environ["BRAVE_API_KEY"],
                        "Accept": "application/json",
                    }
                    resp = requests.get(url, headers=headers, params=payload, timeout=10)
                    resp.raise_for_status()
                    # print(resp.text)
                    if resp.headers.get("Content-Type", "").startswith("application/json"):
                        data = resp.json()
                        for result in data.get("web", {}).get("results", []):  # Correctly navigate to 'web' -> 'results'
                            results.append({
                                "title": result.get("title"),
                                "url": result.get("url"),
                                "content": result.get("description", ""),  # Use 'description' instead of 'content'
                                "search_query": search_query
                            })
                    else:
                        self._parse_html_response(resp.text)
                    break  # Exit the retry loop on success

                except requests.exceptions.HTTPError as e:
                    if resp.status_code == 429:  # Too Many Requests
                        # print(f"Rate limited. Retrying in {backoff} seconds...")
                        time.sleep(backoff)  # Wait before retrying
                        backoff *= 2  # Exponential backoff
                        retries -= 1
                    else:
                        # results.append({
                        #     "error": f"Error retrieving from {domain}",
                        #     "details": str(e),
                        #     "search_query": search_query
                        # })
                        break
                except requests.exceptions.RequestException as e:
                    # results.append({
                    #     "error": f"Error retrieving from {domain}",
                    #     "details": str(e),
                    #     "search_query": search_query
                    # })
                    break

        if len(results) > top_k:
            filtered = [r for r in results if 'content' in r]
            scored = [
                {
                    **r,
                    "score": self.calculate_relevance_score(r, r.get("search_query", ""))
                } for r in filtered
            ]
            
        else:
            filtered = [r for r in results if 'content' in r]
            scored = [
                {
                    **r,
                    "score": self.calculate_relevance_score(r, r.get("search_query", ""))
                } for r in filtered
            ]
        scored_results = sorted(scored, key=lambda x: x['score'], reverse=True)[:top_k]

        if read_content:
            # Fetch article content for top 5 results
            processed_count = 0
            for result in scored_results:
                if processed_count >= 5:
                    break

                url = result.get("url")
                if url:
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Extract content from <article> tags
                        article_content = ""
                        for article in soup.find_all("article"):
                            article_content += article.get_text(separator="\n").strip() + "\n"

                        # Append article content if available
                        if article_content.strip():
                            result["article_content"] = article_content.strip()[:10000]
                            processed_count += 1  # Increment the count of successfully processed results

                    except requests.exceptions.RequestException as e:
                        # result["article_content"] = f"Error retrieving article content: {str(e)}"
                        pass

        return {"search_results": scored_results}