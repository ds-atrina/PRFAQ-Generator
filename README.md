# PRFAQ-Generator

A system for generating PR/FAQ documents using AI agents and multiple data sources. This tool leverages CrewAI, OpenAI, and various information retrieval mechanisms to create comprehensive PR/FAQ documents based on user inputs.

## Project Structure

```
PRFAQ-Generator/
├── main.py                     # Streamlit application entry point
├── crew.py                     # Core orchestration logic
├── requirements.txt            # Project dependencies
├── config/                     # Configuration files
│   ├── agents.yaml             # Agent definitions
│   └── tasks.yaml              # Task definitions
├── utils/                      # Utility functions
│   ├── utils.py                # Common utility functions
│   └── qdrant_multiple_files.py # Qdrant collection setup
└── tools/                      # Tool implementations
    ├── qdrant_tool.py          # Knowledge base query tool
    ├── context_fusion_tool.py  # Context fusion functionality
    └── web_search/             # Web search components
        ├── web_search.py       # Web search implementation
        └── whitelisted_sites.py # Trusted domains list
```

## Core Components

### Main Application Files

#### streamlit_main.py
The Streamlit application entry point that provides the user interface.
- Handles user input collection (topic, problem, solution)
- Manages file uploads (PDF/DOCX) with validation
- Coordinates PR/FAQ generation process
- Displays generated content with formatting
- Provides feedback mechanism for refining results 

#### crew.py
Core orchestration logic for the PR/FAQ generation process using CrewAI.
- Defines the `PRFAQGeneratorCrew` class that coordinates agents and tasks
- Manages conditional execution based on user inputs
- Handles data flow between tasks
- Integrates with external tools and services 

### Configuration Files

#### config/agents.yaml
Defines the AI agents used in the system with their roles, goals, and backstories.
- Knowledge Base Agent: Retrieves information from the knowledge base
- Web Scrape Extractor: Extracts content from provided URLs
- Extract Info Agent: Extracts information from reference documents
- Content Generation Agent: Generates PR/FAQ introduction
- Question Generation Agent: Generates the questions for internal and external FAQs
- Answer Generation Agent: Hits the Knowledge Base and Web Search, if required, to answer each question and merges with the introduction to generate the final PR/FAQ

#### config/tasks.yaml
Defines the tasks that agents perform and their expected outputs.
- Knowledge Base Retrieval: Queries the knowledge base
- Web Search: Searches the web for information
- Web Scrape Extraction: Extracts content from URLs
- Extract Info: Processes reference documents
- Content Generation: Creates PR/FAQ introduction
- Question Generation: Generates comprehensive questions 
- Answer Generation: Generates answers from KB and web search and generates the final combined PR/FAQ

### Utility Functions

#### utils/utils.py
Common utility functions used throughout the application.
- `extract_text_from_pdf`: Extracts text from PDF files using PyMuPDF
- `remove_links`: Removes URL links from text
- `get_openai_llm`: Creates an OpenAI LLM instance
- `render_text_or_table_to_str`: Formats data for display

#### utils/qdrant_multiple_files.py
Handles the creation and management of Qdrant vector database collections.
- Creates and configures vector collections
- Processes and chunks text for efficient storage
- Generates embeddings using OpenAI
- Inserts data into the Qdrant database 

### Tool Implementations

#### tools/qdrant_tool.py
Provides integration with the Qdrant vector database for knowledge retrieval.
- `QdrantTool` class: Implements the CrewAI tool interface
- Handles connection with the Qdrant client 

#### tools/context_fusion_tool.py
Combines information from multiple sources to create a coherent context.
- Merges knowledge base results with web search data
- Resolves conflicts between different information sources
- Prioritizes information based on relevance and reliability

#### tools/web_search
##### web_search.py
Implements web search functionality using Brave.
- `WebTrustedSearchTool` class: Performs web searches
- Domain relevance scoring and content quality assessment
- HTML response parsing for extracting search results

##### whitelisted_sites.py
Contains lists of trusted domains and specific URLs for web searches.
- `whitelisted_site_list`: Specific trusted URLs
- `whitelisted_domain_list`: Trusted domains for filtering search results 

## System Workflow

1. **User Input**: User provides topic, problem, solution, and optional reference materials via the Streamlit UI
2. **Information Gathering**: System retrieves information from:
   - Knowledge base (Qdrant vector database)
   - Web search (Brave search with trusted domains)
   - Uploaded documents (PDF/DOCX)
   - Provided URLs
3. **Content Generation**: AI agents process gathered information to generate:
   - PR/FAQ introduction with title, subtitle, problem statement, etc.
   - Internal FAQs (8-10 questions) for stakeholders
   - External FAQs (8-10 questions) for customers
4. **Output & Refinement**: System presents the generated PR/FAQ and allows for feedback and refinement

## Setup and Usage

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `QDRANT_URL`: URL of your Qdrant service
   - `QDRANT_COLLECTION_NAME`: Collection in your Qdrant service to be used as Knowledge Base
   - `BRAVE_API_KEY`: Your Brave API key for web search
   To use the APIs, you will also need:
   - `SUPABASE_URL`: The URL of Supabase where the inputs are fetched from
   - `SUPABASE_KEY`: The key of Supabase where the inputs are fetched from

3. Run the application:
   ```
   streamlit run main.py
   ```

4. Access the UI at http://localhost:8501

## Dependencies

- Python 3.11
- Streamlit
- OpenAI API
- CrewAI
- Qdrant
- SearxNG
- PyMuPDF (fitz)
- python-docx
- BeautifulSoup4
- Pandas

## Notes

This system uses a multi-agent approach with CrewAI to generate comprehensive PR/FAQ documents. The architecture follows a modular design with UI, orchestration, agent, and task layers working together. The system integrates with external services for knowledge retrieval and web search, ensuring information is gathered from trusted sources.
