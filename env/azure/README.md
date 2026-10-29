# Azure: running the benchmark on a T4 VM

Tested 2026-10-29: `Standard_NC4as_T4_v3` (1x Tesla T4 16 GB, 4 vCPU, 28 GB RAM) in North Europe, Microsoft
`ubuntu-hpc` 24.04 image (NVIDIA driver 580 preinstalled). Total cost about $3-4.

## Before you start

- **Quota:** `az vm list-usage -l northeurope -o table | grep -i T4`. The original subscription had 16 vCPUs
  of NCasT4_v3 in North Europe and no GPU quota anywhere else in Europe. Bigger GPUs (A10, A100, H100) need a
  quota request in the portal (Subscriptions > Usage + quotas).
- **Capacity:** quota does not guarantee hardware. NC16as and NC8as returned `AllocationFailed` in all zones
  that day; NC4as worked. Try `zone = "1"`, `"2"`, `"3"` in turn, or a smaller size.
- **Your IP:** disconnect any VPN and use `curl -4 https://api.ipify.org` for `allowed_ssh_cidrs`.

## 1. Create the VM (Terraform)

```bash
cd env/azure/terraform
cp terraform.tfvars.example terraform.tfvars   # fill in subscription_id and your IP
az login
terraform init && terraform apply
```

Or with the Azure CLI only (what the original run used):

```bash
az group create -n rg-llm-bench-neu -l northeurope
az network nsg create -g rg-llm-bench-neu -n nsg-llmbench
az network nsg rule create -g rg-llm-bench-neu --nsg-name nsg-llmbench -n ssh-from-me --priority 100 \
  --source-address-prefixes <YOUR_IP>/32 --destination-port-ranges 22 --access Allow --protocol Tcp
az vm create -g rg-llm-bench-neu -n vm-llmbench --size Standard_NC4as_T4_v3 \
  --image microsoft-dsvm:ubuntu-hpc:2404:latest --admin-username llmbench \
  --ssh-key-values ~/.ssh/id_ed25519.pub --os-disk-size-gb 256 --storage-sku Premium_LRS \
  --nsg nsg-llmbench --public-ip-sku Standard --nic-delete-option Delete --os-disk-delete-option Delete
az vm auto-shutdown -g rg-llm-bench-neu -n vm-llmbench --time 2300
```

Pin the host key through Azure rather than trusting the first connection:

```bash
az vm run-command invoke -g rg-llm-bench-neu -n vm-llmbench --command-id RunShellScript \
  --scripts "cat /etc/ssh/ssh_host_ed25519_key.pub"
```

## 2. Install and run (from the repo root on your machine)

```bash
VM=llmbench@<public_ip>
ssh $VM 'mkdir -p ~/llm/bench/results ~/llm/models'
tar czf - -C bench run.py tasks.py make_data.py docs2txt.py data results/rag_index.json | ssh $VM 'tar xzf - -C ~/llm/bench'
scp env/azure/list.txt env/azure/sums.txt $VM:llm/models/
scp env/azure/dl_sums.txt env/azure/setup_azure.sh env/laptop/fetch_models.sh $VM:llm/
scp env/azure/queue_azure.sh $VM:llm/bench/
ssh $VM 'bash ~/llm/setup_azure.sh && bash ~/llm/fetch_models.sh > ~/llm/fetch.log 2>&1'   # ~45 GB, minutes in Azure
ssh $VM 'cd ~/llm/bench && setsid nohup bash queue_azure.sh > ~/llm/queue.log 2>&1 < /dev/null &'
```

The queue runs Qwen3.5-9B, Gemma-4-E4B, gpt-oss-20b and Qwen3.5-35B-A3B (about 3 hours in total), then
`llama-bench`, and prints `ALL DONE` in `~/llm/queue.log`.

## 3. Collect results and delete everything

```bash
ssh $VM 'tar czf - -C ~/llm/bench/results .' | tar xzf - -C bench/results
terraform destroy        # or: az group delete -n rg-llm-bench-neu --yes
```

Failed `az vm create` attempts leave public IPs behind that are billed; deleting the resource group removes them.
