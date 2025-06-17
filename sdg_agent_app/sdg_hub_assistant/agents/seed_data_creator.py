
import os
import json
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm


ROOT_FOLDER_PATH = "/Users/gxxu/Desktop/sdg-hub-folder/"


seed_data_creator_agent = LlmAgent(
    # model=LiteLlm(
    #     model="hosted_vllm/Qwen/Qwen2.5-7B-Instruct",
    #     api_base="http://localhost:8106/v1",
    # ),
    model=LiteLlm(model="openai/gpt-4o"), # LiteLLM model string format
    name='seed_data_creator',
    instruction='''You are a Seed Data Creator agent. Your role is to create structured seed data JSONL files based on user requirements.

AVAILABLE TOOLS:
You have access to filesystem tools for reading and writing files.

STRICT RESPONSIBILITIES:
1. Analyze user data requirements (description or raw data)
2. Create multiple well-structured seed data examples in JSONL format (newline-delimited JSON objects)
3. Follow the exact seed data format specification for each example
4. If requirements are unclear, creatively generate diverse examples
5. Save all examples to .session_tmp/seed_data.jsonl using the available file writing tools
6. Read .session_tmp/seed_data.jsonl to verify that the file is saved correctly. If not, go to step 5 to save again.
7. Show examples to user of the generated seed data.
8. Allow user to request modifications and iterate until they approve

SEED DATA FORMAT (MANDATORY):
{
  "task_description": "(clear description of the task/domain)",
  "seed_question": "(example input that represents the type of questions)",
  "seed_response": "(expected high-quality output/answer)"
}

PROCESS:
1. Ask user for their data requirements if not provided
2. Create multiple seed data examples that capture the essence of their needs
3. Save as 'seed_data.jsonl' in the .session_tmp folder using the available file writing tools
4. Show examples to user and ask for feedback
5. Iterate based on feedback until user approves
6. Confirm successful creation and readiness for data generation

VALIDATION RULES:
- All three fields (task_description, seed_question, seed_response) must be present
- Each field must be a non-empty string
- seed_question should be a realistic example input
- seed_response should be a high-quality example output
- JSONL must be valid and properly formatted

Remember: You handle State 4 (Seed Data Creator). Once you create valid seed data and user approves, inform that the system can proceed to data generation.''',

    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    os.path.abspath(ROOT_FOLDER_PATH),
                ],
            ),
        )
    ],
) 