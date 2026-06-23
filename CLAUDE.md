# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Packet Raptor is an AI assistant for chatting with network packet captures (`.pcap`). It applies the RAPTOR pattern (Recursive Abstractive Processing for Tree-Organized Retrieval) to packet data: PCAP → JSON → semantic chunks → recursively clustered + LLM-summarized tree → Chroma vector store → conversational retrieval with multi-query synthesis. The entire application is a single Streamlit script: `packet_raptor/packet_raptor.py`.

## Running

The app is designed to run only via Docker Compose (it depends on a sibling Ollama service and expects NVIDIA GPUs):

```bash
docker-compose up        # builds packet_raptor, starts ollama + ollama-webui
```

- Packet Raptor UI: http://localhost:8585
- Ollama WebUI (use this to pull/download models first): http://localhost:3002
- Ollama API: http://localhost:11434

Workflow: pull a model via Ollama WebUI, then open Packet Raptor, upload a `.pcap`, select the model, wait for the tree to build, and ask questions. Works best on **larger** captures; for small PCAPs the sibling project "Packet Buddy" is recommended.

Inside the container the startup command is `scripts/startup.sh` → `streamlit run packet_raptor.py`. There is no separate build, lint, or test setup — there are no tests, no requirements.txt (deps are installed directly in `docker/Dockerfile`), and no linter config.

## Architecture (the RAPTOR pipeline)

`ChatWithPCAP.__init__` runs the whole pipeline in sequence; read it as the table of contents:

1. **PCAP → JSON** — `pcap_to_json()` shells out to `tshark -nlr <pcap> -T json`. Done in the upload page before the chat instance is created.
2. **Load + chunk** — `JSONLoader` with `jq_schema=".[] | ._source.layers"` extracts per-packet layer data; `SemanticChunker` (over the embedding model) splits it into docs.
3. **Leaf nodes + embeddings** — each chunk becomes a `Node`; embedded with HuggingFace Instructor (`hkunlp/instructor-large`) on CUDA.
4. **Tree build** — `build_tree` → `recursive_cluster_summarize`: KMeans-cluster nodes (`determine_initial_clusters` = sqrt heuristic), LLM-summarize each cluster into a parent node, recurse until a single `root_node` remains.
5. **Vector store** — `store_in_chroma` traverses the tree, collecting both leaf texts and intermediate summaries into one in-memory Chroma collection.
6. **Retrieval chain** — `ConversationalRetrievalChain` over the Chroma retriever (`k=10`) with `ConversationBufferMemory`.

**Query path** (`chat()`): generates 4 related queries via the LLM (`generate_related_queries`, JSON parsed by `extract_json_from_response`), runs the original + related queries through the retrieval chain, then `create_synthesis_prompt` asks the LLM to synthesize one composite answer. The RAPTOR tree is also rendered as an interactive pyvis/networkx graph (`create_tree_graph`) saved to `tree.html` and embedded in the page.

The two-page Streamlit flow is driven by `st.session_state['page']` (1 = `upload_and_convert_pcap`, 2 = `chat_interface`), set at the bottom `__main__` block.

## Things to know before editing

- **LLM backend is OpenAI-compatible and auto-detected**: the LLM is a `ChatOpenAI` client pointed at `{server}/v1`, so it works against **both Ollama and llama.cpp** (mirrors what our `local-packet-whisperer` fork does). The server URL is not hardcoded — it defaults to `OLLAMA_URL` env (or `http://ollama:11434`) and is editable in the upload page; `detect_backend()` probes `/api/version` (Ollama) vs `/health` (llama.cpp) and shows a badge. The hostname `ollama` only resolves inside the compose network. Because it's a chat model, `self.llm.invoke(...)` returns an `AIMessage` (use `.content`), not a bare string.
- **GPU optional**: `load_model()` picks `cuda` when `torch.cuda.is_available()` else `cpu`, so the Instructor embeddings run on either. The compose GPU reservations are commented out by default (CPU-friendly, runs on GPU-less hosts like ihkki); uncomment the `deploy:` blocks on an NVIDIA host. The LLM itself runs on the backend, not in-process, so it never needs a local GPU.
- **Pinned versions matter**: `sentence-transformers==2.2.2` is pinned in the Dockerfile because newer versions break `InstructorEmbedding`. Don't bump it casually.
- The model is cached at import via `@st.cache_resource load_model()` so the Instructor weights download once per session.
- Uploaded PCAPs and generated JSON land in `temp/` next to the script; `tree.html` is written to the working dir. Both `data/` (Ollama/webui volumes) and `temp` artifacts are gitignored-adjacent runtime files.
