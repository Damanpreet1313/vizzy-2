import urllib.parse
from typing import Dict, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.services.vector_store import get_vector_store

class PilotModeState(TypedDict):
    user_query: str
    collection_name: str
    chat_reply: str
    generated_image_url: str

def retrieve_and_generate_node(state: PilotModeState):
    query = state["user_query"]
    # Retrieve context from Milvus Lite
    vector_store = get_vector_store(collection_name=state["collection_name"])
    docs = vector_store.similarity_search(query, k=2)
    retrieved_context = "\n\n".join([doc.page_content for doc in docs])
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5, request_timeout=30)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Vizzy, an interactive e-reader companion. Based on the retrieved context, fulfill the user's creative request. Return ONLY a JSON string containing 'chat_reply' and 'image_prompt' keys."),
        ("user", "Context from book:\n{context}\n\nUser request: {query}")
    ])
    chain = prompt | llm | JsonOutputParser()
    try:
        res = chain.invoke({"context": retrieved_context, "query": query})
    except Exception:
        res = {
            "chat_reply": "I couldn't process that specific query smoothly, but here is a breathtaking conceptual visualization for you!",
            "image_prompt": f"Cinematic digital artwork depicting {query}"
        }
    encoded_prompt = urllib.parse.quote(res.get("image_prompt", query))
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true"
    return {
        "chat_reply": res.get("chat_reply", ""),
        "generated_image_url": img_url
    }

workflow = StateGraph(PilotModeState)
workflow.add_node("agent", retrieve_and_generate_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

pilot_mode_graph = workflow.compile()
