#!/bin/bash
# Submit one PBS job per model as soon as its download is checksum-verified.
# usage: submit.sh "name:gguf:gpus:mem[:node]" ...  (node defaults to any L40S node)
cd ~/llm/models
for spec in "$@"; do IFS=: read n g gpus mem node <<< "$spec"
  first=$(grep -m1 "Qwen3.5-122B" sums.txt >/dev/null && [[ $g == Q4_K_M/* ]] && echo split)
  files=$( [ "$first" = split ] && grep -o "Q4_K_M/Qwen3.5-122B[^ ]*" sums.txt || echo "$g")
  for f in $files; do until [ -f "$f" ] && grep " $f\$" sums.txt | sha256sum -c --quiet 2>/dev/null; do sleep 60; done; done
  ppn=$((gpus * 8))
  id=$(qsub -N $n -o $HOME/llm/logs/$n.log -v NAME=$n,GGUF=$g -l nodes=${node:-1}:ppn=$ppn:gpus=$gpus:l40s,mem=$mem,walltime=12:00:00 $HOME/llm/bench.pbs)
  echo "$(date +%T) submitted $n as $id"
done
