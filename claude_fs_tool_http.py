# claude_fs_tool_http.py

import os
import json
import requests

# === Your FastAPI filesystem config ===
API_BASE = "http://155.138.159.75"
AUTH     = ("admin", "supersecret")
# =======================================

# === Claude HTTP Chat Config ===
ANTHROPIC_CHAT_URL = "https://api.anthropic.com/v1/messages"
API_KEY            = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("Set your ANTHROPIC_API_KEY environment variable before running.")

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-11-08",
    "Content-Type": "application/json"
}
# =================================

def list_dir(path: str):
    r = requests.get(f"{API_BASE}/fs/list", auth=AUTH, params={"path": path})
    r.raise_for_status()
    return r.json()

def read_file(path: str):
    r = requests.get(f"{API_BASE}/fs/read", auth=AUTH, params={"path": path})
    r.raise_for_status()
    return r.text

def claude_chat(raw_messages):
    system_prompt = raw_messages[0]["content"]
    chat_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in raw_messages[1:]
        if m["role"] in ("user", "assistant")
    ]
    payload = {
        "model": "claude-2",
        "system_prompt": system_prompt,
        "messages": chat_messages,
        "max_tokens_to_sample": 1000,
        "stream": False
    }
    resp = requests.post(ANTHROPIC_CHAT_URL, headers=HEADERS, json=payload)
    print("REQUEST PAYLOAD:", json.dumps(payload, indent=2))
    resp.raise_for_status()
    return resp.json()

def main():
    # Tool definitions for Claude
    tools = [
        {
            "name": "list_dir",
            "description": "List files and directories under a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to /root/api"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "read_file",
            "description": "Read the contents of a file at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to /root/api"}
                },
                "required": ["path"]
            }
        }
    ]

    # 1) Ask Claude to pick a tool
    messages = [
        {"role": "system", "content": "You are a programming assistant with filesystem tools."},
        {"role": "user",   "content": "Please list the files in the project root and show me README.md."}
    ]

    resp1 = claude_chat(messages)
    choice = resp1["choices"][0]["message"]
    if "function_call" not in choice:
        print("Claude did not choose a function:", choice["content"])
        return

    # 2) Execute the function
    fname = choice["function_call"]["name"]
    args  = json.loads(choice["function_call"]["arguments"])
    if fname == "list_dir":
        result = list_dir(**args)
    else:
        result = read_file(**args)

    # 3) Give Claude the function result
    messages.append(choice)
    messages.append({
        "role": "function",
        "name": fname,
        "content": json.dumps(result)
    })

    resp2 = claude_chat(messages)
    print(resp2["choices"][0]["message"]["content"])

if __name__ == "__main__":
    main()
