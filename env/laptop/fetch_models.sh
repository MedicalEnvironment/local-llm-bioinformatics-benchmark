#!/bin/bash
# Resumable HF downloader: retries on stalls (<10 KB/s for 20 s), then verifies sha256.
cd ~/llm/models
while read r f; do
  [ -f "$f" ] && continue
  for i in $(seq 1 200); do
    curl -sL --fail -C - --speed-limit 10000 --speed-time 20 -o "$f.part" "https://huggingface.co/$r/resolve/main/$f" && { mv "$f.part" "$f"; echo "$(date +%T) done $f"; break; }
    echo "$(date +%T) retry $i $f ($(stat -c%s "$f.part" 2>/dev/null) B)"; sleep 2
  done
done < list.txt
sha256sum -c sums.txt
