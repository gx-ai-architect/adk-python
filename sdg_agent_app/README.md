# SDG Hub Multi-Agent System

A multi-agent system for creating synthetic training data using SDG Hub and InstructLab.

## 7-State System Overview

The system uses intelligent routing across 7 states:

| State | Name | Description |
|-------|------|-------------|
| **0** | **Greeting & Intent Detection** | **Welcome & Routing Hub** - Provides a cheerful, professional greeting to users accessing the SDG Hub Assistant. Analyzes user messages to determine intent and routes to appropriate workflows: Q&A, knowledge data generation, or skills data generation. Introduces the project as developed by Red Hat AI Innovation Team, provides system overview with scoping capabilities, and includes essential links to [SDG Hub](https://github.com/Red-Hat-AI-Innovation-Team/sdg_hub/tree/main). Sets user expectations and guides initial navigation. |
| **1** | **General Q&A** | **Knowledge & Consultation Hub** - Handles comprehensive questions about SDG Hub and InstructLab technologies. Leverages built-in knowledge base for general inquiries and utilizes MCP RAG tool for specific code-related queries against relevant GitHub repositories. Provides intelligent recommendations tailored to user use cases, suggesting appropriate data generation workflows (knowledge or skills) to improve their intended applications. Acts as a consultation service to guide users toward optimal solutions. |
| **2** | **Knowledge Flow** | **Document-Based Data Generation** - Orchestrates the complete knowledge synthetic data generation pipeline. **Process Flow**: 1) Document ingestion using Docling for PDF/document processing, 2) Interactive creation of `seed_data.jsonl` containing high-quality question-answer examples based on provided documents, 3) Automated synthetic data generation using ingested documents and seed data. **Status**: Currently under development - this comprehensive flow is not yet implemented but represents the target knowledge data generation workflow. |
| **3** | **Skills Greeting** | **Skills Flow Initialization** - Serves as the entry point for skills-based synthetic data generation. Explains the skills workflow methodology, assesses user's specific use case and current readiness level. Provides comprehensive guidance on seed data creation requirements for skills training. **User Routing**: Determines next steps based on user state - directs to Seed Data Creation (State 4) for new users, or directly to Data Generation (State 5) for users with existing seed data. Ensures proper workflow preparation. |
| **4** | **Seed Data Creator** | **Interactive Data Structuring** - Facilitates creation of structured seed data files in JSONL format for both skills and knowledge domains. Provides step-by-step guidance through the seed data creation process with real-time validation. Ensures data structure compliance with InstructLab standards and best practices. Features interactive prompting, format validation, and quality checks to produce high-quality seed data that serves as the foundation for synthetic data generation. |
| **5** | **Data Generator** | **Synthetic Data Production** - Executes synthetic training data generation using provided seed data through MCP tool integration. **Process Management**: Initiates generation, monitors progress, and reports success/failure status with detailed feedback. Upon successful completion, provides file location and access information. **Quality Control**: Enables user review of generated data with option to return to Seed Data Creator (State 4) for refinement if results don't meet expectations. Handles error recovery and iteration workflows. |
| **6** | **Review & Exit** | **Session Completion & Transition** - Provides comprehensive summary of accomplished tasks with congratulatory messaging. Reviews all generated outputs, file locations, and achieved objectives. **User Continuation**: Inquires about additional questions or tasks - routes back to Greeting (State 0) for new workflows or gracefully terminates the session. Ensures proper session cleanup and provides clear next steps or conclusion messaging. Acts as the natural endpoint with optional continuation capability. |

## Quick Start

```bash
# install adk in previous dir
cd ..
pip install -e .
cd sdg_agent_app
pip install -e requirements.txt
adk web
```

Then open your browser to the URL shown (typically http://localhost:8000).

## Environment Setup

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your_openai_api_key
```


2. Setup the SDG Hub MCP server:
https://github.com/Red-Hat-AI-Innovation-Team/sdg-mcp-server

That's it! The system will guide you through creating training data with natural language interaction.


3. Update the Hardcoded Root Dir / Target Dir in agents
