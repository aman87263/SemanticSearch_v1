# SemanticSearch_v1 — Oracle Cloud Deployment Runbook

## 1. Scope and final architecture

This runbook records the Oracle Cloud deployment from VM creation through the final successful HTTPS deployment, including the debugging steps and why they mattered.

Final architecture:

```text
Internet
  |
  v
capriman27.duckdns.org
  |
  v
Nginx :80/:443
  |----------------------|
  v                      v
React frontend :8080   FastAPI backend :8000
                           |
                    +------+------+
                    |             |
                    v             v
              Supabase DB     Groq LLM
              + pgvector
```

The final verified flow was: HTTPS -> React UI -> FastAPI -> document upload/processing -> Supabase -> search/RAG -> Groq answer.

---

## 2. Create the Oracle Cloud VM

### 2.1 VM configuration

Create an Always Free eligible OCI Compute instance using:

- Ubuntu 24.04 Canonical
- `VM.Standard.A1.Flex`
- ARM64
- 2 OCPU
- 12 GB RAM
- 100 GB boot volume

The deployed VM received public IP `144.24.124.40`.

### 2.2 Why this mattered

The application needed a persistent cloud host capable of running the frontend and backend containers. The Ampere A1 shape also required checking ARM64 compatibility.

### 2.3 Verify architecture

```bash
uname -m
```

Expected:

```text
aarch64
```

---

## 3. Configure OCI networking

### 3.1 Create the VCN

Use:

```text
semanticsearch-vcn
```

### 3.2 Create the public subnet

Use:

```text
semanticsearch-public
```

### 3.3 Create an Internet Gateway

Use:

```text
semanticsearch-igw
```

### 3.4 Configure the route table

The route table was initially missing a usable Internet route.

Add:

```text
Destination: 0.0.0.0/0
Target: Internet Gateway
Gateway: semanticsearch-igw
```

### 3.5 Why this mattered

A public IP does not by itself guarantee Internet connectivity. The subnet must have a default route through an Internet Gateway.

---

## 4. Configure OCI Security List

Add ingress rules for:

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| 22 | TCP | `0.0.0.0/0` | SSH |
| 80 | TCP | `0.0.0.0/0` | HTTP / Let's Encrypt |
| 443 | TCP | `0.0.0.0/0` | HTTPS |

SSH initially failed because TCP 22 was not allowed. Adding port 22 fixed SSH access.

There were two SSH rules eventually; the duplicate was harmless but unnecessary.

### Why this mattered

OCI Security Lists are one firewall layer. The Ubuntu VM has its own firewall as well, so both layers must allow required traffic.

---

## 5. Connect and prepare Ubuntu

Connect using the SSH private key created for the VM. Never put that private key in Git.

Install Git:

```bash
sudo apt update
sudo apt install -y git
```

Install Docker and verify:

```bash
docker --version
```

Clone the repository:

```bash
git clone <repository-url>
cd ~/SemanticSearch_v1
```

### Why this mattered

The production deployment is built from the Git-controlled application source rather than from manual changes made directly inside containers.

---

## 6. Configure production environment variables

Create the VM environment file:

```bash
cd ~/SemanticSearch_v1
nano .env
```

The production environment contains values corresponding to:

```env
APP_ENVIRONMENT=production
DATABASE_URL=<Supabase Session Pooler URI>
GROQ_API_KEY=<Groq API key>
UPLOAD_DIRECTORY=/tmp/uploads
CORS_ORIGINS=<production origin>
VITE_API_BASE_URL=<production API base>
```

Never commit or paste real secrets into documentation.

### Why this mattered

The Oracle deployment uses:

- Supabase PostgreSQL/pgvector instead of local PostgreSQL
- Groq instead of Ollama
- Dockerized frontend/backend

---

## 7. Configure production Docker Compose

The production stack deliberately excludes PostgreSQL and Ollama.

The Compose configuration used:

```yaml
services:

  backend:
    build:
      context: ./backend
    restart: unless-stopped
    environment:
      APP_ENVIRONMENT: production
      DATABASE_URL: ${DATABASE_URL:?Set DATABASE_URL}
      GROQ_API_KEY: ${GROQ_API_KEY:?Set GROQ_API_KEY}
      UPLOAD_DIRECTORY: /tmp/uploads
      CORS_ORIGINS: ${CORS_ORIGINS:?Set CORS_ORIGINS}
    ports:
      - "8000:8000"
    volumes:
      - backend_uploads:/tmp/uploads
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 12

  frontend:
    build:
      context: ./frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  backend_uploads:
```

### Why frontend uses host port 8080

Nginx needs host ports 80 and 443. Therefore the frontend container serves its internal port 80 through host port 8080.

---

## 8. Validate, build, and start containers

Validate the Compose file:

```bash
docker compose --env-file .env -f docker-compose.production.yml config
```

Build:

```bash
docker compose --env-file .env -f docker-compose.production.yml build
```

Start:

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d
```

Check:

```bash
docker compose --env-file .env -f docker-compose.production.yml ps
```

Expected:

```text
backend    Up (healthy)
frontend   Up
```

### Why this mattered

This established that the application could build and run natively on the Oracle ARM64 VM.

---

## 9. Verify backend and frontend locally on the VM

Backend:

```bash
curl http://localhost:8000/api/health
```

Expected:

```json
{"status":"healthy"}
```

Frontend:

```bash
curl -I http://localhost:8080
```

Expected HTTP 200.

### Why this mattered

These tests isolated the containers from OCI, DNS, Nginx, and browser problems.

---

## 10. Install and configure Nginx

Install:

```bash
sudo apt update
sudo apt install -y nginx
```

Create:

```bash
sudo nano /etc/nginx/sites-available/semanticsearch
```

Initial HTTP configuration:

```nginx
server {
    listen 80;
    server_name capriman27.duckdns.org;

    client_max_body_size 50M;

    location = /api {
        proxy_pass http://127.0.0.1:8000/api;
        include proxy_params;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        include proxy_params;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        include proxy_params;
    }
}
```

Validate:

```bash
sudo nginx -t
```

Reload:

```bash
sudo systemctl reload nginx
```

---

## 11. Debug the Nginx port conflict

Nginx initially could not use port 80 because the Docker frontend occupied host port 80.

Change the frontend mapping from:

```yaml
ports:
  - "80:80"
```

to:

```yaml
ports:
  - "8080:80"
```

Then recreate the frontend:

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d --build frontend
```

### Why this mattered

Nginx must own public ports 80/443 for reverse proxying and TLS termination.

---

## 12. Enable the SemanticSearch Nginx site

Create the site symlink:

```bash
sudo ln -s /etc/nginx/sites-available/semanticsearch /etc/nginx/sites-enabled/semanticsearch
```

If it returns:

```text
ln: failed to create symbolic link ... File exists
```

that means the symlink is already present.

Verify:

```bash
ls -la /etc/nginx/sites-enabled/
```

The expected entry is:

```text
semanticsearch -> /etc/nginx/sites-available/semanticsearch
```

Remove the default Nginx site:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Validate:

```bash
sudo nginx -t
```

Confirm the active hostname:

```bash
sudo nginx -T | grep -n "server_name"
```

Expected:

```text
server_name capriman27.duckdns.org;
```

### Why this mattered

The browser initially showed the default Nginx welcome page because the default virtual host was still active.

---

## 13. Debug Ubuntu iptables blocking HTTP

OCI port 80 was open, but public HTTP still failed.

The Ubuntu `iptables` INPUT chain had a final REJECT rule. Port 80 needed an ACCEPT rule before it.

Add:

```bash
sudo iptables -I INPUT 5 -p tcp --dport 80 -m conntrack --ctstate NEW -j ACCEPT
```

Verify:

```bash
sudo iptables -L INPUT -n --line-numbers
```

### Why this mattered

This proved that OCI Security List and Ubuntu `iptables` are separate layers.

The final ordering needed to be conceptually:

```text
ACCEPT established
ACCEPT loopback/required traffic
ACCEPT tcp/22
ACCEPT tcp/80
REJECT all
```

---

## 14. Configure DuckDNS

Use the hostname:

```text
capriman27.duckdns.org
```

Point it to:

```text
144.24.124.40
```

### Why this mattered

A hostname provides a stable production address and is required for the Let's Encrypt certificate.

---

## 15. Verify public HTTP routing

Test:

```bash
curl -I http://capriman27.duckdns.org
```

The result was HTTP 200 from Nginx.

Test the backend through Nginx:

```bash
curl http://capriman27.duckdns.org/api/health
```

Result:

```json
{"status":"healthy"}
```

Test the HTML:

```bash
curl -s http://capriman27.duckdns.org | head -30
```

The response contained the React production bundle.

### Why this mattered

This proved both reverse-proxy paths:

```text
/      -> frontend
/api   -> backend
```

were working.

---

## 16. Diagnose the `crypto.randomUUID()` error

The browser initially displayed:

```text
Uncaught TypeError: crypto.randomUUID is not a function
```

Only a small part of the React UI rendered.

### Root cause

The application was being served over plain HTTP.

`crypto.randomUUID()` is restricted to secure contexts in normal browser use. HTTPS was therefore required for the production site.

### Why this mattered

The React build itself was not fundamentally broken. The browser security context was the cause.

---

## 17. Open HTTPS port 443

Add TCP 443 to the OCI Security List.

Then add the corresponding Ubuntu firewall rule:

```bash
sudo iptables -I INPUT 5 -p tcp --dport 443 -m conntrack --ctstate NEW -j ACCEPT
```

Verify:

```bash
sudo iptables -L INPUT -n --line-numbers
```

Ensure the 443 ACCEPT rule is above the final REJECT.

---

## 18. Verify Certbot

Certbot was already installed:

```bash
certbot --version
```

Result:

```text
certbot 2.9.0
```

---

## 19. Enable Let's Encrypt HTTPS

Run:

```bash
sudo certbot --nginx -d capriman27.duckdns.org
```

Provide a valid email address, accept the Terms of Service, and choose HTTP-to-HTTPS redirect when prompted.

Certbot successfully:

- received the certificate
- deployed it to Nginx
- enabled HTTPS
- configured scheduled automatic renewal

Certificate location:

```text
/etc/letsencrypt/live/capriman27.duckdns.org/
```

Never expose `privkey.pem`.

The issued certificate was valid until December 5, 2026 at the time of deployment.

---

## 20. Verify HTTPS and fix the frontend API URL

Open:

```text
https://capriman27.duckdns.org
```

Hard refresh:

```text
Ctrl + Shift + R
```

The full UI then rendered and the `crypto.randomUUID()` error disappeared.

However, the frontend was still trying to upload to:

```text
http://144.24.124.40:8000/api/documents
```

### Root cause

The frontend `.env` contained:

```env
VITE_API_BASE_URL=http://144.24.124.40:8000/api
```

Vite embeds `VITE_*` values during the frontend build.

### Correct production setting

Change to:

```env
VITE_API_BASE_URL=/api
```

Then rebuild:

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d --build frontend
```

### Why `/api` is preferable

The browser now calls:

```text
https://capriman27.duckdns.org/api/documents
```

and Nginx internally forwards it to:

```text
http://127.0.0.1:8000/api/documents
```

This avoids hard-coding the VM IP and keeps the browser on the same HTTPS origin.

---

## 21. Debug backend logs

Use:

```bash
cd ~/SemanticSearch_v1
docker compose --env-file .env -f docker-compose.production.yml logs -f --tail=100 backend
```

For recent logs:

```bash
docker compose --env-file .env -f docker-compose.production.yml logs --tail=200 backend
```

An initial attempt failed with:

```text
couldn't find env file: /home/ubuntu/.env
```

### Root cause

The command was run from `~/` instead of the repository directory containing `.env`.

### Fix

Run it from:

```text
~/SemanticSearch_v1
```

### Why this mattered

It distinguished an environment-file path problem from an application/container problem.

---

## 22. Debug the transient 504 upload

After correcting the frontend API URL, the upload request correctly became:

```text
https://capriman27.duckdns.org/api/documents
```

One attempt returned:

```text
504 Gateway Timeout
```

### Interpretation

The request had reached the correct Nginx endpoint, but Nginx did not receive a backend response within its proxy timeout.

The upload endpoint performs potentially lengthy work such as:

```text
save PDF
  -> extract
  -> chunk
  -> embed
  -> store
  -> return
```

### Diagnostic action

Watch the backend:

```bash
docker compose --env-file .env -f docker-compose.production.yml logs -f --tail=100 backend
```

Then repeat the upload.

The next attempt succeeded.

### Conclusion

Because the next upload and search completed successfully, the single 504 was treated as transient rather than sufficient evidence for an Nginx or application rewrite.

Do not change proxy timeouts solely because of one isolated occurrence.

---

## 23. Final end-to-end validation

The final successful test verified:

### 23.1 HTTPS

```text
https://capriman27.duckdns.org
```

PASS

### 23.2 Frontend

Full React UI rendered.

PASS

### 23.3 Browser UUID functionality

`crypto.randomUUID()` worked.

PASS

### 23.4 API

```bash
curl https://capriman27.duckdns.org/api/health
```

returned:

```json
{"status":"healthy"}
```

PASS

### 23.5 Document upload

PDF upload succeeded.

PASS

### 23.6 Document processing

Document processing completed.

PASS

### 23.7 Search

Search successfully retrieved document content.

PASS

### 23.8 RAG/LLM

The production retrieval and Groq answer flow succeeded.

PASS

---

# 24. Final deployment architecture

```text
                         INTERNET
                            |
                            v
                 capriman27.duckdns.org
                            |
                            v
                    NGINX :80/:443
                      HTTPS/TLS
                       /                            /                             v          v
             React :8080    FastAPI :8000
                                |
                         +------+------+
                         |             |
                         v             v
                  Supabase DB       Groq LLM
                  + pgvector
```

---

# 25. Useful operational commands

## 25.1 Container status

```bash
cd ~/SemanticSearch_v1
docker compose --env-file .env -f docker-compose.production.yml ps
```

## 25.2 Backend logs

```bash
docker compose --env-file .env -f docker-compose.production.yml logs -f --tail=100 backend
```

## 25.3 Frontend logs

```bash
docker compose --env-file .env -f docker-compose.production.yml logs -f --tail=100 frontend
```

## 25.4 Restart

```bash
docker compose --env-file .env -f docker-compose.production.yml restart
```

## 25.5 Rebuild/redeploy

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d --build
```

## 25.6 Backend health

```bash
curl http://localhost:8000/api/health
```

## 25.7 Public API health

```bash
curl https://capriman27.duckdns.org/api/health
```

## 25.8 Nginx configuration test

```bash
sudo nginx -t
```

## 25.9 Nginx reload

```bash
sudo systemctl reload nginx
```

## 25.10 Listening ports

```bash
sudo ss -lntp
```

## 25.11 Firewall

```bash
sudo iptables -L INPUT -n --line-numbers
```

## 25.12 Certificate status

```bash
sudo certbot certificates
```

## 25.13 Renewal test

```bash
sudo certbot renew --dry-run
```

---

# 26. Production hardening still recommended

These were not required for the successful deployment, but should be completed before considering the infrastructure fully hardened.

## 26.1 Remove public exposure of backend port 8000

Current Compose publishes:

```yaml
ports:
  - "8000:8000"
```

The preferred final architecture is:

```text
Public: 80/443 only
Internal: Nginx -> backend
```

Use an internal Docker network and remove host-level exposure of port 8000.

## 26.2 Persist iptables rules

The 80/443 ACCEPT rules were added at runtime.

Verify persistence across reboot. If using `iptables-persistent`, inspect existing rules before saving so Oracle-specific rules are not unintentionally damaged.

## 26.3 Move PDF storage to Supabase Storage

The current deployment uses:

```text
/tmp/uploads
```

inside a Docker volume.

For durable production object storage, move uploaded PDFs to Supabase Storage.

## 26.4 Make document processing asynchronous

A long-running synchronous upload can cause proxy timeouts.

Preferred pattern:

```text
POST /documents
    |
    +--> save metadata/file
    |
    +--> enqueue processing
    |
    +--> return quickly
             |
             v
       background worker
```

## 26.5 Verify certificate renewal

```bash
sudo certbot renew --dry-run
```

## 26.6 Add observability

Recommended:

- structured logs
- request IDs
- processing status/error states
- application metrics
- database monitoring
- LLM latency/token metrics
- retrieval evaluation
- health/readiness endpoints

---

# 27. Troubleshooting summary

| Symptom | Root cause | Fix |
|---|---|---|
| SSH unavailable | OCI port 22 missing | Add TCP 22 ingress |
| Public traffic unavailable despite public IP | Missing Internet route | Add `0.0.0.0/0 -> Internet Gateway` |
| Port 80 unavailable | Ubuntu iptables final REJECT | Add TCP 80 ACCEPT before REJECT |
| Nginx could not bind port 80 | Frontend Docker container occupied port 80 | Move frontend to host 8080 |
| Nginx welcome page | Default virtual host still enabled | Enable SemanticSearch site and remove default |
| Partial React UI | `crypto.randomUUID()` unavailable over HTTP | Enable HTTPS |
| Frontend calling old IP | Vite API URL baked into build | Set `VITE_API_BASE_URL=/api` and rebuild |
| Docker logs could not find `.env` | Command executed outside repo | Run from `~/SemanticSearch_v1` |
| One upload returned 504 | Long/transient backend processing | Inspect logs and retest before changing architecture |
| Upload and search finally succeeded | Production path validated | Proceed to hardening |

---

# 28. Final deployment status

```text
Oracle VM                         PASS
ARM64 Docker build                PASS
OCI networking                    PASS
SSH                               PASS
OCI port 80                       PASS
OCI port 443                      PASS
Ubuntu iptables                   PASS
Docker Compose                    PASS
FastAPI                           PASS
React frontend                    PASS
Nginx reverse proxy               PASS
DuckDNS                            PASS
Let's Encrypt HTTPS               PASS
crypto.randomUUID                 PASS
Frontend -> API                   PASS
Document upload                   PASS
Document processing               PASS
Search                            PASS
Supabase                          PASS
Groq                              PASS
End-to-end RAG                    PASS
```

The Oracle Cloud deployment is therefore **successfully operational end-to-end**. Secrets and private credentials are intentionally excluded from this document.
