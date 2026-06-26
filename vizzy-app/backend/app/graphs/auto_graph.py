import urllib.parse
from typing import List, Dict, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class AutoModeState(TypedDict):
    text_segments: List[str]
    current_index: int
    total_frames: int
    collection: List[Dict[str, Any]]

def analyze_scene_node(state: AutoModeState):
    idx = state["current_index"]
    current_text = state["text_segments"][idx]

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7, request_timeout=30)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a storyboard director. Find the single most visually stunning, dramatic, or exciting moment in the text segment. Output ONLY a valid JSON object with 'scene_justification', 'extracted_text_quote', and 'image_prompt'. Do not warp with markdown tags."),
        ("user", "Text: {text}")
    ])

    chain = prompt | llm | JsonOutputParser()
    try:
        ai_response = chain.invoke({"text": current_text[:4000]})  # Guard against context length
    except Exception:
        ai_response = {
            "scene_justification": "Fallback choice",
            "extracted_text_quote": "N/A",
            "image_prompt": "A beautiful cinematic digital painting of a dynamic fantasy setting, concept art style."
        }

    new_frame = {
        "frame_index": idx,
        "text_summary": ai_response.get("scene_justification", ""),
        "quote": ai_response.get("extracted_text_quote", ""),
        "prompt": ai_response.get("image_prompt", "")
    }

    collection = list(state["collection"])
    collection.append(new_frame)
    return {"collection": collection}

def generate_image_url_node(state: AutoModeState):
    idx = state["current_index"]
    updated_collection = list(state["collection"])
    target_prompt = updated_collection[idx]["prompt"]
    encoded_prompt = urllib.parse.quote(target_prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true"
    updated_collection[idx]["image_url"] = image_url
    return {"collection": updated_collection, "current_index": idx + 1}

def should_continue(state: AutoModeState):
    if state["current_index"] < state["total_frames"]:
        return "analyze"
    return END

workflow = StateGraph(AutoModeState)
workflow.add_node("analyze", analyze_scene_node)
workflow.add_node("generate_image", generate_image_url_node)
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "generate_image")
workflow.add_conditional_edges("generate_image", should_continue)

auto_mode_graph = workflow.compile()
