That's a great idea\! Presenting this project in a `README.md` format makes it easy to share, start, and understand.

Here is the complete **Agentic RAG for Sri Lankan Law** project breakdown, ready for you to copy and paste into a `README.md` file.

-----

## 🇱🇰 Lanka Legal Analyst (LLA): An Agentic RAG Chatbot

### Project Overview

**Lanka Legal Analyst (LLA)** is a state-of-the-art legal research assistant powered by **Agentic Retrieval-Augmented Generation (RAG)**. Its purpose is to provide highly accurate, grounded, and citable information exclusively on **Sri Lankan Law**.

Unlike traditional chatbots, LLA uses a system of specialized AI agents to plan, search, synthesize, and validate answers against official Acts, Ordinances, and Case Law, ensuring legal accuracy and minimizing hallucinations.

### Core Technology Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Orchestration** | Python, LangChain / LlamaIndex | Manages the workflow and controls the interaction between sub-agents and tools. |
| **LLM Backend** | GPT-4o, Claude 3.5, or Local LLMs (e.g., Llama 3) | Provides the reasoning, planning, and final text generation capabilities. |
| **Vector Database** | ChromaDB, Pinecone, or Weaviate | Stores the numerical embeddings of legal texts for semantic retrieval. |
| **Data Sources** | Acts, Ordinances, Gazettes (Official PDFs/Text) | The authoritative corpus of Sri Lankan law (requires initial scraping and preprocessing). |
| **Embedding Model** | Legal-tuned model (e.g., BGE-M3 or specialized legal embeddings) | Converts legal text into high-quality vectors for precise retrieval. |

### 🧠 Agentic RAG Architecture

The LLA system employs a multi-agent structure to handle complex legal queries:

1.  **Router Agent:** Analyzes the user query and determines the complexity (Simple Fact, Statutory Interpretation, Case Law needed).
2.  **Query Planning Agent:** Breaks down complex, multi-faceted questions (e.g., "property law and immigration rules") into sequential sub-queries.
3.  **Statutory Agent:** Specializes in searching and retrieving exact sections from specific Acts (e.g., *Penal Code*, *Companies Act*).
4.  **Case Law Agent:** Searches for and summarizes relevant precedents (judgments) from the Supreme Court or Court of Appeal.
5.  **Refiner/Critic Agent (Grounding):** Critically checks the draft answer against the retrieved source documents to ensure every claim is legally grounded and cited correctly.

### 🛡️ Core System Mandates (Prompt & Safety)

The entire system is governed by a strict system prompt to ensure responsible legal information delivery:

  * **1. Citing Mandate:** Every legal statement *must* be followed by an explicit citation (e.g., *Companies Act, Section 18* or *[1998] 1 SLR 250*).
  * **2. Anti-Hallucination:** If the retrieved documents do not contain the answer, the agent *must* state that the information is unavailable, rather than guessing.
  * **3. Professional Disclaimer:** Every substantive response concludes with a mandatory disclaimer:

> **DISCLAIMER:** *This is not professional legal advice. This information is for research and informational purposes only. Consult a qualified Sri Lankan legal professional for advice regarding your specific circumstances.*

### 🚀 Getting Started (Vibe Coding Guide)

#### 1\. Data Ingestion & Preprocessing

  * **Source Data:** Identify and download core Sri Lankan legal texts (e.g., The Constitution, key Acts like the Companies Act, Penal Code, etc.).
  * **Structural Chunking:** Implement a custom chunking strategy that splits documents by legal structure (Sections, Sub-sections, Articles) rather than arbitrary paragraph length to preserve legal context.
  * **Bilingual Challenge:** Determine the scope (English only, or include Sinhala/Tamil). If multilingual, select a cross-lingual embedding model.

#### 2\. Agent Framework Setup

```bash
# Example setup for a Python environment
pip install langchain langchain-openai chromadb python-dotenv
```

  * Define the roles and capabilities of your five agents (Router, Planner, Statutory, Case Law, Refiner).
  * Map the retrieval tools (VectorDB lookups) as callable functions for the agents.

#### 3\. Orchestrator Implementation

  * Implement the main loop that receives a query, hands it to the Router, manages the Planner and specialized agents, and finally passes the result to the Refiner before presenting the output.

### 🎯 Future Enhancements

  * **Real-time Gazette Monitoring:** Automated pipeline to ingest new legislation and amendments from the Government Gazette immediately.
  * **Hierarchical Indexing:** Index the legal corpus using a hierarchical structure (Act -\> Part -\> Chapter -\> Section) to enable multi-level retrieval.
  * **Local LLM Integration:** Optimize the system to use smaller, high-performing local LLMs for cost-efficiency.