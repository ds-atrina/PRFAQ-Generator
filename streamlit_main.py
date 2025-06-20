__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import io
import os
import sys
import docx
import json
import time
import openai
from utils.utils import extract_text_from_pdf, render_text_or_table_to_str, convert_to_json
from langchain_openai import ChatOpenAI  
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.qdrant_tool import kb_qdrant_tool
from tools.web_search.web_search import WebTrustedSearchTool
from graph import start_langgraph


# Ensure `src/` is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Set your OpenAI API key here or use an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def display_output(output):
    """Function to display PR FAQ sections."""
    pr_faq_str = ""
    pr_faq_str += f"*{output.get('UserResponse', '')}*\n\n"
    pr_faq_str += f"**Title:** {output.get('Title', '')}\n\n"
    pr_faq_str += f"**Subtitle:** {output.get('Subtitle', '')}\n\n"
    pr_faq_str += f"**Introduction Paragraph:** {output.get('IntroParagraph', '')}\n\n"
    pr_faq_str += f"**Problem Statement:** {output.get('ProblemStatement', '')}\n\n"
    pr_faq_str += f"**Solution:** {output.get('Solution', '')}\n\n"
    pr_faq_str += "**Leader's Quote:** \n\n"
    pr_faq_str += "**Customer's Quote:** \n\n"

    pr_faq_str += f"\n**Competitors:**\n"
    for competitor in output.get("Competitors", []):
        name = competitor.get("name", "")
        url = competitor.get("url", "")
        pr_faq_str += f"\n- [{name}]({url})\n"

    pr_faq_str += f"\n**Internal FAQs:**\n"
    for faq in output.get("InternalFAQs", []):
        question = faq.get('Question', faq.get('question', 'Unknown Question'))
        answer = faq.get('Answer', faq.get('answer', 'No answer provided'))

        pr_faq_str += f"\n**Q: {question}**\n"
        pr_faq_str += f"\nA:\n{render_text_or_table_to_str(answer)}\n"

    pr_faq_str += f"\n**External FAQs:**\n"
    for faq in output.get("ExternalFAQs", []):
        question = faq.get('Question', faq.get('question', 'Unknown Question'))
        answer = faq.get('Answer', faq.get('answer', 'No answer provided'))

        pr_faq_str += f"\n**Q: {question}**\n"
        pr_faq_str += f"\nA:\n{render_text_or_table_to_str(answer)}\n"

    return pr_faq_str

def chat_with_llm(existing_faq, user_feedback, topic, problem, solution, chat_history):
    """
    Chat with LLM to answer user questions or feedback.
    This function is optimized for performance and generalized for various conversational queries.
    """
    # Initialize LLM
    #llm = ChatOpenAI(model="o4-mini", temperature=1)  # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.2)

    refine_prompt = f"""
        The user provided the following feedback:
        "{user_feedback}"
        The current PR FAQ is based on the following context:
        Topic: {topic}
        Problem statement: {problem}
        Solution: {solution}

        Based on this feedback and the given context of topic, problem statement and solution, determine the most effective search query to put in a search engine to gather relevant and latest information user feedback query around the topic, problem or solution.
        Do not give specific queries about the product, be more general so that any relevant information regarding the problem or solution can be collected, even if it is not exact.
        You can consider India for location-specific searches if required unless mentioned otherwise.
        Avoid mentioning proper nouns or dates/years in the prompt, instead use words like "latest" and general key terms from the context. 
        Return ONLY the refined search query without any additional text.
    """
    refined_query_response = llm.invoke(refine_prompt)
    refined_query = refined_query_response.content.strip()

    kb_response = kb_qdrant_tool.run(refined_query)

    web_tool = WebTrustedSearchTool()
    web_response = web_tool.run(
        query=refined_query,
        trust=True,
        read_content=False,
        top_k=5,
        onef_search=False
    )
    
    # print(f"""The context fusion tool returned the following context for query {refined_query}:\n {context_response}""")

    prompt = f"""You are an intelligent assistant tasked with responding to user response.

        User response:
        "{user_feedback}"

        The PR FAQ is generated based on the following:
        - Topic: {topic}
        - Problem statement: {problem}
        - Solution: {solution}


        A search was carried out for the feedback with the refined query:
        "{refined_query}"

        The response from knowledge base search is as follows:
        {kb_response}

        The response from web search is as follows:
        {web_response}

        Here is the chat history for context:
        {json.dumps(chat_history[-6:], indent=4)}

        Answer the user response based on the user feedback and the given context of topic, problem statement and solution, using web search or knowledge base results. 
        In the case that it is not related to the topic, problem statement or solution, just respond to the user based on what they said. Like responding to thank you with you are welcome and I am here to help you if you need anything and so on.
        Ensure your reply is consistent with the FAQs, if not, mention that to the user. Answer as if you are answering an FAQ. Do not give lengthy answers, be concise and to the point.
        Do not answer negatively or vaguely like "I don't know" or "Not specified." 
        ONLY RETURN THE GENERATED ANSWER, NO EXTRA TEXT. If required, include examples, step-by-step guidance, markdown-formatted tables where applicable, and clearly marked sub-points or bullet points ("\n-") or bold or italics for clarity. 
        
        Here is the current PRFAQ for context:
        "{existing_faq}"
    """
    response = llm.invoke(prompt)

    # Step 5: Return the generated response
    return response.content.strip()
    
def modify_faq(existing_faq, user_feedback, topic, problem, solution, chat_history):
    """
    Modify an existing PR FAQ based on user feedback, chat history, and additional context. 
    This function uses refined search queries to gather relevant information from web and knowledge base searches.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.2)

    refine_prompt = f"""
        The user provided the following feedback:
        "{user_feedback}"
        The current PR FAQ is based on the following context:
        Topic: {topic}
        Problem statement: {problem}
        Solution: {solution}

        - Based on this feedback and the given context of topic, problem statement and solution, determine the most effective search query to put in a search engine to gather relevant and latest information user feeback query around the topic, problem or solution.
        - Create a search query that balances specificity and breadth: it should aim to gather **detailed, structured information** that can answer the user feedback precisely (for example, cost breakdowns, competitor feature tables, regional insights), while also being broad enough to capture related insights.
        - You can consider India for location-specific searches if required unless mentioned otherwise.
        - Avoid mentioning proper nouns or dates/years in the prompt, instead use words like "latest" and general key terms from the context. 
        - Prioritise Indian market context by default unless stated otherwise.
        - If the query involves costing or pricing, explicitly add "India" and "cost breakdown" or "pricing table" in the search query.
        - Return ONLY the refined search query as a string without any additional text.         
    """
    refined_query_response = llm.invoke(refine_prompt)
    refined_query = refined_query_response.content.strip()

    kb_response = kb_qdrant_tool.run(refined_query)

    web_tool = WebTrustedSearchTool()
    web_response = web_tool.run(
        query=refined_query,
        trust=True,
        read_content=False,
        top_k=5,
        onef_search=False
    )
    
    # print(f"""The context fusion tool returned the following context for query {refined_query}:\n {context_response}""")        

    prompt = f"""
        You are an intelligent assistant working at 1Finance tasked with modifying an existing PR FAQ based on user feedback.

        The PR FAQ is generated based on the following:
        - Problem statement: {problem}
        - Solution: {solution}

        User feedback:
        "{user_feedback}"

        Here is the chat history for context:
        "{json.dumps(chat_history[-6:], indent=4)}"

        Carefully identify what the user wants to do exactly based on the chat history and current user feedback. 
        If the request can be handled by the past conversational context, do not use further information to make the modifications.
        Use the below information, if required, to make appropriate changes in the PR FAQ. 

        A search was carried out for the feedback with the refined query:
        "{refined_query}"

        The response from knowledge base search is as follows:
        {kb_response}

        The response from web search is as follows:
        {web_response}

        Here is the existing PR FAQ:
        ```{existing_faq}```

        Instructions:
        - Modify the PR FAQ comprehensively based on the user feedback, ensure the PR FAQ is consistent throughout and any changes or additions are reflected throughout the prfaq.
        - Change the UserResponse field according to the user's feedback. It should be a reply to the user's message.
        - Use information from the search results or knowledge base to make the required changes or additions in the PR FAQ. Give relevant, latest and comprehensive answers from the retrieved information.
        - Ensure that any new information aligns with the problem statement and solution provided.
        - [STRICT] Whenever the user feedback requests a table, ensure that the response **must include a well-formatted markdown table.** If the retrieved information lacks a table, extract the relevant data points and **format them into a table yourself.**
        - For cost/pricing-related feedback, always assume the country context is India (unless otherwise stated) and provide costs in INR. Avoid using USD or other currencies unless specified.
        - Prioritise Indian market context by default unless the user specifies otherwise.
        - Assume any new feedback is a FAQ unless specified otherwise.
        - [STRICT] DO NOT CHANGE THE FORMATTING OR THE STRUCTURE OF THE EXISTING PR FAQ and return the entire (ALL FIELDS WITHOUT OMITTING ANY, AS THEY ARE WITH UPDATES, IF ANY), updated PR FAQ in STRICT JSON format: Use double quotes to wrap keys and values.
            Title: str
            Subtitle: str
            IntroParagraph: str
            ProblemStatement: str
            Solution: str
            Competitors: list of dict
            InternalFAQs: list
            ExternalFAQs: list
            UserResponse: str
        eg. {{
                "Title": "Revolutionizing AI Assistants",
                "Subtitle": "Introducing the Next-Gen AI for Business Solutions",
                "IntroParagraph": "In today's digital age, businesses need smarter AI solutions to streamline workflows and improve efficiency. Our new AI assistant is here to revolutionize the way companies operate.",
                "ProblemStatement": "Many businesses struggle with automating repetitive tasks, improving customer support, and handling large volumes of inquiries efficiently.",
                "Solution": "Our AI assistant leverages cutting-edge NLP and machine learning to provide seamless automation, personalized responses, and real-time insights.",
                "Competitors": [
                    {{
                    "name":"Amazon Rekognition", 
                    "url":"https://docs.aws.amazon.com/rekognition/"
                    }}, 
                    {{
                    "name":"Google Cloud Vision API", 
                    "url":"https://cloud.google.com/vision/docs/detecting-safe-search"
                    }}
                ],
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
                        "Answer": "Yes, we use industry-standard encryption and compliance measures to ensure data security."
                    }},
                    {{
                        "Question": "Can the AI assistant handle multiple languages?",
                        "Answer": "Absolutely! It's developed in a way that supports multiple languages and can be customized based on user needs."
                    }},
                    {{
                        "Question": "Can I use Markdown-style tables?",
                        "Answer": "| Feature         | Benefit        |\n|------------------|----------------|\n| Auto-Generate    | Saves time     |\n| LLM-Driven       | Context aware  |"
                    }},
                    {{
                        "Question": "Can I also return JSON-style tables?",
                        "Answer": [
                            {{"Input Type": "Markdown Table", "Support": "Yes"}},
                            {{"Input Type": "JSON Table", "Support": "Yes"}}
                        ]
                    }}
                ],
                "UserResponse": "Here is the generated PR/FAQ document on topic and your provided inputs. Please review and let me know if any changes are needed."
            }}
        - Avoid vague responses like "I don't know" or "Not specified." Use the given context to derive meaningful answers or omit such points.

        - While generating the FAQs and answers, follow these stylistic and tone guidelines:
            - Use British English (e.g., "capitalise," "colour").
            - Keep language human, positive and transparent.
            - Ensure the tone is formal yet personable, clear, and consistent with brand values.
            - Avoid technical jargon unless necessary, and explain all abbreviations/acronyms.

        Here is the existing PR FAQ:
        ```{existing_faq}```
    """
    response = llm.invoke(prompt)

    updated_faq = convert_to_json(response.content)
    return updated_faq
    
MAX_FILES = 5
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_LINKS = 5

def main():
    st.set_page_config(layout="wide")
    st.title("PR/FAQ Generator (Beta v4.0)")

    # Store PR FAQ and chat history in session state
    if "pr_faq" not in st.session_state:
        st.session_state.pr_faq = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.sidebar:
        with st.expander("How to Use Guide"):
            st.markdown("""
                **How to Use**

                - **Fill out the required fields in the sidebar**:
                    - **Title**: Enter a concise title for your PRFAQ (minimum 3 characters).
                    - **Problem**: Describe the challenge or issue your solution addresses (minimum 20 characters).
                    - **Solution**: Explain how your solution resolves the problem (minimum 50 characters).
                    - **Reference Links**: *Optional* Provide URLs for additional reference material.
                    - **Upload Reference Documents**: *Optional* Upload PDF or DOCX files for context.
                    - **Use Web Search**: Turn the switch on to use web search capabilities for generating your PRFAQ using latest and relevant information.

                - **Click "Generate PR FAQ"**: The system will process your inputs and generate a PRFAQ. (*Note*: This process may take **4-8 minutes** depending on the complexity of your inputs.)

                - **View Execution Details**: The app will display the generated PRFAQ and the time taken to generate it.

                - **Interact with the Chat**: You can review the PRFAQ once created and provide feedback or additional prompts to refine it.
                    - **Use @generate**: To regenerate the PR FAQ with modifications.
                    - **Other Prompts**: Ask questions or provide feedback to get a response from the assistant.
            """)

        # User Inputs
        st.header("Inputs")

        topic = st.text_input("Title*", "", placeholder="at least 3 characters", help= "Enter a concise title showcasing the main theme of your content.\ne.g., AI-Powered PRFAQ Generator", label_visibility="visible")
        problem = st.text_input("Problem*", "", placeholder="at least 20 characters", help= "Describe the issue or challenge that your solution addresses. Provide sufficient detail to clearly convey the problem.\ne.g., Crafting comprehensive PRFAQs is often time-consuming and requires significant effort, leading to delays in product development and communication", label_visibility="visible")
        solution = st.text_input("Solution*", "", placeholder="at least 50 characters", help= "Explain how your product or service effectively resolves the identified problem. Ensure the description is detailed.\ne.g., Introducing an AI-powered PRFAQ generator that automates the creation of detailed and accurate PRFAQs, streamlining the process and reducing time-to-market",  label_visibility="visible")
        web_scraping_links = st.text_input("Reference Links (if any)", "", help= "Provide upto 5 comma separated URLs of the webpages that serve as a reference for your content. Ensure the links are valid and accessible")
        reference_docs = st.file_uploader("Upload Reference Documents (if any)", type=["pdf", "docx"], accept_multiple_files=True, help= "Attach upto 5 PDF or DOCX documents, each may be upto 25 MB, that serve as a reference for your content. This could include reports, whitepapers, or existing PRFAQs")
        use_websearch = st.toggle("Use Web Search", value=False)

        if st.button("Generate PR FAQ"):
            if len(topic) < 3:
                st.error("Title is too short. Please enter at least 3 characters.")
            elif len(problem) < 20:
                st.error("Problem is too short. Please enter at least 20 characters.")
            elif len(solution) < 50:
                st.error("Solution is too short. Please enter at least 50 characters.")
            else:
                # Validate links
                links_list = [link.strip() for link in web_scraping_links.split(",") if link.strip()]
                if len(links_list) > MAX_LINKS:
                    st.error(f"Too many reference links. Max allowed: {MAX_LINKS}")
                    return

                # Validate file upload
                if reference_docs and len(reference_docs) > MAX_FILES:
                    st.error(f"Too many files uploaded. Max allowed: {MAX_FILES}")
                    return

                oversized_files = [doc.name for doc in reference_docs if doc.size > MAX_FILE_SIZE_BYTES]
                if oversized_files:
                    st.error(f"The following files exceed {MAX_FILE_SIZE_MB}MB limit: {', '.join(oversized_files)}")
                    return
                
                with st.spinner('Processing your inputs...'):
                    start_time = time.perf_counter()

                    reference_doc_content = []
                    if reference_docs:
                        for reference_doc in reference_docs:
                            content = ""
                            file_extension = os.path.splitext(reference_doc.name)[1].lower()
                            if file_extension == ".pdf":
                                content += extract_text_from_pdf(reference_doc)
                                st.write(f"Reference document {reference_doc.name} read and processed.")
                            elif file_extension == ".docx":
                                doc = docx.Document(io.BytesIO(reference_doc.read()))
                                content += "\n".join([para.text for para in doc.paragraphs])
                                st.write(f"Reference document {reference_doc.name} read and processed.")
                            else:
                                st.error(f"Only PDF and DOCX files are allowed. {reference_doc.name} is not a valid type.")
                            reference_doc_content.append(content)

                with st.spinner('Generating the PRFAQ for you...'):
                    # Define inputs for PR FAQ generation
                    inputs = {
                        'topic': topic,
                        'problem': problem,
                        'solution': solution,
                        'chat_history': ["Generate this PR/FAQ for me"],
                        # 'context': 'This is some default context.',
                        # 'content': 'This is some default content.',
                        'reference_doc_content': reference_doc_content,
                        'web_scraping_links': links_list,
                        'use_websearch':use_websearch
                    }

                    step_placeholder = st.empty()

                    def streamlit_step_callback(data):
                        step_placeholder.info(f"**Step:** {data['step']}\n\n{data['detail']}")

                    cleaned_json = start_langgraph(inputs, streaming_callback=None)
                    # print(f"Generated PR FAQ: {cleaned_json}")
                    try:
                        st.session_state.pr_faq = cleaned_json  # Store in session
                        st.success("PR FAQ generated successfully!")
                        st.session_state.chat_history.append({"role": "assistant", "content": display_output(cleaned_json)})
                    except json.JSONDecodeError as e:
                        st.session_state.pr_faq = modify_faq(cleaned_json, "Solve this in my JSON, I got this error: " + str(e), topic, problem, solution)
                        
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                st.write(f"It took me {execution_time:.2f} seconds to generate this PR FAQ for you!")
                # print(f"Token Usage: {crew_output.token_usage}")
    
    if st.session_state.pr_faq:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Use @generate in your query to update your PR/FAQ, else chat with AI:"):
            st.chat_message("user").markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            if "@generate" in prompt.lower():
                with st.spinner('Updating your PRFAQ...'):
                    # Process feedback or new prompt
                    new_output = modify_faq(st.session_state.pr_faq, prompt, topic, problem, solution, st.session_state.chat_history)
                    response = display_output(new_output)
                    st.session_state.pr_faq = response
                    
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
            else:
                with st.spinner('Answering your query...'):
                    # Process feedback or new prompt
                    new_output = chat_with_llm(st.session_state.pr_faq, prompt, topic, problem, solution, st.session_state.chat_history)
                    
                    # Display assistant response in chat message container
                    with st.chat_message("assistant"):
                        st.markdown(render_text_or_table_to_str(new_output))
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": new_output})
 

if __name__ == "__main__":
    main()
