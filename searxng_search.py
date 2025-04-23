from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, List, Dict, Any
import requests
import datetime
import re
from langchain_openai import ChatOpenAI
from urllib.parse import urlencode, urlparse
from whitelisted_sites import whitelisted_domain_list


class SearxSmartQuerySchema(BaseModel):
    topic: str = Field(..., description="Topic or product name (e.g., PlanMyTax.ai)")
    problem: str = Field(..., description="Problem being solved")
    solution: str = Field(..., description="Proposed solution")


class SearxNGTrustedSearchTool(BaseTool):
    name: str = "SearxNG Trusted Search Tool"
    description: str = (
        "Performs smart search on relevant whitelisted financial sites using a SearxNG instance"
    )
    args_schema: Type[BaseModel] = SearxSmartQuerySchema

    def _choose_relevant_domains(self, topic: str, problem: str, solution: str) -> List[str]:
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        prompt = (
            f"You are helping a researcher identify the most relevant websites to search.\n"
            f"Product Idea: {topic}\n"
            f"Problem: {problem}\n"
            f"Solution: {solution}\n\n"
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
        return selected[:3]

    def is_quality_content(self, text: str) -> bool:
        words = text.split()
        sentences = text.split(".")
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0
        return (
            len(words) > 50
            and len(sentences) > 3
            and 5 < avg_words_per_sentence < 30
            and "crawling error" not in text.lower()
            and "error fetching content" not in text.lower()
        )

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
                        score += 40
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

    def _run(self, topic: str, problem: str, solution: str) -> Dict[str, Any]:
        searx_instance = "https://search.valenceai.in/search"
        selected_domains = self._choose_relevant_domains(topic, problem, solution)

        if not selected_domains:
            return {"error": "No relevant domains selected. Try a broader topic or revise inputs."}

        results = []
        for domain in selected_domains:
            search_query = f"site:{domain} {topic} {problem} {solution}"
            payload = {
                "q": search_query,
                "format": "json",
                "theme": "simple"
            }

            try:
                # POST properly formatted form data
                encoded_payload = urlencode(payload)
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
                url = (
                    f"{searx_instance}?"
                    f"format=json&language=en&safesearch=1&engines=google,brave,duckduckgo,bing,yahoo,wikipedia,wikidata"
                )
                resp = requests.get(url, data=encoded_payload, headers=headers, timeout=10)
                resp.raise_for_status()

                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    data = resp.json()
                    for result in data.get("results", []):
                        results.append({
                            "title": result.get("title"),
                            "url": result.get("url"),
                            "content": result.get("content", ""),
                            "search_query": search_query
                        })
                else:
                    results.extend(self._parse_html_response(resp.text))

            except requests.exceptions.RequestException as e:
                results.append({
                    "error": f"Error retrieving from {domain}",
                    "details": str(e),
                    "search_query": search_query
                })

        MAX_RESULTS = 10
        if len(results) > MAX_RESULTS:
            filtered = [r for r in results if 'content' in r and self.is_quality_content(r['content'])]
            scored = [
                {
                    **r,
                    "score": self.calculate_relevance_score(r, r.get("search_query", ""))
                } for r in filtered
            ]
            results = sorted(scored, key=lambda x: x['score'], reverse=True)[:MAX_RESULTS]

        return {
            "search_results": results
        }

    def search_with_query(self, query: str) -> Dict[str, Any]:
        """Search SearxNG with a freeform query and fetch content from top 5 sites."""
        searx_instance = "https://search.valenceai.in/search"
        payload = {
            "q": query,
            "format": "json",
            "theme": "simple"
        }

        results = []
        try:
            # POST properly formatted form data
            encoded_payload = urlencode(payload)
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            url = (
                f"{searx_instance}?"
                f"format=json&language=en&safesearch=1&engines=google,brave,duckduckgo,bing,yahoo,wikipedia,wikidata"
            )
            resp = requests.post(url, data=encoded_payload, headers=headers, timeout=10)
            resp.raise_for_status()

            if resp.headers.get("Content-Type", "").startswith("application/json"):
                data = resp.json()
                for result in data.get("results", []):
                    results.append({
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": result.get("content", ""),
                        "search_query": query
                    })
                else:
                    results.extend(self._parse_html_response(resp.text))

        except requests.exceptions.RequestException as e:
            results.append({
                "error": f"Error retrieving results",
                "details": str(e),
                "search_query": query
            })

        MAX_RESULTS = 20
        if len(results) > MAX_RESULTS:
            filtered = [r for r in results]
            scored = [
                {
                    **r,
                    "score": self.calculate_relevance_score(r, query)
                } for r in filtered
            ]
            results = sorted(scored, key=lambda x: x['score'], reverse=True)[:MAX_RESULTS]

        # Ensure we process at least 5 results or all available results
        processed_count = 0
        for result in results:  # Go through all results if fewer than 5 valid ones are found
            if processed_count >= 5:  # Stop once we have processed 5 successful results
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
                    result["article_content"] = f"Error retrieving article content: {str(e)}"

        return {
            "search_results": results
        }