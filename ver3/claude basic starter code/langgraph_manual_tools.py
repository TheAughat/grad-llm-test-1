import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    call_id: str

@dataclass
class AgentState:
    messages: List[BaseMessage]
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[Dict]] = None

class ManualToolBinding:
    """
    Custom tool binding implementation for LangGraph
    Mimics automatic tool binding but gives you full control
    """
    
    def __init__(self, claude_client):
        self.claude = claude_client
        self.tools = {}
        
    def register_tool(self, name: str, func: callable, description: str, parameters: Dict):
        """Register a tool with its function and schema"""
        self.tools[name] = {
            'function': func,
            'description': description,
            'parameters': parameters
        }
    
    def get_tool_descriptions(self) -> str:
        """Generate tool descriptions for the system prompt"""
        if not self.tools:
            return ""
            
        tool_desc = "You have access to the following tools:\n\n"
        for name, tool in self.tools.items():
            tool_desc += f"Tool: {name}\n"
            tool_desc += f"Description: {tool['description']}\n"
            tool_desc += f"Parameters: {json.dumps(tool['parameters'], indent=2)}\n\n"
        
        tool_desc += """To use a tool, respond with:
<tool_call>
<name>tool_name</name>
<arguments>{"param1": "value1", "param2": "value2"}</arguments>
</tool_call>

You can make multiple tool calls in one response if needed."""
        
        return tool_desc
    
    def parse_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse tool calls from Claude's response"""
        tool_calls = []
        pattern = r'<tool_call>\s*<name>(.*?)</name>\s*<arguments>(.*?)</arguments>\s*</tool_call>'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for i, (name, args_str) in enumerate(matches):
            try:
                arguments = json.loads(args_str.strip())
                tool_calls.append(ToolCall(
                    name=name.strip(),
                    arguments=arguments,
                    call_id=f"call_{i}"
                ))
            except json.JSONDecodeError:
                print(f"Error parsing arguments for tool {name}: {args_str}")
                
        return tool_calls
    
    def execute_tools(self, tool_calls: List[ToolCall]) -> List[Dict]:
        """Execute the tool calls and return results"""
        results = []
        for call in tool_calls:
            if call.name in self.tools:
                try:
                    result = self.tools[call.name]['function'](**call.arguments)
                    results.append({
                        'call_id': call.call_id,
                        'name': call.name,
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'call_id': call.call_id,
                        'name': call.name,
                        'error': str(e)
                    })
            else:
                results.append({
                    'call_id': call.call_id,
                    'name': call.name,
                    'error': f"Tool {call.name} not found"
                })
        return results
    
    def agent_node(self, state: AgentState) -> AgentState:
        """Main agent node that calls Claude"""
        messages = state.messages
        
        # Build system prompt with tool descriptions
        system_prompt = "You are a helpful assistant."
        tool_desc = self.get_tool_descriptions()
        if tool_desc:
            system_prompt += f"\n\n{tool_desc}"
        
        # Convert messages to Claude format
        claude_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                claude_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                claude_messages.append({"role": "assistant", "content": msg.content})
        
        # Get response from Claude
        response = self.claude.multiturn_conversation(
            messages=claude_messages,
            system_prompt=system_prompt
        )
        
        # Parse tool calls
        tool_calls = self.parse_tool_calls(response)
        
        # Add AI message
        new_messages = messages + [AIMessage(content=response)]
        
        return AgentState(
            messages=new_messages,
            tool_calls=tool_calls if tool_calls else None
        )
    
    def tool_node(self, state: AgentState) -> AgentState:
        """Tool execution node"""
        if not state.tool_calls:
            return state
            
        # Execute tools
        results = self.execute_tools(state.tool_calls)
        
        # Format results for the next message
        results_text = "Tool execution results:\n"
        for result in results:
            results_text += f"\nTool: {result['name']}\n"
            if 'error' in result:
                results_text += f"Error: {result['error']}\n"
            else:
                results_text += f"Result: {result['result']}\n"
        
        # Add tool results as a user message
        new_messages = state.messages + [HumanMessage(content=results_text)]
        
        return AgentState(
            messages=new_messages,
            tool_results=results,
            tool_calls=None
        )
    
    def should_continue(self, state: AgentState) -> str:
        """Determine if we should continue or end"""
        return "tools" if state.tool_calls else END
    
    def create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", self.tool_node)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {"tools": "tools", END: END}
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

# Example usage with a simple calculator tool
def calculator(operation: str, a: float, b: float) -> float:
    """Simple calculator function"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else "Error: Division by zero"
    else:
        return "Error: Unknown operation"

if __name__ == "__main__":
    from claude_basic_setup import ClaudeClient
    
    claude = ClaudeClient()
    tool_binding = ManualToolBinding(claude)
    
    # Register the calculator tool
    tool_binding.register_tool(
        name="calculator",
        func=calculator,
        description="Perform basic arithmetic operations",
        parameters={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    )
    
    # Create and run the graph
    graph = tool_binding.create_graph()
    
    initial_state = AgentState(
        messages=[HumanMessage(content="What is 15 multiplied by 7?")]
    )
    
    final_state = graph.invoke(initial_state)
    print("Final response:", final_state.messages[-1].content)