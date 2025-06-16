# Multi-Agent Synthetic Data Generation System

## Overview

This is a Google ADK-based multi-agent system for synthetic data generation that follows a strict 4-state workflow. The system coordinates between specialized agents to create high-quality seed data and generate synthetic training data using the SDG hub.

## System Architecture

### State Flow (STRICT)
```
State-1: Seed Data Creation → State-2: Seed Data Iteration → State-3: Data Generation → State-4: Close/Restart → State-1 (loop)
```

**Key Rules:**
- ✅ Always maintain current state
- ✅ Never skip states  
- ✅ State transitions only on explicit completion
- ✅ Each state has specific completion criteria

## Agents

### 1. Seed Data Creator Agent (State-1)
- **Purpose**: Create structured seed data JSON files from user requirements
- **Input**: User data requirements (description or raw data)
- **Output**: Valid `seed_data.json` file
- **Tools**: File management MCP
- **Completion**: Valid seed file created → Transition to State-2

**Seed Data Format:**
```json
{
  "task_description": "Clear description of the task/domain",
  "seed_question": "Example input question",
  "seed_response": "Expected high-quality output"
}
```

### 2. Seed Data Iterator Agent (State-2)
- **Purpose**: Refine seed data based on user feedback
- **Input**: Existing seed data file
- **Output**: Refined seed data file
- **Process**: Review → User feedback → Iterate → Approval
- **Tools**: File management MCP
- **Completion**: User approval OR max iterations (3) → Transition to State-3

### 3. Data Generator Agent (State-3)
- **Purpose**: Generate synthetic training data using SDG hub
- **Input**: Approved seed data + generation parameters
- **Output**: Generated synthetic data files
- **Tools**: File management MCP + SDG generation MCP
- **Parameters**: 
  - `output_count`: Number of examples (1-1000)
  - `variation_level`: Low/Medium/High
  - `output_format`: JSON/CSV/TXT
- **Completion**: Data generated → Transition to State-4

### 4. State Controller
- **Purpose**: Manage state transitions and system flow
- **Features**:
  - Persistent state tracking
  - Validation of completion criteria
  - Error handling with state rollback
  - Session management across agents

## Usage

### Quick Start

1. **Run Interactive Session:**
```bash
cd adk-python/skills_agent
python multi_agent_main.py
# Choose option 1 for interactive session
```

2. **Run Demo Session:**
```bash
python multi_agent_main.py
# Choose option 2 for demo session
```

### Step-by-Step Example

#### State-1: Seed Data Creation
```
👤 User: "I need training data for a customer service chatbot that handles order inquiries"

🤖 Seed Creator: Creates seed_data.json with:
{
  "task_description": "Customer service chatbot for order inquiries",
  "seed_question": "Hi, I'd like to check the status of my order #12345",
  "seed_response": "I'll help you check your order status. Order #12345 was shipped on..."
}
```

#### State-2: Seed Data Iteration
```
👤 User: "Can you make the question more specific about delivery tracking?"

🤖 Iterator: Updates seed data based on feedback
👤 User: "Yes, I approve this seed data"
```

#### State-3: Data Generation
```
👤 User: "Generate 10 examples with medium variation in JSON format"

🤖 Generator: Creates synthetic training data using SDG hub
- Generates 10 variations of the seed example
- Saves as generated_data_YYYYMMDD_HHMMSS.json
```

#### State-4: Close/Restart
```
👤 User: "restart" → Returns to State-1
👤 User: "close" → Ends session
```

## Commands

### System Commands
- `status` - Show current state and system information
- `help` - Display help information
- `exit`/`quit` - End the session

### State-Specific Commands
- **State-1**: Describe your data requirements
- **State-2**: Provide feedback or type "approve"/"yes"
- **State-3**: Specify generation parameters
- **State-4**: Type "restart" or "close"

## File Structure

```
mcp_agents/
├── __init__.py                  # Module exports
├── agent.py                     # Original single agent (legacy)
├── state_manager.py             # State management system
├── seed_data_creator.py         # State-1 agent
├── seed_data_iterator.py        # State-2 agent  
├── data_generator.py            # State-3 agent
├── multi_agent_controller.py    # Main controller
└── multi_agent_main.py          # Example usage
```

## Generated Files

The system creates several files during operation:

- `seed_data.json` - Structured seed data
- `system_state.json` - Persistent state information
- `generated_data_YYYYMMDD_HHMMSS.json` - Timestamped output
- `generated_data_latest.json` - Latest generation result

## State Validation

Each state validates completion before transition:

### State-1 Validation
- ✅ `seed_data.json` exists
- ✅ Contains required fields: `task_description`, `seed_question`, `seed_response`
- ✅ All fields are non-empty strings
- ✅ Valid JSON format

### State-2 Validation  
- ✅ User explicit approval ("yes", "approve", etc.)
- ✅ OR maximum iterations (3) reached

### State-3 Validation
- ✅ Synthetic data generation completed
- ✅ Output files created successfully
- ✅ Generation parameters within valid ranges

## Error Handling

- **State Rollback**: Return to previous state on failure
- **Session Recovery**: Resume from last valid state
- **Graceful Degradation**: Continue with best available data
- **Validation Errors**: Clear error messages with guidance

## Configuration

### Model Configuration
All agents use the same LLM configuration:
```python
model = LiteLlm(
    model="hosted_vllm/qwen-7b-instruct-knowledge-v0.5",
    api_base="http://localhost:8108/v1",
)
```

### Path Configuration
- `TARGET_FOLDER_PATH`: SDG MCP server location
- `ROOT_FOLDER_PATH`: Workspace root for file operations

## Integration with Google ADK

The system leverages Google ADK features:

- **LlmAgent**: Core agent framework
- **MCPToolset**: Tool integration via MCP protocol
- **InMemoryRunner**: Session and execution management
- **Session Management**: Multi-agent session coordination

## Best Practices

1. **Always check system status** with `status` command
2. **Provide clear requirements** in State-1
3. **Give specific feedback** in State-2
4. **Validate generated data** in State-3
5. **Use restart** for new generation cycles

## Troubleshooting

### Common Issues

1. **Agent not responding**: Check if LLM server is running
2. **File not found**: Verify path configurations
3. **State stuck**: Use `status` to check completion criteria
4. **Generation failed**: Check SDG MCP server status

### Debug Commands
```bash
# Check system state
python -c "from mcp_agents import StateManager; print(StateManager().get_current_state())"

# Validate seed data
python -c "import json; print(json.load(open('seed_data.json')))"
```

## Extensions

The system is designed for extensibility:

- **Custom Agents**: Add new specialized agents
- **Additional States**: Extend the state machine
- **Tool Integration**: Add new MCP toolsets
- **Output Formats**: Support additional data formats

## License

Copyright 2025 Google LLC - Licensed under Apache License 2.0 