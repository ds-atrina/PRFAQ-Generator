from prompts.constants import onefinance_guidelines, onefinance_info, role_info

def CONTENT_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, kb_content, competitor_results):
    return f"""{role_info}
        Generate a detailed PR FAQ introduction in JSON format for the topic ```{topic}```, leveraging the following provided information and enhancing them if necessary :
        1. The topic on which FAQ is to be generated: ``{topic}```
        2. The problem we are trying to tackle: ```{problem}```
        3. The solution to the problem or the features of the offering: ```{solution}```
        4. The chat history: ```{chat_history}```
        5. The extracted information from reference document (if available): {reference_doc_content}
        6. The web-scraped information (if available) and how it is relevant to 1 Finance's new offering: {web_scrape_content}
        7. Any relevant information extracted from the knowledge base: {kb_content}
        8. The competitors and their URLs: {competitor_results}

        ONLY USE INFORMATION PRESENT IN THE KNOWLEDGE BASE DO NOT MAKE UP INFORMATION.
        Use the web search tool to search for competitors and market research for popular products solving the same problem and their urls. Set trust to false, read_content to false and top_k as 20.
        Ensure that no specific dates, names, or locations are mentioned—use placeholders instead—and follow the provided JSON template exactly.

        You work for 1 Finance. {onefinance_info}
        Follow these additional writing and content guidelines of 1 Finance while generating the output:
        {onefinance_guidelines}

        OUTPUT FORMAT IN STRICT JSON:
        {{
            "Title": "1 FINANCE ANNOUNCES XXX TO ENABLE XXX TO OBTAIN/HAVE XXX.",
            "Subtitle": "The subtitle reframes the headline solution. Write one sentence about the benefits.",
            "IntroParagraph": "[Location] - [Launch Date] - 2-4 sentences that gives a summary of the product and the benefits. Should be self-contained so that a person could read only this paragraph and still understand the new product/feature.
            "ProblemStatement": "3-4 sentences describing the problems this product/feature plans to solve and briefly describe the problem and its negative impact. This section tests your assumptions about the pain-points that you are addressing.",
            "Solution": "3-5 sentences describing how the new product/feature addresses these problems. For more complex products/features, you may need more than one paragraph. This section tests your assumptions about how you are solving the pain-points.",
            "Competitors": [{{"name": "Company name or Product name", "url":"URL of the product website"}}] [LIST OF GENUINE COMPANIES/PRODUCTS JSON (don't make up names or URLs or use blogs)],
        }}
    """

def QUESTION_GENERATION_PROMPT(topic, problem, solution, chat_history):
    return f"""{role_info}
        You are tasked with generating clear, structured, and **non-redundant Internal and External FAQs** for a PRFAQ document using the inputs below:

        - **Topic**: {topic}
        - **Problem**: {problem}
        - **Solution**: {solution}
        - **Chat History (including PRFAQ introduction)**: {chat_history}

        ---

        ### Objective:
        Create ~9-10 well-structured questions each for:
        - **Internal FAQs** (for product, engineering, legal, etc.)
        - **External FAQs** (for customers, partners, press)

        Each section should follow a logical PRFAQ-style narrative — avoid random ordering.

        ---

        ### Step 1: Generate & Combine
        1. Generate 20 exhaustive questions per section.
        2. Combine/rephrase overlapping or similar questions (except fixed ones).
        3. Final output: ~9-10 concise, high-value questions per section.

        ---

        ### Mandatory Questions (Rephrasing allowed, but do not remove, combine, or relocate):

        #### Internal (must STRICTLY appear in **Internal FAQs only**):
        - Who is the target audience for this product who were facing the problem statement?
        - What is the potential impact on business/Return on Investment (ROI) for the company?
        - Which departments were involved, are currently involved, or will need to be involved in executing this, and what will their roles be?
        - Does it align with the company's philosophy?

        #### External (must STRICTLY appear in **External FAQs only**):
        - How will it impact/make the target audience's life better?

        These questions **must be slightly reframed for clarity** and appear **in random order within their correct section only**.

        ---

        ### Structure Guidance

        #### Internal FAQs: 
        Cover areas like:
        - Business rationale and market need
        - Product vision and alignment with company 
        - Why is this a problem that needs to be solved right now
        - Technical approach, risks, and scalability
        - Legal, compliance, and privacy concerns
        - Resourcing, timeline, and launch readiness
        - Success metrics and future roadmap

        #### External FAQs:
        Cover:
        - How it the product is to be used and how it helps the target audience
        - What the product is and what problems it solves
        - Pricing, availability, onboarding
        - Key features and known limitations
        - Security, privacy, and data handling
        - Support and future updates

        ---

        ### Inputs for Question Generation (in priority order):
        1. Problem & solution from `content_generation_agent` and chat history
        2. Output of `kb_agent`
        3. Output of `web_scrape_extractor` and `extract_info_agent`

        ---

        ### Important Constraints:
        - Do **not** introduce fabricated or assumed information
        - Avoid any duplication, overlap, or semantically similar questions
        - Keep tone aligned with 1 Finance brand:
        {onefinance_guidelines}

        You are acting on behalf of **1 Finance**:  
        {onefinance_info}

        ---

        ### Output Format (JSON):
        ```json
        {{
        "internal_questions": [
            "Rephrased internal Q1...",
            ...
        ],
        "external_questions": [
            "Rephrased external Q1...",
            ...
        ]
        }}
    """

def ANSWER_GENERATION_PROMPT(topic, problem, solution, chat_history, response, web_scrape_content, reference_doc_content):
    return f"""{role_info}
    You are generating the PR/FAQ document for the topic `{topic}`, problem statement {problem} and solution {solution}.
    You are supposed to generate proper markdown formatted answers for each question based on available information, the answers from KB and web search are as follows: 
    ```{response}```
    If a question does not have an answer in the knowledge base or web, use the output from the web scrape extraction task and the extract info task to answer the question.
    Web scrape content: ```{web_scrape_content}```
    Reference document content: ```{reference_doc_content}```
    The last resort should be using the generated content to frame an answer that is consistent with the other content of the PR/FAQ.
    Answer each question on the basis of this information and priority, framing it properly with proper formatting.
    
    **Important Considerations to be followed STRICTLY:**
      - Include clearly marked sub-points or bullet points (using string "\n-") or bold or italics for clarity. 
      - Include examples, step-by-step guidance, markdown-formatted tables where applicable.
      - Answer the question with specific, unique, and non-interchangeable sentences. Avoid generic or modular statements that could fit into other unrelated answers. Every sentence must be tightly connected to the context of this question only.
      - Answer the question clearly and precisely. Strictly avoid using jargon or generic phrases like 'state-of-the-art', 'leverage', 'cutting-edge', or any similar buzzwords. Use simple, specific language grounded in the actual context.
      - **Do not** repeat the same ideas.
      - It is possible that the answer is not present in the knowledge base, web search, web scrape, extract info task or generated content. In that case, the answer should be generated based on available information from trusted sources and maintain consistency throuhgout the document.
      
    UNDER NO CIRCUMSTANCES SHOULD FABRICATED OR ASSUMED CONTENT BE INTRODUCED. ALWAYS PRIORITISE VERIFIABLE, CREDIBLE INFORMATION FROM GIVEN CONTEXT OF KNOWLEDGE BASE, WEB SEARCH, WEB SCRAPING TASK AND EXTRACT INFO TASK.
    ANSWERS SHOULD BE EXTREMELY DETAILED, ALL-INFORMING AND WELL-FORMATTED.
    Add a user response field as a reply to what the user requested for in terms of modifications or generation: ```{chat_history[-1]}```.
    So UserResponse should be the reply that will be shown to the user as a response to their request for generating the PR/FAQ document along with the document.

    While generating the FAQs and answers, follow these stylistic and tone guidelines:
    {onefinance_guidelines}
    EXPECTED OUTPUT FORMAT IN JSON:   
    {{
    "InternalFAQs": [
          {{
              "Question": "How does the AI assistant integrate with existing tools?",
              "Answer": "It seamlessly integrates with platforms like \n-Slack \n-Microsoft Teams \n-CRM systems via APIs."
          }},
          {{
              "Question": "What kind of training data is required?",
              "Answer": "The AI assistant can be **fine-tuned** with company-specific data for enhanced performance."
          }}
      ],
      "ExternalFAQs": [
          {{
              "Question": "Is the AI assistant secure?",
              "Answer": "In order to ensure data security we use:\n- End-to-end encryption \n- Regular security audits \n- Compliance with GDPR and CCPA."
          }},
          {{
              "Question": "What the features and their corresponding benefits of the product?",
              "Answer": "| Feature         | Benefit        |\n|------------------|----------------|\n| Auto-Generate    | Saves time     |\n| LLM-Driven       | Context aware  |"
          }},
          {{
              "Question": "Name the competitors and compare it with our product in table form.",
              "Answer": [
                {{"Name": "Markdown Table", "Feature": "Yes"}},
                {{"Name": "JSON Table", "Feature": "Yes"}}
              ]
          }}
      ],
      "UserResponse": "Here is the generated PR/FAQ document on topic and your provided inputs. Please review and let me know if any changes are needed."
    }}
    """