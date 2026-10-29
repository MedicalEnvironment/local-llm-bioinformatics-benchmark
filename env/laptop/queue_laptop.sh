#!/bin/bash
# Laptop queue: run the 53-item benchmark for each model, then llama-bench. Results: results/laptop-<model>.json
# Expects the layout from README.md: ~/llm/{llama.cpp,models,venv,bench}. run.py resumes where it stopped.
cd ~/llm/bench
PY=~/llm/venv/bin/python
COMMON="-c 16384 -fa on --fit on --reasoning-budget 6144"
SPECS="qwen3.5-9b:Qwen3.5-9B-Q4_K_M.gguf gemma4-e4b:gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
for s in $SPECS; do n=laptop-${s%%:*}; g=${s#*:}
  echo "$(date +%T) start $n"; $PY -u run.py model $n $g $COMMON 2>&1 | tee -a results/$n.progress
done
for s in $SPECS; do n=laptop-${s%%:*}; g=${s#*:}
  echo "$(date +%T) bench $n"; $PY run.py bench $n $g -fa on -fitt 512
done
echo ALL DONE
