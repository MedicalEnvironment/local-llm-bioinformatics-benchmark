# Laptop: running the benchmark locally

**Prerequisites:** Linux with an NVIDIA GPU (8 GB+ memory) and driver, Python 3.10+, `curl`, about 15 GB of disk. No root access needed. Replace `<path-to-repo>` with where you cloned this repository.

Original run: RTX 4060 Laptop GPU (8 GB), Ryzen 7 7435HS, 15 GB RAM, Ubuntu 26.04. No root needed.

```bash
mkdir -p ~/llm/{llama.cpp,dl,models} && cd ~/llm/dl
xargs -n1 curl -sLO < <path-to-repo>/env/laptop/llama_urls.txt
sha256sum -c <path-to-repo>/env/laptop/llama_sums.txt
for t in *.tar.gz; do tar xzf $t -C ~/llm/llama.cpp; done
python3 -m venv ~/llm/venv && ~/llm/venv/bin/pip install numpy pandas biopython
cp <path-to-repo>/env/laptop/{list.txt,sums.txt} ~/llm/models/ && bash <path-to-repo>/env/laptop/fetch_models.sh
mkdir -p ~/llm/bench && cp -r <path-to-repo>/bench/* ~/llm/bench/
cd ~/llm/bench && bash <path-to-repo>/env/laptop/queue_laptop.sh
```

Interactive use: `llama-server -m ~/llm/models/Qwen3.5-9B-Q4_K_M.gguf -c 16384 -fa on --fit on`, then open
http://127.0.0.1:9931/ (this build's default port is 9931, not 8080).

`run.py embed` rebuilds the RAG index and needs EmbeddingGemma-300M
(`ggml-org/embeddinggemma-300M-GGUF`, `embeddinggemma-300M-Q8_0.gguf`); the committed
`bench/results/rag_index.json` makes this unnecessary.
