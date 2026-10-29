# RTU HPC (Rudens cluster): running the benchmark on L40S GPUs

**Prerequisites:** an RTU HPC account with an allocation (jobs are charged to it), SSH key login, and basic familiarity with PBS (`qsub`, `qstat`). This guide is specific to the RTU "Rudens" cluster; on another Torque/PBS cluster, the node names, modules and GPU properties will differ.

Tested 2026-10-29 on `ui-1.hpc.rtu.lv` (CentOS 7, Torque 6.1 + Moab, NVIDIA driver 550) with jobs on the
L40S nodes `wn73` (1 GPU) and `wn75` (2 GPUs).

## Node types with GPUs (as listed by `pbsnodes` on the day)

| Nodes | GPUs | CPU / RAM | Property to request |
| --- | --- | --- | --- |
| wn71, wn72 | 4x L40S 48 GB | Xeon Gold 6548 | `l40s` |
| wn73-wn76 | 2x L40S 48 GB | 2x EPYC 9654 (192 cores), 1.5 TB | `l40s` |
| wn44 | 4x A100 40 GB | | `a100` |
| wn59, wn60 | 4x V100 16 GB | | `v100` |

The official llama.cpp CUDA 12.8 build includes native code for the L40S (sm_89), so it runs on the 550 driver
through CUDA minor-version compatibility. For A100/V100 it would need PTX JIT, which the 550 driver cannot do
for CUDA 12.8 code: use the L40S nodes, or build llama.cpp against CUDA 12.4.

## Steps

1. **SSH.** Add `ssh_config.example` to `~/.ssh/config` (shared connection), copy your key with
   `ssh-copy-id`, and verify the host key fingerprint with hpc@rtu.lv before accepting it.
2. **Copy the repo** to the cluster: `scp -r comperehensive_llm_run ui-1.hpc.rtu.lv:`.
3. **Set up** (login node, about 5 minutes): `bash comperehensive_llm_run/env/hpc/setup_hpc.sh`.
4. **Download models** (about 180 GB for all of `list.txt`; reorder the list to get the one you need first):
   `setsid nohup bash ~/llm/fetch_models.sh > ~/llm/fetch.log 2>&1 < /dev/null &`.
   If a download slows to a crawl, kill its `curl` process; the loop resumes with a fresh connection.
5. **Submit** one job per model; `submit.sh` waits until the file passes its checksum:

   ```bash
   cd ~/llm
   # name:gguf:gpus:mem[:node]
   setsid nohup bash submit.sh "hpc-qwen3.5-9b:Qwen3.5-9B-Q4_K_M.gguf:1:48gb:wn73" \
       "hpc-qwen3.5-122b-a10b:Q4_K_M/Qwen3.5-122B-A10B-Q4_K_M-00001-of-00003.gguf:2:160gb:wn75" \
       > submit.log 2>&1 < /dev/null &
   ```
6. **Watch:** `qstat -u $USER`, `tail -f ~/llm/bench/results/<name>.progress`. Results land in
   `~/llm/bench/results/<name>.json`; the Torque log `~/llm/logs/<name>.log` appears when the job ends.

## What bench.pbs does

- Reads the job's GPUs from `PBS_GPUFILE` into `CUDA_VISIBLE_DEVICES`, picks a free port (nodes are shared).
- Unpacks `python:3.12-slim-trixie` with Apptainer 1.1.6 into node-local `/scratch` (a few seconds) and runs
  everything inside it with `--nv`.
- Passes the library path as `APPTAINERENV_LD_LIBRARY_PATH` (Apptainer resets `LD_LIBRARY_PATH`).
- Runs the 53 items with the same settings as the laptop and Azure, then `llama-bench`.

## Pitfalls met during the original run

- **Singularity 3.4.1 hangs on compute nodes** (works on the login node). Use Apptainer from `/scratch`.
- **wn74** kept a stuck container process (uninterruptible kernel wait) that blocked new containers. If a job
  shows zero CPU time after minutes, look with `ssh <node> ps -u $USER -o pid,stat,wchan:22,args` and move on.
- **Reservations:** a job pinned to `wn71` stayed queued; `checkjob <id>` showed the node was `Reserved`.
- **`pkill -f pattern` over SSH** can kill your own SSH session when the pattern appears in the command line;
  kill by PID or from a script file.
- Jobs are charged to your group's Moab allocation (`mam-balance`).
