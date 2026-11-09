"""Thin wrapper around Gemini on Vertex AI: one client, retries, token accounting."""
import json
import re
import threading
import time

from google import genai
from google.genai import types

PROJECT = "storefront-agents-4128"
LOCATION = "global"
MODEL = "gemini-3.8-flash"

_client = None
_lock = threading.Lock()
USAGE = {}  # agent name -> {"calls", "input", "output", "thinking", "search_queries"}


def client():
    global _client
    if _client is None:
        _client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    return _client


def _record(agent, resp, search_queries=0):
    u = resp.usage_metadata
    with _lock:
        a = USAGE.setdefault(agent, {"calls": 0, "input": 0, "output": 0, "thinking": 0, "search_queries": 0})
        a["calls"] += 1
        a["input"] += u.prompt_token_count or 0
        a["output"] += u.candidates_token_count or 0
        a["thinking"] += getattr(u, "thoughts_token_count", 0) or 0
        a["search_queries"] += search_queries


def generate(agent, contents, *, json_mode=True, tools=None, thinking=None, retries=5):
    """Call the model. Returns (parsed JSON or text, raw response)."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json" if json_mode else None,
        tools=tools,
        thinking_config=types.ThinkingConfig(thinking_level=thinking) if thinking else None,
    )
    last = None
    for attempt in range(retries):
        try:
            resp = client().models.generate_content(model=MODEL, contents=contents, config=config)
            gm = resp.candidates[0].grounding_metadata if resp.candidates else None
            n_queries = len(gm.web_search_queries or []) if gm else 0
            _record(agent, resp, n_queries)
            if not json_mode:
                return resp.text, resp
            return parse_json(resp.text), resp
        except Exception as e:  # transient errors and bad JSON both retry
            last = e
            time.sleep(10 * (attempt + 1))  # 429s need real back-off
    raise RuntimeError(f"{agent}: {type(last).__name__}: {last}")


def parse_json(text):
    """Parse JSON, tolerating a ```json fence around it."""
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.S)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def image_part(path):
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")


def search_tool():
    return [types.Tool(google_search=types.GoogleSearch())]
