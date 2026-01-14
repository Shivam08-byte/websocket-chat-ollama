# 🤖 Agent1 - Quick Reference Card

## 🎯 What is Agent1?

A **ReAct (Reasoning + Acting) agent** that demonstrates:
- ✅ Function calling / Tool use
- ✅ Reasoning and planning
- ✅ Conversation memory
- ✅ Multi-step task execution

Perfect for learning AI agents and interview preparation!

---

## 🚀 Quick Access

| Resource | URL |
|----------|-----|
| **Interactive UI** | http://localhost:8081/agents/agent1 |
| **Agent Info** | GET /api/agents/agent1/info |
| **List Tools** | GET /api/agents/agent1/tools |
| **Send Query** | POST /api/agents/agent1/query |
| **Reset History** | POST /api/agents/agent1/reset |
| **Documentation** | [AGENT1_GUIDE.md](../guides/AGENT1_GUIDE.md) |

---

## 🛠️ Available Tools

| Tool | What it does | Example Query |
|------|--------------|---------------|
| 🧮 **calculator** | Math operations | "What is 25 * 8 + 17?" |
| ⏰ **get_current_time** | Current date/time | "What time is it?" |
| 🌤️ **get_weather** | Weather info (mock) | "Weather in Mumbai?" |
| 📚 **search_knowledge** | Knowledge base | "Tell me about Python" |

---

## 💬 Example Queries

### Simple
```bash
curl -X POST http://localhost:8081/api/agents/agent1/query \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is 144 / 12?"}'
```

### Time Check
```bash
curl -X POST http://localhost:8081/api/agents/agent1/query \
  -H 'Content-Type: application/json' \
  -d '{"message":"What time is it?"}'
```

### Weather (Mock)
```bash
curl -X POST http://localhost:8081/api/agents/agent1/query \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is the weather in London?"}'
```

### Multi-step
```bash
curl -X POST http://localhost:8081/api/agents/agent1/query \
  -H 'Content-Type: application/json' \
  -d '{"message":"Calculate sqrt(144) and tell me the time"}'
```

---

## 🎓 Interview Topics Covered

### Conceptual
- ✅ What is an AI agent?
- ✅ What is the ReAct pattern?
- ✅ How does function calling work?
- ✅ What are tool schemas?
- ✅ How to prevent infinite loops?

### Technical
- ✅ Parsing LLM outputs for tool calls
- ✅ Error handling in agents
- ✅ State management (conversation history)
- ✅ Prompt engineering for agents
- ✅ Iteration control and limits

---

## 🔄 How Agent1 Works

```
1. User sends query
         ↓
2. Agent receives query → Builds prompt with system message + history
         ↓
3. Ollama LLM generates response → THOUGHT + ACTION + ACTION_INPUT
         ↓
4. Agent parses response → Identifies tool to call
         ↓
5. ToolRegistry executes tool → Returns result
         ↓
6. Agent adds result to history → Next iteration
         ↓
7. Agent sees tool result → Generates FINAL_ANSWER
         ↓
8. Returns answer + reasoning steps + tools used
```

---

## 📊 Response Format

```json
{
  "success": true,
  "answer": "25 * 8 equals 200.",
  "steps": [
    {
      "type": "tool_call",
      "thought": "I need to calculate 25 * 8",
      "tool": "calculator",
      "input": {"expression": "25 * 8"},
      "result": "{\"result\": 200, \"message\": \"...\"}"
    },
    {
      "type": "final",
      "content": "FINAL_ANSWER: 25 * 8 equals 200."
    }
  ],
  "tools_used": ["calculator"],
  "iterations": 2
}
```

---

## 🏗️ Code Structure

```
app_agents/
├── __init__.py
├── app.py          # FastAPI routes (4 endpoints)
├── agent1.py       # ReAct agent logic (210 lines)
│   ├── Agent1 class
│   ├── run() method (main loop)
│   ├── get_system_prompt()
│   └── _build_prompt()
└── tools.py        # Tool registry (220 lines)
    ├── ToolRegistry class
    ├── get_tools() - Returns schemas
    └── execute_tool() - Runs functions
```

---

## 🎯 Key Features

| Feature | Implementation | Line Count |
|---------|----------------|------------|
| **ReAct Loop** | agent1.py:run() | ~100 lines |
| **Tool Registry** | tools.py | 220 lines |
| **4 Tools** | calculator, time, weather, search | 150 lines |
| **API Routes** | app.py | 90 lines |
| **Frontend UI** | agent1.html | 400 lines |
| **Documentation** | AGENT1_GUIDE.md | 300+ lines |

**Total**: ~1,260 lines of code

---

## 🧪 Testing Checklist

- [ ] Open UI: http://localhost:8081/agents/agent1
- [ ] Test calculator: "What is 25 * 8?"
- [ ] Test time: "What time is it?"
- [ ] Test weather: "Weather in Mumbai?"
- [ ] Test knowledge: "Tell me about Python"
- [ ] Test multi-step: "Calculate sqrt(144) and check weather"
- [ ] Check reasoning steps displayed
- [ ] Verify tools used badge
- [ ] Test reset button
- [ ] Try example queries from sidebar

---

## 🎨 UI Features

- ✅ Beautiful gradient theme (purple/blue)
- ✅ Tool sidebar with descriptions
- ✅ Real-time reasoning steps display
- ✅ Tools used tracking
- ✅ Example queries (click to use)
- ✅ Conversation reset button
- ✅ Loading indicators
- ✅ Responsive design

---

## 🚦 Troubleshooting

### Agent doesn't use tools
**Cause**: Model too small (gemma:2b)  
**Fix**: Use better model like llama3 or improve prompts

### Shows reasoning but doesn't execute
**Cause**: Response format not parsed correctly  
**Check**: agent1.py line ~80 (parsing logic)

### Tools return errors
**Cause**: Invalid parameters or execution failure  
**Check**: tools.py execute_tool() method

---

## 📈 Next Steps

1. **Learn the code**:
   - Read agent1.py (ReAct implementation)
   - Study tools.py (tool execution)
   - Understand app.py (API routes)

2. **Extend functionality**:
   - Add more tools (file operations, API calls)
   - Implement streaming responses
   - Add self-correction logic

3. **Interview prep**:
   - Explain ReAct pattern
   - Walk through tool calling flow
   - Discuss error handling
   - Design multi-agent system

4. **Production ready**:
   - Use better LLM (GPT-4, Claude)
   - Add authentication
   - Implement rate limiting
   - Add monitoring/logging

---

## 📚 Learning Resources

- **Full Guide**: [AGENT1_GUIDE.md](../guides/AGENT1_GUIDE.md)
- **Implementation**: [AGENT_IMPLEMENTATION.md](../design/AGENT_IMPLEMENTATION.md)
- **Architecture**: [MODULAR_ARCHITECTURE.md](../architecture/MODULAR_ARCHITECTURE.md)
- **Main README**: [README.md](../../README.md)

---

## 💡 Pro Tips

1. **UI is your friend** - Use visual interface to understand flow
2. **Check reasoning steps** - See how agent thinks
3. **Read the prompts** - System prompt teaches the agent
4. **Experiment freely** - Try different queries
5. **Reset when stuck** - Clear history and start fresh

---

## 🎉 You Now Have

✅ Working AI agent with function calling  
✅ 4 different tool types  
✅ Beautiful interactive UI  
✅ Complete documentation  
✅ Interview-ready knowledge  
✅ Foundation for advanced agents  

**Start experimenting**: http://localhost:8081/agents/agent1

---

*Agent1 v1.0 - Built for Learning 🚀*
