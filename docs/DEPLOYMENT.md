## Target deployment (Azure, EU, < €200/month)

### Goals and constraints
- EU data residency (e.g., West Europe or North Europe)
- Public entrypoint with TLS
- Autoscale to handle bursts; scale to zero when idle
- Operate near or below €200/month at low/medium usage

### Recommended architecture (managed, cost‑efficient)
- Azure Container Apps (ACA) environment (West Europe)
  - One Container App per service: `reverseproxy`, `agentic-analysis`, `ingest-service`, `backend` (optional), and `frontend` (or host static assets separately).
  - Ingress:
    - Public ingress only on `reverseproxy`.
    - Internal ingress for other apps; reachable only inside the ACA environment.
  - Scaling:
    - Min replicas: 0 (scale‑to‑zero when idle).
    - Max replicas: 2–3.
    - Scale on HTTP RPS or CPU (e.g., RPS > 20 for 30s → +1 replica).

- Azure Database for PostgreSQL Flexible Server (Burstable, B1ms)
  - Same region and VNet integration with ACA.
  - Automatic backups; low‑cost burstable tier suitable for dev/small prod.

- Azure Container Registry (ACR) Basic
  - Stores application images.

- Azure Storage
  - Azure Files share mounted into `ingest-service` for `/app/data` (raw artifacts).
  - Optionally Azure Blob Storage for long‑term archival.

- Azure Key Vault
  - Secrets for DB, API keys (Azure/OpenAI), etc.

- Azure Monitor (Log Analytics) with tight retention
  - Keep retention 7–14 days to control costs.

### Network and security
- VNet‑integrated ACA and PostgreSQL.
- Only `reverseproxy` has public ingress.
- Enforce HTTPS; use managed certificates.
- IP allowlisting (if needed) at Application Gateway/Front Door or ACA level.

### Environment variables and secrets
- `agentic-analysis`:
  - `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_MODEL`, `AZURE_OPENAI_API_VERSION`
- `ingest-service` and `backend`:
  - `DATABASE_URL` or discrete vars (`SERVER_HOST`, `SERVER_DB`, etc.)
- Store secrets in Key Vault; mount into ACA via Key Vault references.

### Cost guidance (approximate, low load)
- PostgreSQL Flexible Server (B1ms): ~€30–€50
- ACR Basic: ~€4–€5
- ACA compute (scale‑to‑zero, small footprints): ~€20–€80 combined (usage‑dependent)
- Storage + bandwidth + logs: ~€10–€30
- Total typically within €100–€170 under light traffic; still <€200 with moderate usage

### Deployment workflow
1) Build and push images
```bash
# login and create ACR
az acr create -g <rg> -n <acrName> --sku Basic
az acr login -n <acrName>

# build & push (example for reverseproxy)
docker build -t <acrName>.azurecr.io/digiedu/reverseproxy:latest srcs/reverseproxy
docker push <acrName>.azurecr.io/digiedu/reverseproxy:latest

# repeat for: frontend, agentic_analysis, ingest_service, server
```

2) Provision Azure resources
- Resource group in West Europe.
- ACA environment (VNet‑integrated).
- PostgreSQL Flexible Server (VNet‑integrated), database `develop`.
- Storage account with Azure Files share for ingest artifacts.
- Key Vault for secrets.

3) Configure Container Apps
- Create apps for `reverseproxy` (public), `agentic-analysis`, `ingest-service`, `backend` (internal).
- Set environment variables via Key Vault references.
- Mount Azure Files to `ingest-service` at `/app/data`.
- Health probes for `/health` on agent/ingest and root on proxy.

4) Routing
- `reverseproxy` upstreams:
  - `/` → frontend
  - `/agent/` → agentic-analysis
  - `/ingest/` → ingest-service
- Optionally expose backend routes later when needed.

5) TLS and domain
- Map your custom domain to the ACA‑managed endpoint.
- Provision managed certs; enforce HTTPS redirect.

6) Scaling and limits
- Configure autoscale: min=0, max=3, trigger on HTTP RPS/CPU.
- Set CPU/memory small (e.g., 0.25–0.5 vCPU, 0.5–1 GiB) and adjust from metrics.

### Notes for production hardening
- Replace on‑disk session store with a managed DB/Redis.
- Add authentication/authorization (e.g., AAD / OpenID Connect).
- Introduce structured logging + tracing to Log Analytics.
- Add backup/DR policies for PostgreSQL and Storage.

## Data location and processing (EU)
- All compute (Container Apps), PostgreSQL, ACR, and Storage are deployed in EU regions (West Europe or North Europe).
- Azure OpenAI is deployed in an EU region and referenced by the agent service via EU endpoints only.
- VNet integration ensures service ↔ database traffic stays private within the EU region.
- Raw files reside on Azure Files in the same region; optional archival to Blob in the same region.

## Compliance checklist (DigiEduHack)
- EU region documented for every cloud resource (ACA, PostgreSQL, Storage, ACR, Azure OpenAI).
- No public AI ingestion of raw datasets; the agent only receives anonymized/aggregated prompts.
- Secrets in Key Vault; only reverse proxy has public ingress; VNet integration end‑to‑end.
- Data processing location is EU; data does not leave the EU.
- Monthly cost estimate included in `README.md` and sizing guidance here.

### Red flags avoided
- Not using public OpenAI endpoints outside the EU.
- Architecture does not route educational data to US services.
- Region and data location documented explicitly above.
