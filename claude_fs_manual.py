import os
import json
import requests

# === Configuration ===
API_BASE        = "http://155.138.159.75"
AUTH            = ("admin", "supersecret")
CLAUDE_ENDPOINT = "https://api.anthropic.com/v1/messages"
HEADERS = {
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json",
}
# =====================

def call_claude(system_prompt: str, messages: list[dict]) -> str:
    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "system": system_prompt,
        "messages": messages,
        "max_tokens": 1000,
    }
    resp = requests.post(CLAUDE_ENDPOINT, headers=HEADERS, json=payload)
    if not resp.ok:
        print("=== REQUEST ===")
        print(json.dumps(payload, indent=2))
        print("=== RESPONSE ===")
        print(resp.status_code, resp.text)
        resp.raise_for_status()

    data = resp.json()
    # Anthropic returns content as a list of blocks
    if isinstance(data.get("content"), list):
        return "".join(block.get("text", "") for block in data["content"])
    else:
        raise RuntimeError(f"Unexpected response shape: {data}")

def main():
    # 1) Describe your tools via the system prompt
    SYSTEM = """
You are a programming assistant with two tools:

1. list_dir(path) → returns JSON listing of files/dirs in /root/api.
2. read_file(path) → returns raw text of a file in /root/api.

Whenever you want to call a tool, output *only* this JSON object and nothing else:

{
  "tool": "<tool_name>",
  "arguments": {
    "path": "<relative-path>"
  }
}

After I run the tool, I will feed you back the result so you can continue.
""".strip()

    # 2) Ask Claude what to do
    USER = "List the files in the project root and then show me README.md."

    # — Debug prints —
    print(">>> ABOUT TO CALL CLAUDE")
    print("SYSTEM PROMPT:", repr(SYSTEM))
    print("USER PROMPT:",   repr(USER))

    # 3) First round: Claude emits a JSON tool-call
    json_call = call_claude(
        SYSTEM,
        [{"role": "user", "content": USER}]
    )

    print("=== RAW json_call ===")
    print(repr(json_call))

    if not json_call:
        raise RuntimeError("❌ Received no content from Claude at all!")

    # 4) Parse & execute the tool-call locally
    # Extract the JSON object from any surrounding text
    json_call_stripped = json_call.strip()
    start = json_call_stripped.find("{")
    end   = json_call_stripped.rfind("}") + 1
    if start == -1 or end == -1:
        raise RuntimeError(f"❌ Couldn't find JSON object in Claude's response:\n{json_call}")
    json_text = json_call_stripped[start:end]
    call = json.loads(json_text)

    tool = call["tool"]
    path = call["arguments"]["path"]

    if tool == "list_dir":
        result = requests.get(
            f"{API_BASE}/fs/list",
            auth=AUTH,
            params={"path": path}
        ).json()
    elif tool == "read_file":
        result = requests.get(
            f"{API_BASE}/fs/read",
            auth=AUTH,
            params={"path": path}
        ).text
    else:
        raise RuntimeError(f"Unknown tool: {tool}")

    # 5) Feed the result back into Claude for its final answer
    followup = call_claude(
        SYSTEM,
        [
            {"role": "assistant", "content": json_call},
            {"role": "assistant", "content": json.dumps(result)}
        ]
    )

    print(followup)

if __name__ == "__main__":
    main()
