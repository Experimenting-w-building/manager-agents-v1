import os
from typing import List, Dict, Set

# Core LangChain and LangGraph imports
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from langgraph.graph import END, StateGraph
from langchain_deepseek import ChatDeepSeek

# Local Imports
from agents import ElizaOSAgent, TronAgent, GooseAgent
from models import AgentRequirements, AgentTask, AgentType, ManagerState, TaskStatus

# For development/testing: Simulate API responses
def simulate_api_response(agent_type: AgentType, query: str) -> dict:
    """Simulate API responses for testing without real endpoints"""
    responses = {
        AgentType.ELIZAOS: f"ElizaOS analysis: Based on the query '{query}', I recommend using the ElizaOS filesystem API with pattern matching to solve this efficiently.",
        AgentType.TRON: f"Tron framework response: For '{query}', you should implement a grid-based approach using Tron's lightweight memory management features.",
        AgentType.GOOSE: f"Goose framework solution: '{query}' can be addressed with Goose's distributed processing model using the following pattern..."
    }
    return {"success": True, "result": responses[agent_type]}

# Manager Agent Implementation
class FrameworkManagerAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.framework_agents = {
            AgentType.ELIZAOS: ElizaOSAgent(),
            AgentType.TRON: TronAgent(),
            AgentType.GOOSE: GooseAgent()
        }
        
        # Prompt for determining which agents are needed
        self.agent_selector_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in framework selection. Your job is to determine which specialized 
            framework agents need to be consulted to answer a query comprehensively.
            
            Available framework agents:
            - elizaos: Specializes in the ElizaOS framework, which excels at AI-driven operating systems, file system operations, and pattern matching
            - tron: Specializes in the Tron framework, which focuses on grid-based algorithms, lightweight memory management, and real-time processing
            - goose: Specializes in the Goose framework, which is known for distributed processing, fault tolerance, and scalable solutions
            
            For each agent, determine if it's needed to fully answer the query. Consider the query carefully - some queries might require multiple frameworks, while others might only need one specific framework.
            
            For each framework, provide:
            - Whether it's needed (true/false)
            - A clear reason explaining why it is or isn't needed"""),
            ("human", "Query: {query}")
        ])
        
        # Prompt for aggregating responses
        self.response_aggregator_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at synthesizing information from multiple specialized framework agents.
            Your job is to create a comprehensive, cohesive response that addresses the original query by combining
            insights from different frameworks.
            
            When combining responses:
            1. Identify common themes and differences between framework approaches
            2. Highlight the strengths of each framework for the specific parts of the solution
            3. Provide a unified recommendation that incorporates the best elements from each framework
            4. Ensure there are no contradictions in the final response
            5. Use a clear structure that flows naturally between different framework insights"""),
            ("human", """Original query: {query}
            
            Framework agent responses:
            {agent_responses}
            
            Please create a comprehensive response that addresses the original query by synthesizing these insights. Do not talk about the context provided, 
            but instead just use it to answer the question naturally.
            """)
        ])
    
    def determine_required_agents(self, query: str) -> Set[AgentType]:
        """Determine which agents are needed to answer the query"""
        # Create base JSON parser
        base_parser = JsonOutputParser(pydantic_object=AgentRequirements)
        chat_llm = ChatDeepSeek(model="deepseek-chat")
        
        # Wrap with fixing parser that can handle invalid JSON
        parser = OutputFixingParser.from_llm(
            parser=base_parser,
            llm=chat_llm
        )
        
        chain = self.agent_selector_prompt | chat_llm | parser
        
        try:
            result = chain.invoke({"query": query})
            # Access agents using dictionary notation
            agents_list = result['agents']
            # Extract the required agents using dictionary notation
            required_agents = {agent['agent_type'] for agent in agents_list if agent['needed']}
            return required_agents
        except Exception as e:
            # Fallback if parsing still fails
            print(f"Warning: Failed to parse agent requirements: {e}")
            # Return all agents as a fallback
            return set(AgentType)
    
    def process_with_agent(self, agent_type: AgentType, query: str) -> dict:
        """Process the query with the specified agent"""
        # For real implementation, use actual API calls
        return self.framework_agents[agent_type].process(query)
        
        # For testing/development, use simulated responses
        # return simulate_api_response(agent_type, query)
    
    def aggregate_responses(self, query: str, completed_tasks: List[AgentTask]) -> str:
        """Combine responses from all agents into a cohesive answer"""
        # Format the agent responses for the prompt
        agent_responses = "\n\n".join([
            f"{task.agent_type.upper()} AGENT:\n{task.response}"
            for task in completed_tasks
            if task.status == TaskStatus.COMPLETED
        ])
        
        chain = self.response_aggregator_prompt | self.llm
        result = chain.invoke({
            "query": query,
            "agent_responses": agent_responses
        })
        
        return result.content

# LangGraph implementation
def create_framework_manager_graph(llm: BaseChatModel):
    # Create the manager agent
    manager = FrameworkManagerAgent(llm)
    
    # Define graph nodes
    def initialize(state: ManagerState) -> ManagerState:
        """Initialize the state by determining which agents are needed"""
        required_agents = manager.determine_required_agents(state["original_query"])
        
        # Create tasks for each required agent
        tasks = [
            AgentTask(
                agent_type=agent_type,
                query=state["original_query"]
            )
            for agent_type in required_agents
        ]
        
        new_state =  {
            **state,
            "tasks": tasks,
            "required_agents": required_agents,
            "current_agent": None
        }
        # print("[Initialize] State after initialization:", new_state)
        return new_state

    
    def select_next_agent(state: ManagerState) -> ManagerState:
        """Select the next agent to process the query"""
        for task in state["tasks"]:
            if task.status == TaskStatus.PENDING:
                new_state = {**state, "current_agent": task.agent_type}
                print(f"[Select Next Agent] Selected agent: {task.agent_type}")
                return new_state
        
        # If no pending tasks, set current_agent to None
        return {
            **state,
            "current_agent": None
        }
    
    def process_with_agent(state: ManagerState) -> ManagerState:
        """Process the query with the current agent"""
        if state["current_agent"] is None:
            return state
        
        # Find the current task
        current_task = next(task for task in state["tasks"] if task.agent_type == state["current_agent"])
        
        # Process with the appropriate agent
        result = manager.process_with_agent(current_task.agent_type, current_task.query)
        
        if result["success"]:
            current_task.response = result["result"]
            current_task.status = TaskStatus.COMPLETED
        else:
            current_task.error = result["error"]
            current_task.status = TaskStatus.FAILED
        
        # Update the tasks list
        updated_tasks = [
            task if task.agent_type != current_task.agent_type else current_task
            for task in state["tasks"]
        ]
        
        new_state = {
            **state,
            "tasks": updated_tasks
        }
        return new_state
    
    def should_continue(state: ManagerState) -> str:
        """Determine if there are more agents to process or if we're done"""
        if state["current_agent"] is None and all(task.status != TaskStatus.PENDING for task in state["tasks"]):
            print("[Should Continue] No pending tasks, finishing workflow.")
            return "finish"
        print("[Should Continue] There are still pending tasks, continuing workflow.")
        return "continue"
    
    def finalize(state: ManagerState) -> Dict:
        """Create the final output by aggregating responses"""
        completed_tasks = [task for task in state["tasks"] if task.status == TaskStatus.COMPLETED]
        print("[Finalize] Completed tasks:", [(t.agent_type, t.status) for t in completed_tasks])
        
        # Handle case where no agents provided successful responses
        if not completed_tasks:
            final_output = "Unable to provide a response as all specialized agents encountered errors."
        else:
            final_output = manager.aggregate_responses(state["original_query"], completed_tasks)
        
        message = [AIMessage(content=f"Query processed. Here's the answer:\n\n{final_output}")]
        result = {
            "final_output": final_output,
            "messages": message  # This will be properly combined with existing messages via operator.add
        }
        print("[Finalize] Final output:", final_output)
        return result
    
    # Build the graph
    workflow = StateGraph(ManagerState)
    
    # Add nodes
    workflow.add_node("initialize", initialize)
    workflow.add_node("select_next_agent", select_next_agent)
    workflow.add_node("process_with_agent", process_with_agent)
    workflow.add_node("finalize", finalize)
    
    # Add edges
    workflow.add_edge("initialize", "select_next_agent")
    # workflow.add_edge("select_next_agent", "process_with_agent")
    workflow.add_edge("process_with_agent", "select_next_agent")
    workflow.add_conditional_edges(
        "select_next_agent",
        should_continue,
        {
            "continue": "process_with_agent",
            "finish": "finalize"
        }
    )
    workflow.add_edge("finalize", END)
    
    # Set the entry point
    workflow.set_entry_point("initialize")
    
    # Compile the graph
    return workflow.compile()

# Example usage
def run_framework_manager(query: str, llm: BaseChatModel):
    graph = create_framework_manager_graph(llm)
    
    # Create initial state with all required fields
    initial_state = {
        "original_query": query,
        "messages": [HumanMessage(content=query)],
        "tasks": [],
        "required_agents": set(),
        "current_agent": None,
        "final_output": ""  # Use an empty string instead of None
    }
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    return result

async def query_manager_agent(query: str, deepseek_llm="deepseek-reasoner"):
    llm = ChatDeepSeek(model=deepseek_llm)
    return run_framework_manager(query, llm)

# # Example execution
# if __name__ == "__main__":    
#     llm = ChatDeepSeek(model="deepseek-reasoner")
    
#     # Sample queries to test with
#     queries = [
#         "write some code that works with elizaos and goose",  # Likely needs all three
#         "How can I create a fault-tolerant pattern matching system?",  # ElizaOS and Goose
#         "What's the best way to process grid-based data with memory constraints?",  # Primarily Tron
#     ]
    
#     # Process a sample query
#     query = input("Question: ")
#     print(f"Processing query: {query}")
    
#     result = run_framework_manager(query, llm)
    
#     print(f"\nFinal Response:\n{result['final_output']}")
    
#     # Print execution details for debugging
#     print("\nAgent Selection Summary:")
#     for agent_type in result["required_agents"]:
#         print(f"- {agent_type} was required")
    
#     print("\nTask Execution Summary:")
#     for task in result["tasks"]:
#         print(f"Agent: {task.agent_type}")
#         print(f"Status: {task.status}")
#         if task.error:
#             print(f"Error: {task.error}")
#         print("---")