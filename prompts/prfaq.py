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

    You are tasked with generating clear, structured, and **non-redundant Internal and External FAQs** for a PRFAQ document using the inputs below.
    ---

    ### Inputs
    - **Topic**: {topic}
    - **Problem**: {problem}
    - **Solution**: {solution}
    - **Chat History**: {chat_history}

    ---

    ### Step-by-Step Generation Process (MUST FOLLOW STRICTLY)

    ####  STEP 1: Draft Raw Questions  
    Generate **20 raw questions each** for:

    - **Internal FAQs**, focusing on:
    - Business rationale and market need  
    - Product vision and company alignment  
    - Urgency and timing  
    - Technical approach, scalability, and risks  
    - Legal, compliance, and privacy considerations  
    - Resources, timelines, launch readiness  
    - Success metrics and roadmap  

    - **External FAQs**, focusing on:
    - What the product is and the core problem it solves  
    - Target users and usage  
    - Pricing, onboarding, and availability  
    - Features and limitations  
    - Data handling, privacy, and security  
    - Support and updates roadmap  

    ---

    ####  STEP 2: Deduplicate & Prioritize  
    - Review all 20 raw questions in each section.  
    - **Merge or rephrase** any overlapping or semantically similar questions.  
    - Select the **8–9 most important, distinct, and high-value questions per section** to retain.

    ---

    ####  STEP 3: Add Mandatory Questions (STRICTLY ENFORCED)

    > Do not skip this step. Do not misplace. Do not duplicate. Mandatory questions are **non-negotiable**.

    After Step 2 is complete:
    - Insert the following **mandatory questions** into their **designated sections only**.
    - These must be inserted **in random order** (not grouped at the bottom) **within** the 8–9 curated questions.
    - These questions must appear **exactly once**, **only in their correct section**, and **must not be altered in meaning** (light rephrasing is allowed for clarity or tone).

    ---

    **Internal FAQs — Add ALL 4 questions ONLY to Internal section:**
    1. Who is the target audience for this product?  
    2. What is the potential impact on business/Return on Investment (ROI) for the company?  
    3. Which departments are or will be involved in the execution of this initiative, and what roles will they play?
    4. Does it align with the company's philosophy?

    > DO NOT place these in the External FAQs  
    > MUST appear **only once**, **randomly interspersed** in the Internal section
    > Final Internal FAQ count: **12–13** (8–9 generated + 4 mandatory)

    ---

    ** External FAQs — Add ONLY this 1 question to External section:**
    1. How will it impact/make the target audience's life better?

    > DO NOT place this in Internal FAQs  
    > MUST appear **only once**, **randomly interspersed** in the External section
    > Final External FAQ count: **9–10** (8–9 generated + 1 mandatory)

    ---

    ### Input References (in priority order):
    1. Problem & solution from `content_generation_agent` and `chat_history`  
    2. Output of `kb_agent`  
    3. Output of `web_scrape_extractor` and `extract_info_agent`  

    ---

   ### Hard Constraints
    -  Do not fabricate or assume facts not in the input  
    -  Do not duplicate or move mandatory questions  
    - Internal FAQs must contain **exactly 4 mandatory questions + 8–9 non-mandatory**  
    - External FAQs must contain **exactly 1 mandatory question + 8–9 non-mandatory**  
    - Mandatory questions must appear **only in their correct section** and **in random positions**  
    - Ensure Internal FAQs total to **12–13**, and External FAQs total to **9–10**

    ---

    ### Tone and Brand
    - Maintain tone and voice consistent with **1 Finance**:  
    {onefinance_guidelines}
    - Adhere to standards of positioning and accuracy:  
    {onefinance_info}

    ---
    ### Final Output Format 
    Return the output in JSON format like this:

    ```json
    {{
    "internal_questions": [
        "What are the key risks we’ve identified in deployment?",
        "How does this product align with our quarterly OKRs?",
        "Who is the target audience for this product?",
        "What is the potential impact on business/Return on Investment (ROI) for the company?",
        "Which departments are or will be involved in the execution of this initiative, and what roles will they play?"
        "Does it align with the company's philosophy?"
    ],
    "external_questions": [
        "What is the onboarding process for a new user?",
        "How does this solution differ from others in the market?",
        "How will it impact/make the target audience's life better?"
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