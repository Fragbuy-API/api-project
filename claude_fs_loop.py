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
    if isinstance(data.get("content"), list):
        return "".join(block.get("text", "") for block in data["content"])
    raise RuntimeError(f"Unexpected response shape: {data}")


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start == -1 or end == -1:
        raise RuntimeError(f"Couldn't find JSON in response: {raw}")
    return json.loads(raw[start:end])


def main():
    # Define system prompt enforcing one tool call per turn
    SYSTEM = """
You are a programming assistant with two tools:

1. list_dir(path) → returns JSON listing of files/directories in /root/api.
2. read_file(path) → returns the raw text of a file in /root/api.

When you want to call a tool, output only that single JSON object and nothing else:

{
  "tool": "<tool_name>",
  "arguments": { "path": "<relative-path>" }
}

After I run the tool and feed back the result, you may call the next tool. Stop when you have finished processing all tasks and output only the final answer.
""".strip()

    # Initial user request
    user_request = "List the files in the project root and then show me README.md."
    
    # Conversation history seeded with user request
    convo = [{"role": "user", "content": user_request}]

    while True:
        # Ask Claude for one tool call or final answer
        raw_reply = call_claude(SYSTEM, convo)

        # Try to extract a tool call JSON
        try:
            call = extract_json(raw_reply)
        except RuntimeError:
            # No JSON: treat raw_reply as final answer and print
            print(raw_reply)
            break

        tool = call.get("tool")
        path = call.get("arguments", {}).get("path")

        # Execute the tool
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

        # Append Claude's tool call and the result as assistant messages
        convo.append({"role": "assistant", "content": raw_reply})
        convo.append({"role": "assistant", "content": json.dumps(result)})

    # End of loop

if __name__ == "__main__":
    main()
