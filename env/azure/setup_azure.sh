#!/bin/bash
set -e
mkdir -p ~/llm/llama.cpp ~/llm/dl ~/llm/models
cd ~/llm/dl
for u in https://github.com/ggml-org/llama.cpp/releases/download/b11639/cudart-llama-b11639-bin-ubuntu-cuda-12.8-x64.tar.gz https://github.com/ggml-org/llama.cpp/releases/download/b11639/llama-b11639-bin-ubuntu-cuda-12.8-x64.tar.gz; do curl -sLO --fail $u; done
sha256sum -c ~/llm/dl_sums.txt
for t in *.tar.gz; do tar xzf $t -C ~/llm/llama.cpp; done
ls ~/llm/llama.cpp ~/llm/llama.cpp/*/ | head -20
python3 -m venv ~/llm/venv && ~/llm/venv/bin/pip -q install numpy pandas biopython
