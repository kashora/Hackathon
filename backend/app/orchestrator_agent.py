from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, END

load_dotenv() # to load gemini API key

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

class OrchestrationState(TypedDict):
    raw_chat_history: List[List[str]]
    knowledge_base_data: str
    current_query: str
    
    technical_analysis: str
    business_analysis: str
    final_report: str
    
def format_chat_history_for_prompt(raw_history: List[List[str]]) -> str:
    if not raw_history:
        return "No previous conversation history."
    return "\n".join([f"{item[0].capitalize()}: {item[1]}" for item in raw_history])


technical_analyst_system_prompt = (
    "You are a meticulous Technical Analyst. Your task is to analyze the provided knowledge base data "
    "and the ongoing conversation (especially the latest query) from a purely technical perspective. "
    "Focus on aspects like technical feasibility, system architecture implications, data structures, "
    "algorithms, potential technical challenges, and technological opportunities. "
    "Be concise and specific in your analysis."
)
technical_analyst_human_template = """
Current User Query: {current_query}

Full Conversation History:
{formatted_chat_history}

Provided Knowledge Base Data (relevant to the current query):
{knowledge_base_data}

Based on all the above information, provide your focused technical analysis:
"""

technical_analyst_prompt = ChatPromptTemplate.from_messages([
    ("system", technical_analyst_system_prompt),
    ("human", technical_analyst_human_template)
])
technical_analyst_chain = technical_analyst_prompt | llm | StrOutputParser()

# Business Analyst Agent
business_analyst_system_prompt = (
    "You are a strategic Business Analyst. Your task is to analyze the provided knowledge base data "
    "and the ongoing conversation (especially the latest query) from a business perspective. "
    "Focus on aspects like market viability, user needs, business model implications, potential ROI, "
    "business risks, and strategic alignment or opportunities. "
    "Be concise and insightful in your analysis."
)
business_analyst_human_template = """
Current User Query: {current_query}

Full Conversation History:
{formatted_chat_history}

Provided Knowledge Base Data (relevant to the current query):
{knowledge_base_data}

Based on all the above information, provide your focused business analysis:
"""
business_analyst_prompt = ChatPromptTemplate.from_messages([
    ("system", business_analyst_system_prompt),
    ("human", business_analyst_human_template)
])
business_analyst_chain = business_analyst_prompt | llm | StrOutputParser()

# Report Agent
report_agent_system_prompt = (
    "You are a proficient Report Agent. Your task is to synthesize the provided Technical Analysis "
    "and Business Analysis into a single, comprehensive, and coherent summary report. "
    "The report must directly address the user's current query and take into account the "
    "overall conversation context. Make it clear, well-structured, and easy to understand."
)
report_agent_human_template = """
Original User Query that this report addresses: {current_query}

Full Conversation History:
{formatted_chat_history}

Technical Analysis Provided:
{technical_analysis}

Business Analysis Provided:
{business_analysis}

Generate a consolidated report based on all the above information:


"""
report_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", report_agent_system_prompt),
    ("human", report_agent_human_template)
])
report_agent_chain = report_agent_prompt | llm | StrOutputParser()


# 5. Define Nodes for the Graph

def prepare_input_node(state: OrchestrationState) -> Dict[str, Any]:
    raw_history = state["raw_chat_history"]
    current_query = "No query found"
    if raw_history:
        # Find the last user query
        for i in range(len(raw_history) - 1, -1, -1):
            if raw_history[i][0].lower() == 'user':
                current_query = raw_history[i][1]
                break
    
    return {"current_query": current_query}

def technical_analyst_node(state: OrchestrationState) -> Dict[str, str]:
    formatted_history = format_chat_history_for_prompt(state["raw_chat_history"])
    analysis = technical_analyst_chain.invoke({
        "current_query": state["current_query"],
        "formatted_chat_history": formatted_history,
        "knowledge_base_data": state["knowledge_base_data"]
    })
    return {"technical_analysis": analysis}

def business_analyst_node(state: OrchestrationState) -> Dict[str, str]:
    formatted_history = format_chat_history_for_prompt(state["raw_chat_history"])
    analysis = business_analyst_chain.invoke({
        "current_query": state["current_query"],
        "formatted_chat_history": formatted_history,
        "knowledge_base_data": state["knowledge_base_data"]
    })
    return {"business_analysis": analysis}

def report_agent_node(state: OrchestrationState) -> Dict[str, str]:
    formatted_history = format_chat_history_for_prompt(state["raw_chat_history"])
    report = report_agent_chain.invoke({
        "current_query": state["current_query"],
        "formatted_chat_history": formatted_history,
        "technical_analysis": state["technical_analysis"],
        "business_analysis": state["business_analysis"]
    })
    return {"final_report": report}

# 6. Construct the Graph (Orchestration Workflow)
workflow = StateGraph(OrchestrationState)

# Add nodes
workflow.add_node("prepare_inputs", prepare_input_node)
workflow.add_node("technical_analyst", technical_analyst_node)
workflow.add_node("business_analyst", business_analyst_node)
workflow.add_node("report_agent", report_agent_node)

# Set entry point
workflow.set_entry_point("prepare_inputs")

# Add sequential edges
workflow.add_edge("prepare_inputs", "technical_analyst")
workflow.add_edge("technical_analyst", "business_analyst")
workflow.add_edge("business_analyst", "report_agent")
workflow.add_edge("report_agent", END)

# Compile the workflow
app = workflow.compile()

# 7. Run the Orchestration Workflow

def run_orchestration(
    raw_chat_history: List[List[str]], 
    knowledge_base_data: str
) -> str:
    initial_state = {
        "raw_chat_history": raw_chat_history,
        "knowledge_base_data": knowledge_base_data,
        "current_query": "", 
        "technical_analysis": "",
        "business_analysis": "",
        "final_report": ""
    }
    
    final_state = app.invoke(initial_state, {"recursion_limit": 10})
    
    
    if final_state and final_state.get("final_report") and final_state.get("final_report") != "cannot generate response":
        return final_state
    else:
        return "Error: Could not generate report."

from pprint import pprint
# Example Usage:
if __name__ == "__main__":
    sample_chat_history = [
        ["user", "We are considering developing a new mobile app for budget tracking. What are the key considerations?"],
        ["assistant", "That's a broad question! Could you specify if you're interested in technical aspects, market demand, or something else?"],
        ["user", "Let's focus on how to make it stand out in terms of features and user engagement, considering data privacy."]
    ]
    
    sample_knowledge_base_data = (
        "Recent market research indicates a high demand for budget tracking apps with strong AI-driven insights and gamification features. "
        "Key privacy regulations like GDPR and CCPA must be adhered to, requiring robust data encryption and user consent mechanisms. "
        "Competitor apps often lack personalized financial advice. Technology trends point towards using federated learning for privacy-preserving AI features."
    )

    final_report_output = run_orchestration(sample_chat_history, sample_knowledge_base_data)

    sample_chat_history_2 = [
        ["user", "What are the pros and cons of using Python for web development?"]
    ]
    sample_knowledge_base_data_2 = (
        "Python is widely used for web development with frameworks like Django and Flask. "
        "Pros: Large ecosystem, readability, rapid development. "
        "Cons: Global Interpreter Lock (GIL) can be a bottleneck for CPU-bound tasks, "
        "sometimes slower performance compared to languages like Go or Java for specific use cases. "
        "Excellent for AI/ML integration."
    )
    final_report_output_2 = run_orchestration(sample_chat_history_2, sample_knowledge_base_data_2)

    
    sample_chat_history_3 = [
        ["user", "Hello"]
    ]
    sample_knowledge_base_data_3 = (
        "no relevant data "
    )
    final_report_output_3 = run_orchestration(sample_chat_history_3, sample_knowledge_base_data_3)