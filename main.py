# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import io
import os
import sys
import docx
import json
import time
import openai
from utils import extract_text_from_pdf, render_text_or_table_to_str
from langchain_openai import ChatOpenAI  
from langchain.agents import Tool
from langchain.tools import BaseTool
from crew import PRFAQGeneratorCrew
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from searxng_search import SearxNGTrustedSearchTool
from qdrant_tool import kb_qdrant_tool
from modify_faq import modify_faq

# Ensure `src/` is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Set your OpenAI API key here or use an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def display_output(output):
    """Function to display PR FAQ sections."""
    pr_faq_str = ""
    pr_faq_str += f"**Title:** {output.get('Title', '')}\n\n"
    pr_faq_str += f"**Subtitle:** {output.get('Subtitle', '')}\n\n"
    pr_faq_str += f"**Introduction Paragraph:** {output.get('IntroParagraph', '')}\n\n"
    pr_faq_str += f"**Customer Problems:** {output.get('CustomerProblems', '')}\n\n"
    pr_faq_str += f"**Solution:** {output.get('Solution', '')}\n\n"
    pr_faq_str += f"**Leader's Quote:** {output.get('LeadersQuote', '')}\n\n"
    pr_faq_str += f"**Getting Started:** {output.get('GettingStarted', '')}\n\n"
    pr_faq_str += f"**Customer Quotes:**\n"
    for quote in output.get("CustomerQuotes", []):
        pr_faq_str += f"\n*{quote}*\n"

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
    
# def modify_faq(existing_faq, user_feedback, problem, solution, topic):
#     search_tool = SearxNGTrustedSearchTool()
#     kb_tool = kb_qdrant_tool

#     tools = [
#         Tool(
#             name="Web Search",
#             func=search_tool.search_with_query,
#             description="Perform a web search to gather information required to modify the PR FAQ."
#         ),
#         Tool(
#             name="Knowledge Base Search",
#             func=kb_tool.run,
#             description="Search internal company knowledge base."
#         )
#     ]

#     # LLM
#     llm = ChatOpenAI(model="gpt-4o", temperature=0)

#     # Node: Prompt the LLM with PR FAQ update request
#     def modify_prfaq_llm_node(state):
#         topic = state['topic']
#         problem = state['problem']
#         solution = state['solution']
#         feedback = state['user_feedback']
#         existing = state['existing_faq']

#         prompt = f"""
#             You are an intelligent assistant tasked with modifying an existing PR FAQ based on user feedback.

#             The PR FAQ is generated based on the following:
#             - Problem statement: {problem}
#             - Solution: {solution}

#             User feedback:
#             "{feedback}"

#             If you need external info, you may call tools:
#             - Web Search: for latest public info
#             - Knowledge Base Search: for company docs

#             Only modify the necessary sections. Assume anything new is a FAQ unless specified.

#             ✅ Return STRICT JSON only. Use markdown tables if needed. No extra commentary.
#             Here is the existing PR FAQ:
#             ```{existing}```
#         """
#         return {
#             "messages": [HumanMessage(content=prompt)]
#         }

#     tool_node = RunnableLambda(lambda state: {
#         "tool_results": {
#             tool.name: tool.func(state["tool_query"])  # You can control what gets sent here
#             for tool in tools
#         }
#     })

#     # Node: output parsing
#     def format_json_output(state):
#         raw = state.get("messages")[-1].content
#         try:
#             raw = raw.replace("```json", "").replace("```", "").strip()
#             return {"updated_faq": json.loads(raw)}
#         except Exception as e:
#             return {"error": f"Failed to parse JSON: {str(e)}", "raw": raw}

#     # 🧠 Graph definition
#     def build_prfaq_graph():
#         builder = StateGraph()
#         builder.add_node("llm_modify", modify_prfaq_llm_node)
#         builder.add_node("tools", tool_node)
#         builder.add_node("json_output", format_json_output)

#         # Just a linear flow here
#         builder.set_entry_point("llm_modify")
#         builder.add_edge("llm_modify", "json_output")
#         builder.add_edge("json_output", END)

#         return builder.compile()
    
#     graph = build_prfaq_graph()
#     state = {
#         "existing_faq": existing_faq,
#         "user_feedback": user_feedback,
#         "problem": problem,
#         "solution": solution,
#         "topic": topic
#     }

#     result = graph.invoke(state, config=RunnableConfig(configurable={"tags": ["prfaq-modifier"]}))
#     if "updated_faq" in result:
#         return result["updated_faq"]
#     else:
#         print("[DEBUG] Response not valid JSON:\n", result.get("raw", ""))
#         return existing_faq
        
MAX_FILES = 5
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_LINKS = 5

def main():
    st.set_page_config(layout="wide")
    st.title("PR/FAQ Generator (Beta v2.0)")

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

                - **Click "Generate PR FAQ"**: The system will process your inputs and generate a PRFAQ. (*Note*: This process may take **3-5 minutes** depending on the complexity of your inputs.)

                - **View Execution Details**: The app will display the generated PRFAQ and the time taken to generate it.

                - **Interact with the Chat**: You can review the PRFAQ once created and provide feedback or additional prompts to refine it.
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
            # elif len(problem) < 20:
            #     st.error("Problem is too short. Please enter at least 20 characters.")
            # elif len(solution) < 50:
            #     st.error("Solution is too short. Please enter at least 50 characters.")
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
                        'context': 'This is some default context.',
                        'content': 'This is some default content.',
                        'reference_doc_content': reference_doc_content,
                        'web_scraping_links': links_list,
                        'use_websearch':use_websearch
                    }

                    # Generate PR FAQ using Crew
                    pr_faq_crew = PRFAQGeneratorCrew(inputs)
                    crew_output = pr_faq_crew.crew().kickoff(inputs=inputs)
                    cleaned_json = crew_output.raw.replace("```json","").replace("```","").strip()

                    try:
                        parsed_output = json.loads(cleaned_json)
                        st.session_state.pr_faq = parsed_output  # Store in session
                        st.success("PR FAQ generated successfully!")
                        st.session_state.chat_history.append({"role": "assistant", "content": display_output(parsed_output)})
                    except json.JSONDecodeError as e:
                        st.session_state.pr_faq = modify_faq(cleaned_json, "Solve this in my JSON, I got this error: " + str(e), problem, solution, topic)
                        
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                st.write(f"It took me {execution_time:.2f} seconds to generate this PR FAQ for you!")
                print(f"Token Usage: {crew_output.token_usage}")
    
    if st.session_state.pr_faq:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Enter your feedback or prompt:"):
            st.chat_message("user").markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.spinner('Updating your PRFAQ...'):
                # Process feedback or new prompt
                if st.session_state.pr_faq:
                    new_output = modify_faq(st.session_state.pr_faq, prompt, problem, solution, topic)
                    response = display_output(new_output)
                    st.session_state.pr_faq = new_output
                else:
                    response = f"{response}"

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()