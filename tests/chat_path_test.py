"""Integration smoke test for the chat path (page 2 / ChatWithPCAP).

Drives the Streamlit app to page 2 via AppTest with a tiny synthetic capture, so
that load_model() + embeddings + Chroma + the retrieval chain all execute in a
real Streamlit runtime -- the path the page-1 render in smoke_test.py never reaches.

A single-packet capture yields one leaf node, so the RAPTOR tree short-circuits
without any LLM calls; this keeps the test fast while still exercising the heavy
wiring (Instructor embeddings, semantic chunking, Chroma, the chain setup).

Usage:  python3 tests/chat_path_test.py [path-to-app.py]
"""
import json
import os
import sys
import tempfile

from streamlit.testing.v1 import AppTest

APP = sys.argv[1] if len(sys.argv) > 1 else "/packet_raptor/packet_raptor.py"

TINY_CAPTURE = [
    {
        "_source": {
            "layers": {
                "frame": {"frame.number": "1", "frame.len": "74"},
                "ip": {"ip.src": "10.0.0.1", "ip.dst": "10.0.0.2"},
                "tcp": {"tcp.srcport": "1234", "tcp.dstport": "80", "tcp.flags": "0x0002"},
            }
        }
    }
]


def main() -> int:
    fd, json_path = tempfile.mkstemp(suffix=".pcap.json")
    with os.fdopen(fd, "w") as f:
        json.dump(TINY_CAPTURE, f)

    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["page"] = 2
    at.session_state["json_path"] = json_path
    at.session_state["selected_model"] = "smoke-test-model"
    at.session_state["llm_base_url"] = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    at.run()

    if at.exception:
        print("FAIL: chat path raised:")
        for exc in at.exception:
            print(f"  {exc.value}")
        return 1

    try:
        inst = at.session_state["chat_instance"]
    except (KeyError, AttributeError):
        inst = None
    if inst is None:
        print("FAIL: chat_instance was not created")
        return 2
    if getattr(inst, "root_node", None) is None:
        print("FAIL: RAPTOR tree has no root node")
        return 3

    print("OK: chat path built ChatWithPCAP + RAPTOR tree (embeddings/Chroma/chain) without exception.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
