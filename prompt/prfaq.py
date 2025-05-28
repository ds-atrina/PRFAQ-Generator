from prompt.constants import onefinance_guidelines

def CONTENT_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, kb_content, competitor_results):
    return f"""Generate a detailed PR FAQ introduction in JSON format for the topic ```{topic}```, leveraging the following provided information and enhancing them if necessary :
        1. The topic on which FAQ is to be generated: ``{topic}```
        2. The problem we are trying to tackle: ```{problem}```
        3. The solution to the problem or the features of the offering: ```{solution}```
        4. The chat history: ```{chat_history}```
        4. The extracted information from reference document (if available): {reference_doc_content}
        5. The web-scraped information (if available) and how it is relevant to 1 Finance's new offering: {web_scrape_content}
        6. Any relevant information extracted from the knowledge base: {kb_content}
        7. The competitors and their URLs: {competitor_results}

        ONLY USE INFORMATION PRESENT IN THE KNOWLEDGE BASE DO NOT MAKE UP INFORMATION.
        Use the web search tool to search for competitors and market research for popular products solving the same problem and their urls. Set trust to false, read_content to false and top_k as 20.
        Ensure that no specific dates, names, or locations are mentioned—use placeholders instead—and follow the provided JSON template exactly.

        Follow these additional writing and content guidelines of 1 Finance while generating the output:
        {onefinance_guidelines}
        OUTPUT FORMAT IN STRICT JSON:
        {{
        "Title": "1 FINANCE ANNOUNCES XXX TO ENABLE XXX TO OBTAIN/HAVE XXX.",
        "Subtitle": "The subtitle reframes the headline solution. Write one sentence about the benefits.",
        "IntroParagraph": "[Location] - [Launch Date] - 2-4 sentences that gives a summary of the product and the benefits. Should be self-contained so that a person could read only this paragraph and still understand the new product/feature.
        "ProblemStatement": "3-4 sentences describing the problems this product/feature plans to solve and briefly describe the problem and its negative impact. This section tests your assumptions about the pain-points that you are addressing.",
        "Solution": "3-5 sentences describing how the new product/feature addresses these problems. For more complex products/features, you may need more than one paragraph. This section tests your assumptions about how you are solving the pain-points.",
        "Competitors": [{{"name": "Company name or Product name", "url":"URL of the product website"}}] [LIST OF GENUINE COMPANIES JSON]
        }}
    """

def QUESTION_GENERATION_PROMPT(topic, problem, solution, chat_history):
    return f"""Generate exhaustive and non-redundant internal and external questions about the topic `{topic}`, problem statement `{problem}` and solution `{solution}`, guided by the chat history and existing PRFAQ introduction from content_generation_task.
        1.**Internal FAQs**: (20 questions) focusing on:
            - Business rationale, market need and target audience facing the issue
            - Potential impact on business/Return on Investment (ROI) for the company
            - Departments and their role in this execution, internal stakeholders, dependencies
            - Product vision and alignment with company 
            - Why is this a problem that needs to be solved right now
            - Technical approach, risks, and scalability
            - Legal, compliance, and privacy concerns
            - Resourcing, timeline, and launch readiness
            - Success metrics and future roadmap

        2.**External FAQs**: (20 questions) focusing on:
            - What the product is and what problems it solves
            - Who it's for and how it's used and its impact on their lives (how it makes their life better)
            - Pricing, availability, and onboarding process
            - Key features and known limitations
            - Security, privacy, and data handling
            - Support and future updates

        Now from the list of 20 questions each, combine certain questions that are similar or overlapping in nature or may have an answer in a similar vein to make it more concise and relevant.
        After combining these questions, make sure that the count of questions in each category is around 8-10.
            
        To generate more relevant and specific questions use the following information in order of importance:
        1. Use the problem statement and solution from the output of content_generation_agent and the context from user chat history ```{chat_history}``` to generate relevant questions. 
        2. Use the information from the output of kb_agent.
        3. Use the information from the output of web_scrape_extractor and the output of extract_info_agent.

        **Important Considerations to be followed STRICTLY:**
            - THE QUESTIONS SHOULD BE EXHAUSTIVE.
            - **Do not** repeat the same ideas.
            - **Do not** introduce REDUNDANT, OVERLAPPING, or unnecessarily similar questions.
        
        UNDER NO CIRCUMSTANCES SHOULD FABRICATED OR ASSUMED CONTENT BE INTRODUCED. ALWAYS PRIORITISE VERIFIABLE, CREDIBLE INFORMATION.

        While generating the FAQs and answers, follow these stylistic and tone guidelines:
        {onefinance_guidelines}

        EXPECTED OUTPUT IN JSON:
        {{
            "internal_questions": [
                "How does this product align with our Q4 strategic goals?",
                ...
            ],
            "external_questions": [
                "How can users get started with the new AI assistant?",
                ...
            ]
        }}"""
    prompt = ANSWER_GENERATION_PROMPT(topic, problem, solution, chat_history, reference_doc_content, web_scrape_content, generated_content, response)

def ANSWER_GENERATION_PROMPT(topic, problem, solution, chat_history, response, web_scrape_content, reference_doc_content):
    return f""" You are generating the PR/FAQ document for the topic `{topic}`, problem statement {problem} and solution {solution}.
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