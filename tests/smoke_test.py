"""Headless smoke test for the Streamlit app.

Uses Streamlit's built-in AppTest harness to actually *execute* the app script
in a simulated runtime and capture any exception -- no browser required. This
catches import-time and first-render errors (the exact class of failures that
still return HTTP 200 from the server but show a traceback in the browser).

Usage:
    python3 tests/smoke_test.py [path-to-app.py]

Exits non-zero if the app raises or renders no title.
"""
import sys

from streamlit.testing.v1 import AppTest

APP = sys.argv[1] if len(sys.argv) > 1 else "/packet_raptor/packet_raptor.py"


# Backends used only on the chat page (load_model / ChatWithPCAP). The page-1
# render does not import these, so check them explicitly -- this is the layer
# where the Instructor/sentence-transformers/huggingface_hub rot bites.
CHAT_BACKENDS = [
    ("InstructorEmbedding", "INSTRUCTOR"),
    ("sentence_transformers", "SentenceTransformer"),
    ("langchain_community.embeddings", "HuggingFaceInstructEmbeddings"),
    ("langchain_community.vectorstores", "Chroma"),
    ("langchain_experimental.text_splitter", "SemanticChunker"),
    ("langchain.chains", "ConversationalRetrievalChain"),
    ("langchain.memory", "ConversationBufferMemory"),
    ("langchain_openai", "ChatOpenAI"),
]


def check_chat_backends() -> int:
    import importlib
    print("Checking chat-path backend imports...")
    for mod, obj in CHAT_BACKENDS:
        try:
            getattr(importlib.import_module(mod), obj)
            print(f"  OK   {mod}.{obj}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL {mod}.{obj} -> {type(e).__name__}: {e}")
            return 3
    return 0


def main() -> int:
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()

    if at.exception:
        print("FAIL: the app raised while rendering:")
        for exc in at.exception:
            print(f"  {exc.value}")
        return 1

    titles = [t.value for t in at.title]
    print(f"OK: app rendered without exception. Titles: {titles}")
    if not titles:
        print("WARN: no title element was rendered")
        return 2

    return check_chat_backends()


if __name__ == "__main__":
    raise SystemExit(main())
