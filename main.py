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
from utils import extract_text_from_pdf
from knowledge_base import CompanyKnowledgeBase
from langchain_openai import ChatOpenAI  
from crew import PRFAQGeneratorCrew

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
        pr_faq_str += f"- {quote}\n"
    pr_faq_str += f"\n**Internal FAQs:**\n"
    for faq in output.get("InternalFAQs", []):
        pr_faq_str += f"\n**Q: {faq.get('Question', faq.get('question', 'Unknown Question'))}**\n"
        pr_faq_str += f"\nA: {faq.get('Answer', faq.get('answer', 'No answer provided'))}\n"
    pr_faq_str += f"\n**External FAQs:**\n"
    for faq in output.get("ExternalFAQs", []):
        pr_faq_str += f"\n**Q: {faq.get('Question', faq.get('question', 'Unknown Question'))}**\n"
        pr_faq_str += f"\nA: {faq.get('Answer', faq.get('answer', 'No answer provided'))}\n"
    return pr_faq_str

def modify_faq(existing_faq, user_feedback):
    llm = ChatOpenAI(model="gpt-4o") 
    prompt = f"""
    Here is the existing PR FAQ in triple quotes:
    ```{existing_faq}```

    The user provided the following feedback:
    "{user_feedback}"

    Modify only the necessary parts of the PR FAQ based on the feedback, DO NOT CHANGE THE FORMATTING OR THE STRUCTURE OF THE EXISTING PR FAQ and return the updated PR FAQ in STRICT JSON format.
    """

    response = llm.invoke(prompt)
    response_text = str(response.content)
    response_text = response_text.replace("```json","").replace("```","").strip()

    try:
        updated_faq = json.loads(response_text)
        return updated_faq
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse the updated PR FAQ: {e}")
        return existing_faq

def main():
    st.set_page_config(layout="wide")
    st.title("PR FAQ Generator (Interactive)")

    # Store PR FAQ and chat history in session state
    if "pr_faq" not in st.session_state:
        st.session_state.pr_faq = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.sidebar:
        st.header("Inputs")

        # User Inputs
        topic = st.text_input("Title*", "", placeholder="at least 3 characters", help= "Enter a concise title showcasing the main theme of your content.\ne.g., AI-Powered PRFAQ Generator", label_visibility="visible")
        problem = st.text_input("Problem*", "", placeholder="at least 50 characters", help= "Describe the issue or challenge that your solution addresses. Provide sufficient detail to clearly convey the problem.\ne.g., Crafting comprehensive PRFAQs is often time-consuming and requires significant effort, leading to delays in product development and communication", label_visibility="visible")
        solution = st.text_input("Solution*", "", placeholder="at least 50 characters", help= "Explain how your product or service effectively resolves the identified problem. Ensure the description is detailed.\ne.g., Introducing an AI-powered PRFAQ generator that automates the creation of detailed and accurate PRFAQs, streamlining the process and reducing time-to-market",  label_visibility="visible")
        web_scraping_link = st.text_input("Web Scraping Link (if any)", "", help= "Provide the URL of the webpage from which data needs to be extracted. Ensure the link is valid and accessible")
        reference_pdf = st.file_uploader("Upload Reference Document (if any)", type=["pdf", "docx"], help= "Attach a PDF or DOCX document that serves as a reference for your content. This could include reports, whitepapers, or existing PRFAQs")

        if st.button("Generate PR FAQ"):
            if len(topic) < 3:
                st.error("Title is too short. Please enter at least 3 characters.")
            elif len(problem) < 50:
                st.error("Problem input is too short. Please enter at least 50 characters.")
            elif len(solution) < 50:
                st.error("Solution input is too short. Please enter at least 50 characters.")
            else:
                with st.spinner('Generating the PRFAQ for you...'):
                    # Knowledge base initialization
                    start_time = time.perf_counter()
                    kb_path = 'vector_store/'
                    provided_kb_pdf = "1F_KB.pdf"

                    knowledge_base = CompanyKnowledgeBase(kb_path)
                    if provided_kb_pdf:
                        st.write(f"Updating knowledge base with {provided_kb_pdf}...")
                        if not knowledge_base.is_document_in_kb(provided_kb_pdf):
                            knowledge_base.add_pdf(provided_kb_pdf)
                            st.write("Knowledge base vector DB updated.")
                        else:
                            st.write(f"Document {provided_kb_pdf} is already in the knowledge base.")

                    # Extract reference document content
                    reference_doc_content = ""
                    if reference_pdf:
                        file_extension = os.path.splitext(reference_pdf.name)[1].lower()
                        if file_extension == ".pdf":
                            reference_doc_content = extract_text_from_pdf(reference_pdf)
                            st.write(f"Reference document {reference_pdf.name} read and processed.")
                        elif file_extension == ".docx":
                            doc = docx.Document(io.BytesIO(reference_pdf.read()))
                            reference_doc_content = "\n".join([para.text for para in doc.paragraphs])
                            st.write(f"Reference document {reference_pdf.name} read and processed.")
                        else:
                            st.error("Only pdf and docx files allowed.")

                    # Define inputs for PR FAQ generation
                    inputs = {
                        'topic': topic,
                        'problem': problem,
                        'solution': solution,
                        'context': 'This is some default context.',
                        'content': 'This is some default content.',
                        'reference_doc_content': reference_doc_content,
                        'web_scraping_link': web_scraping_link
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
                        st.session_state.pr_faq = modify_faq(cleaned_json, "Solve this in my JSON, I got this error: " + str(e))
                        # st.session_state.chat_history.append({"role": "assistant", "content": "Error: " + str(e)})

                end_time = time.perf_counter()
                execution_time = end_time - start_time
                st.write(f"It took me {execution_time:.2f} seconds to generate this PR FAQ for you!")

    # Display chat messages from history on app rerun
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Enter your feedback or prompt:"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.spinner('Updating your PRFAQ...'):
            # Process feedback or new prompt
            if st.session_state.pr_faq:
                new_output = modify_faq(st.session_state.pr_faq, prompt)
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