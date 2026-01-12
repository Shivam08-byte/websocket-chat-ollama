# Agent1 - Learning AI Agents

## 🎯 Overview

Agent1 is a simple **ReAct (Reasoning + Acting) Agent** designed to help you understand how AI agents work. It demonstrates core concepts that are essential for agent-based systems and frequently asked in interviews.

## 🚀 Access

- **UI**: http://localhost:8081/agents/agent1
- **API Info**: GET http://localhost:8081/api/agents/agent1/info
- **Query**: POST http://localhost:8081/api/agents/agent1/query

## 📚 What You'll Learn

### 1. **ReAct Pattern** (Reasoning + Acting)
The agent follows a thought-action-observation loop:
- **THOUGHT**: Agent reasons about what to do
- **ACTION**: Agent selects and calls a tool
- **OBSERVATION**: Agent receives tool result
- **Repeat**: Until final answer is reached

### 2. **Function Calling / Tool Use**
Agent can invoke external functions with parameters:
```python
ACTION: calculator
ACTION_INPUT: {"expression": "25 * 8"}
```

### 3. **Planning**
Agent breaks down complex queries into steps:
- Identifies what information is needed
- Decides which tool to use
- Chains multiple tool calls if needed

### 4. **Conversation Memory**
Agent maintains conversation history to provide context-aware responses.

### 5. **Tool Selection**
Agent chooses the right tool based on the query and available capabilities.

## 🛠️ Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| **calculator** | Evaluates math expressions | `25 * 8`, `sqrt(144)` |
| **get_current_time** | Returns current date/time | No parameters |
| **get_weather** | Mock weather data | `"Mumbai"`, `"London"` |
| **search_knowledge** | Searches knowledge base | `"Python"`, `"agents"` |

## 💡 Example Queries

1. **Simple Calculation**:
   ```
   What is 25 * 8 + 17?
   ```

2. **Time Query**:
   ```
   What time is it?
   ```

3. **Weather Check**:
   ```
   What's the weather in Mumbai?
   ```

4. **Knowledge Search**:
   ```
   Tell me about Python
   ```

5. **Multi-step Query**:
   ```
   Calculate sqrt(144) and tell me what time it is
   ```

## 🏗️ Architecture

### Agent Flow
```
User Query
    ↓
Agent Reasoning (LLM)
    ↓
Tool Selection & Execution
    ↓
Result Processing
    ↓
Final Answer
```

### Code Structure

```
app_agents/
├── __init__.py
├── app.py              # FastAPI routes
├── agent1.py           # ReAct agent implementation
└── tools.py            # Tool definitions & execution
```

### Key Components

#### 1. ToolRegistry (`tools.py`)
- Defines available tools with schemas
- Executes tool calls
- Returns structured results

#### 2. Agent1 Class (`agent1.py`)
- Implements ReAct loop
- Manages conversation history
- Parses LLM responses for tool calls
- Handles iterations (max 5)

#### 3. API Routes (`app.py`)
- `/api/agents/agent1/info` - Agent metadata
- `/api/agents/agent1/tools` - List tools
- `/api/agents/agent1/query` - Send query
- `/api/agents/agent1/reset` - Clear history

## 🎓 Interview Topics Covered

### Conceptual
1. **What is an AI agent?**
   - Autonomous system that perceives, reasons, and acts
   - Uses tools to interact with environment
   - Makes decisions to achieve goals

2. **What is the ReAct pattern?**
   - Reasoning + Acting approach
   - Agent explains thinking before taking action
   - Improves interpretability and debugging

3. **How does function calling work?**
   - LLM outputs structured format
   - Parser extracts tool name and parameters
   - Tool executor runs function and returns result
   - Result fed back to LLM for next step

4. **What are tool schemas?**
   - Formal descriptions of tool capabilities
   - Include name, description, parameters
   - Help LLM understand when/how to use tools

5. **How to prevent infinite loops?**
   - Set max iteration limit
   - Detect when agent is stuck
   - Force final answer after threshold

### Technical
1. **Parsing LLM outputs for tool calls**
   - Use structured formats (THOUGHT/ACTION/ACTION_INPUT)
   - Regex or string parsing
   - JSON extraction from text

2. **Error handling**
   - Tool execution failures
   - Invalid parameters
   - Timeout management

3. **State management**
   - Conversation history
   - Tool call tracking
   - Context window management

4. **Prompt engineering**
   - System prompt with tool descriptions
   - Few-shot examples
   - Output format specification

## 🔄 Workflow Example

**User**: "What is 25 * 8?"

**Agent Iteration 1**:
```
THOUGHT: I need to calculate 25 * 8, I'll use the calculator tool.
ACTION: calculator
ACTION_INPUT: {"expression": "25 * 8"}
```

**Tool Result**:
```json
{
  "result": 200,
  "expression": "25 * 8",
  "message": "The result of 25 * 8 is 200"
}
```

**Agent Iteration 2**:
```
THOUGHT: The calculator returned 200. This is the answer.
FINAL_ANSWER: 25 * 8 equals 200.
```

## 🚦 Testing via UI

1. Open http://localhost:8081/agents/agent1
2. Try the example queries in the sidebar
3. Watch the reasoning steps displayed
4. See which tools were used

## 🚦 Testing via API

```bash
# Get agent info
curl http://localhost:8081/api/agents/agent1/info

# Send a query
curl -X POST http://localhost:8081/api/agents/agent1/query \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is 25 * 8?"}'

# Reset conversation
curl -X POST http://localhost:8081/api/agents/agent1/reset
```

## 🎯 Key Takeaways

1. **Agents = LLM + Tools + Loop**
2. **ReAct = Interpretable decision making**
3. **Function calling enables external capabilities**
4. **Proper prompting is critical**
5. **Error handling and limits prevent issues**

## 🔮 Next Steps

After understanding Agent1, you can explore:

1. **Multi-agent systems** - Multiple agents working together
2. **Advanced planning** - Tree of thoughts, self-reflection
3. **Memory systems** - Vector stores, episodic memory
4. **Real tools** - APIs, databases, file systems
5. **Streaming responses** - Real-time tool execution
6. **Self-correction** - Agent validates and fixes mistakes

## 📖 Further Reading

- **ReAct Paper**: "ReAct: Synergizing Reasoning and Acting in Language Models"
- **Tool Use**: OpenAI Function Calling, LangChain Agents
- **Planning**: Chain of Thought, Tree of Thoughts
- **Frameworks**: LangChain, LlamaIndex, AutoGPT

## 🐛 Troubleshooting

**Agent doesn't use tools**:
- Model might be too small (gemma:2b)
- Try better prompt engineering
- Use more capable model (llama3, mistral)

**Infinite loops**:
- Check max_iterations setting
- Review system prompt clarity
- Add more explicit examples

**Tool execution errors**:
- Validate tool input schemas
- Add better error messages
- Implement fallback logic

---

**Remember**: This is a learning agent. Production agents need:
- Better error handling
- Rate limiting
- Security validation
- Logging and monitoring
- Cost tracking
