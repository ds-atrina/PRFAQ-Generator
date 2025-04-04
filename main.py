__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
import sys
import json
import openai
from utils import extract_text_from_pdf
from knowledge_base import CompanyKnowledgeBase
from langchain_openai import ChatOpenAI  
from crew import PRFAQGeneratorCrew

# Ensure `src/` is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Set your OpenAI API key here or use an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
# os.environ["CREWAI_TELEMETRY"] = "False"

def display_output(output):
    """Function to display PR FAQ sections."""
    st.subheader("Title")
    st.write(output.get("Title", ""))

    st.subheader("Subtitle")
    st.write(output.get("Subtitle", ""))

    st.subheader("Introduction Paragraph")
    st.write(output.get("IntroParagraph", ""))

    st.subheader("Customer Problems")
    st.write(output.get("CustomerProblems", ""))

    st.subheader("Solution")
    st.write(output.get("Solution", ""))

    st.subheader("Leader's Quote")
    st.write(output.get("LeadersQuote", ""))

    st.subheader("Getting Started")
    st.write(output.get("GettingStarted", ""))

    st.subheader("Customer Quotes")
    for quote in output.get("CustomerQuotes", []):
        st.write(quote)

    st.subheader("Internal FAQs")
    for faq in output.get("InternalFAQs", []):
        st.write(f"**Q: {faq.get('question', faq.get('Question', 'Unknown Question'))}**")   
        st.write(f"A: {faq.get('answer', faq.get('Answer', 'No answer provided'))}")

    st.subheader("External FAQs")
    for faq in output.get("ExternalFAQs", []):
        st.write(f"**Q: {faq.get('question', faq.get('Question', 'Unknown Question'))}**")
        st.write(f"A: {faq.get('answer', faq.get('Answer', 'No answer provided'))}")

def modify_faq(existing_faq, user_feedback):
    llm = ChatOpenAI(model="gpt-4o") 
    prompt = f"""
    Here is the existing PR FAQ in triple quotes:
    ```{existing_faq}```

    The user provided the following feedback:
    "{user_feedback}"

    Modify only the necessary parts of the PR FAQ based on the feedback, DO NOT CHANGE THE FORMATTING OF THE EXISTING PR FAQ and return the updated PR FAQ in STRICT JSON format.
    """

    response = llm.invoke(prompt)
    
    # Extract the content from the AIMessage object
    response_text = str(response.content)
    response_text = response_text.replace("```json","").replace("```","").strip()
    # print(response_text)
    # st.write(response_text)

    try:
        updated_faq = json.loads(response_text)
        return updated_faq
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse the updated PR FAQ: {e}")
        return existing_faq  # Return original if modification fails

def main():
    st.title("PR FAQ Generator (Interactive)")

    # Store PR FAQ in session state
    if "pr_faq" not in st.session_state:
        st.session_state.pr_faq = None

    # User Inputs
    topic = st.text_input("Topic*", "")
    problem = st.text_input("Problem*", "")
    solution = st.text_input("Solution*", "")
    web_scraping_link = st.text_input("Web Scraping Link", "")
    reference_pdf = st.file_uploader("Upload Reference Document PDF", type="pdf")

    if st.button("Generate PR FAQ"):
        if not topic:
            st.error("Please provide a Topic.")
        elif not problem:
            st.error("Please provide a Problem.")
        elif not solution:
            st.error("Please provide a Solution.")
        else:
            # Knowledge base initialization
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
                reference_doc_content = extract_text_from_pdf(reference_pdf)
                st.write(f"Reference document {reference_pdf.name} read and processed.")

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
                display_output(parsed_output)
            except json.JSONDecodeError as e:
                st.session_state.pr_faq = modify_faq(cleaned_json, "Solve this in my JSON, I got this error: "+e)
                # st.error(f"Error parsing JSON output: {e}")

    # Display and Modify Existing PR FAQ
    if st.session_state.pr_faq:
        feedback = st.text_area("Enter feedback to refine the PR FAQ:")
        if st.button("Update PR FAQ"):
            st.session_state.pr_faq = modify_faq(st.session_state.pr_faq, feedback)
            st.success("PR FAQ updated successfully!")

            # Show updated PR FAQ
            st.subheader("Updated PR FAQ")
            display_output(st.session_state.pr_faq)

if __name__ == "__main__":
    main()