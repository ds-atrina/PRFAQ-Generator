from typing import List, Dict, Any
import requests
import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.web_search.whitelisted_sites import whitelisted_domain_list, onefinance_whitelisted_sites
from dotenv import load_dotenv

load_dotenv() 

#llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.2, google_api_key=os.getenv("GOOGLE_API_KEY"))

class WebTrustedSearchTool:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.getenv("WEB_TRUSTED_SEARCH_API_URL", "https://dev-aion.onefin.app/api/v1/tools/web-search")

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
            f"Return ONLY the domain names in a list like ['domain1.com', 'domain2.com', 'domain3.com']."
        )
        response = llm.invoke(prompt)
        selected = []
        for domain in whitelisted_domain_list:
            if domain.lower() in response.content.lower():
                selected.append(domain)
        return selected

    def choose_onef_domains(self, query: str) -> List[str]:
        prompt = (
            f"You are helping a researcher identify the most relevant company websites to search.\n"
            f"Query: {query}\n"
            f"Here is a list of approved domains:\n{chr(10).join(onefinance_whitelisted_sites)} and their information:\n\n"
            """Below is a list of trusted, whitelisted sources and the types of data they provide:
            ---
            # Research & education platform for all macro indicators of India (indiamacroindicators.co.in)
            # Research and education platform for all cryptos with crypto scoring & ranking (indiacryptoresearch.co.in)
            # AI driven tax education and advisory (planmytax.ai)
            # Education and P2P as an asset offering (1financep2p.com)
            # Physical only magazine which features primary research, interviews we do related to financial industry (1financemagazine.com)
            # Community event to rasie awareness and bring together all personal finance related professionals (gfpsummit.com)
            # Community to bring together advisor's through stories who have shown high integrity and client first approach (fintegritystories.com)
            # Community to bring together HR's who care about employee wellness - mental and financial (indiahrconclave.com)
            """
            f"Pick the top 2 most likely to contain helpful info for this context. "
            f"Return ONLY the domain names in a list like ['domain1.com', 'domain2.com']."
        )
        response = llm.invoke(prompt)
        selected = []
        for domain in onefinance_whitelisted_sites:
            if domain.lower() in response.content.lower():
                selected.append(domain)
        return selected

    def call_web_search_api(self, query: str, read_content: bool, top_k: int, selected_domains: list) -> dict:
        payload = {
            "query": query,
            "read_content": read_content,
            "top_k": top_k,
            "selectedDomains": selected_domains
        }
        headers = {"Content-Type": "application/json"}
        # print(f"Calling web search API with payload: {payload}")
        resp = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def run(
        self,
        query: str,
        trust: bool = True,
        read_content: bool = False,
        top_k: int = 20,
        onef_search: bool = False
    ) -> Dict[str, Any]:
        """
        Uses LLM to select relevant domains, then calls the external web search API
        (which expects selectedDomains as a parameter).
        """
        selected_domains = [""]

        if trust:
            selected_domains.extend(self._choose_relevant_domains(query))
            selected_domains.remove("")

        if onef_search:
            selected_domains.extend(self.choose_onef_domains(query))
            selected_domains.append("1finance.co.in")
            if "" in selected_domains:
                selected_domains.remove("")
        
        if not selected_domains:
            selected_domains.append("")

        results = self.call_web_search_api(
            query=query,
            read_content=read_content,
            top_k=top_k,
            selected_domains=selected_domains
        )
        return results
    
if __name__ == "__main__":
    query = "latest RBI repo rate"
    tool = WebTrustedSearchTool()
    results = tool.run(query, read_content=True, top_k=5, trust=True, onef_search=True)
    print(results)
