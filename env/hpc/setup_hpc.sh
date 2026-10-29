#!/bin/bash
# One-time setup on the RTU HPC login node (ui-1.hpc.rtu.lv). Run from this directory after copying the repo:
#   bash setup_hpc.sh
# Creates ~/llm/{llama.cpp,lib,venv,models,bench,logs}. Needs no root: llama.cpp runs inside a stock Debian
# container because CentOS 7's glibc (2.17) is too old for the official binaries (need >= 2.38).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../.." && pwd)
LLM=$HOME/llm
mkdir -p $LLM/{llama.cpp,dl,models/Q4_K_M,bench/results,logs,lib,sif,apptainer-cache}

# 1. llama.cpp b11639, official CUDA 12.8 build, checksum-verified (same build as laptop and Azure).
cd $LLM/dl
for f in llama-b11639-bin-ubuntu-cuda-12.8-x64.tar.gz cudart-llama-b11639-bin-ubuntu-cuda-12.8-x64.tar.gz; do
  [ -f $f ] || curl -sLO --fail https://github.com/ggml-org/llama.cpp/releases/download/b11639/$f
done
sha256sum -c $REPO/env/laptop/llama_sums.txt
for t in *.tar.gz; do tar xzf $t -C $LLM/llama.cpp; done

# 2. Debian 13 Python image. Singularity 3.4.1 (setuid) works on the login node for setup;
#    jobs use Apptainer from node-local /scratch instead (Singularity hangs on compute nodes).
module load singularity/3.4.1
export APPTAINER_CACHEDIR=$LLM/apptainer-cache SINGULARITY_CACHEDIR=$LLM/apptainer-cache
[ -f $LLM/sif/python312-trixie.sif ] || singularity pull $LLM/sif/python312-trixie.sif docker://python:3.12-slim-trixie
C="singularity exec $LLM/sif/python312-trixie.sif"

# 3. OpenMP runtime missing from the slim image: official Debian package, SHA-256 checked against the archive index.
$C python3 -I $HERE/getgomp.py $LLM/lib

# 4. Python venv (inside the container's Python) with the libraries generated scripts may use.
[ -x $LLM/venv/bin/python ] || $C python3 -m venv $LLM/venv
$C $LLM/venv/bin/pip -q install numpy pandas biopython

# 5. Benchmark harness, data and the precomputed RAG index.
cp $REPO/bench/{run.py,tasks.py,make_data.py,docs2txt.py} $LLM/bench/
cp -r $REPO/bench/data $LLM/bench/
cp $REPO/bench/results/rag_index.json $LLM/bench/results/
cp $HERE/bench.pbs $HERE/submit.sh $LLM/
cp $HERE/list.txt $HERE/sums.txt $LLM/models/
sed 's|^cd ~/llm/models|cd ~/llm/models; mkdir -p Q4_K_M|' $REPO/env/laptop/fetch_models.sh > $LLM/fetch_models.sh

$C env LD_LIBRARY_PATH=$LLM/llama.cpp/llama-b11639:$(echo $LLM/llama.cpp/cudart-*):$LLM/lib \
  $LLM/llama.cpp/llama-b11639/llama-server --version
echo "Setup done. Next: setsid nohup bash ~/llm/fetch_models.sh > ~/llm/fetch.log 2>&1 < /dev/null &"
