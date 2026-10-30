#!/usr/bin/env python3
"""Ask a local Qwen or Llama model through Ollama. No API key and no paid account."""

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a local Llama or Qwen model through Ollama. No API key."
    )
    parser.add_argument("text", nargs="*", help="Question. If omitted, the script reads stdin.")
    parser.add_argument(
        "--model",
        default="qwen2.5:7b",
        help="Ollama model name. Examples: qwen2.5:7b, qwen2.5:3b, llama3.1, llama3.2:3b.",
    )
    parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama base URL.")
    args = parser.parse_args()
    prompt = " ".join(args.text).strip() or sys.stdin.read().strip()
    if not prompt:
        sys.exit("Pass a question, or pipe the finding text in.")

    body = json.dumps(
        {
            "model": args.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You help a piping designer read one Ledger P&ID finding. "
                        "Answer in a few sentences. Use only tags and facts that are in the question. "
                        "If the text is only a candidate from a PDF, say it still needs a designer to confirm it."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        args.host.rstrip("/") + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        sys.exit(
            f"Ollama answered {error.code} for model {args.model}. "
            f"If the model is missing, run: ollama pull {args.model}\n{detail}"
        )
    except urllib.error.URLError as error:
        sys.exit(
            "Could not reach a local model at "
            + args.host
            + ". Install Ollama from https://ollama.com/download, start it, then run: ollama pull "
            + args.model
            + ". Ledger never sends this question to a paid API. Detail: "
            + str(error.reason)
        )
    message = ((payload.get("message") or {}).get("content") or "").strip()
    if not message:
        sys.exit("The local model returned an empty answer.")
    sys.stdout.write(message + "\n")


if __name__ == "__main__":
    main()
