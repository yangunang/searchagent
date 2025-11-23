"""
AgentScope Stock Search Agent Demo
Searches for current stock information (e.g., NVIDIA)
"""
import os
import json
import requests
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope_runtime.engine.agents.agentscope_agent import AgentScopeAgent
from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest


# Define stock search tool
def search_stock_price(symbol: str) -> dict:
    """
    Search for current stock price information
    
    Args:
        symbol: Stock ticker symbol (e.g., NVDA, AAPL, MSFT)
        
    Returns:
        Dictionary with stock information
    """
    # Use Yahoo Finance API alternative or financial data API
    # For demo purposes, simulating with current NVIDIA data
    
    stock_data = {
        "NVDA": {
            "symbol": "NVDA",
            "company": "NVIDIA Corporation",
            "price": 180.05,
            "change": "+1.06%",
            "market_cap": "4.4T",
            "pe_ratio": 44.31,
            "52_week_high": 212.19,
            "52_week_low": 86.62,
            "description": "AI infrastructure and GPU computing company"
        },
        "AAPL": {
            "symbol": "AAPL",
            "company": "Apple Inc.",
            "price": 189.50,
            "change": "+0.5%",
            "market_cap": "3.0T"
        },
        "MSFT": {
            "symbol": "MSFT",
            "company": "Microsoft Corporation",
            "price": 378.20,
            "change": "+0.8%",
            "market_cap": "2.8T"
        }
    }
    
    symbol_upper = symbol.upper()
    if symbol_upper in stock_data:
        return {
            "status": "success",
            "data": stock_data[symbol_upper]
        }
    else:
        return {
            "status": "not_found",
            "message": f"Stock symbol '{symbol}' not found. Try NVDA, AAPL, or MSFT."
        }


# Create toolkit and register tool
toolkit = Toolkit()
toolkit.register_tool_function(search_stock_price)

# Create agent with stock search capability
agent = AgentScopeAgent(
    name="StockAssistant",
    model=DashScopeChatModel(
        "qwen-max",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    ),
    agent_config={
        "sys_prompt": (
            "You're a helpful financial assistant that can search stock prices. "
            "When users ask about stocks, use the search_stock_price tool to get current data. "
            "Provide clear, concise information about stock prices and market data."
        ),
        "toolkit": toolkit,
    },
    agent_builder=ReActAgent,
)

# Create AgentApp with multiple endpoints
app = AgentApp(agent=agent)


@app.endpoint("/stock_query")
def stock_query_handler(request: AgentRequest):
    """Handle stock price queries"""
    return {
        "status": "ok",
        "payload": request,
        "message": "Use /chat for interactive queries"
    }


@app.endpoint("/chat")
async def chat_handler(request: AgentRequest):
    """Handle chat-based stock queries"""
    # Process the user's query through the agent
    user_input = request.input[0]["content"][0]["text"] if request.input else "Hello"
    
    # Agent processes the query
    response = agent.reply({"content": user_input})
    
    return {
        "status": "success",
        "response": response.content if hasattr(response, 'content') else str(response),
        "session_id": request.session_id
    }


@app.endpoint("/stream_chat")
async def stream_chat_handler(request: AgentRequest):
    """Stream responses for stock queries"""
    user_input = request.input[0]["content"][0]["text"] if request.input else ""
    
    # Simulate streaming response
    yield f"Processing query: {user_input}\n"
    
    # Get stock info
    if "nvda" in user_input.lower() or "nvidia" in user_input.lower():
        result = search_stock_price("NVDA")
        if result["status"] == "success":
            data = result["data"]
            yield f"Stock: {data['company']} ({data['symbol']})\n"
            yield f"Current Price: ${data['price']}\n"
            yield f"Change: {data['change']}\n"
            yield f"Market Cap: {data['market_cap']}\n"
            yield f"P/E Ratio: {data['pe_ratio']}\n"
    else:
        yield "Please specify a stock symbol (e.g., NVDA, AAPL, MSFT)\n"


print("✅ Stock Search Agent configured successfully")
print("📊 Available endpoints: /stock_query, /chat, /stream_chat")
