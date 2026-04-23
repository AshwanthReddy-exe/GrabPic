# GrabPic Deployment

## Requirements

### System

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 50 GB | 100+ GB SSD |
| OS | Linux/macOS/Windows | Ubuntu 22.04 LTS |

### Software
- Docker Engine 24.0+
- Docker Compose 2.20+
- Git

### Azure
- Azure subscription
- Resource group
- Storage account with Blob Storage

## Local development

```bash
git clone <repository-url>
cd grabpic
```

Create `.env`:

```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_CONTAINER_NAME=events
USE_BLOB_STORAGE=true
IMAGE_TOKEN_SECRET=your-secret-key-min-32-characters-long
EVENT_EXPIRY_HOURS=10
AI_PUBLIC_BASE_URL=http://localhost:8000
```

Start everything:

```bash
docker-compose up --build
```

Local URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8080`
- AI docs: `http://localhost:8000/docs`

### Run services separately

Frontend:
```bash
cd grabpic-frontend
npm install
npm run dev
```

Backend:
```bash
cd backend
./gradlew bootRun
```

AI service:
```bash
cd ai-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Production

Use production values:

```bash
AZURE_STORAGE_CONNECTION_STRING=<production-connection-string>
AZURE_CONTAINER_NAME=events-prod
USE_BLOB_STORAGE=true
IMAGE_TOKEN_SECRET=<generate-strong-secret>
EVENT_EXPIRY_HOURS=48
AI_PUBLIC_BASE_URL=https://ai.yourdomain.com
```

Start:

```bash
docker-compose -f docker-compose.yml up -d
```

Health checks:

```bash
curl http://localhost:5173
curl http://localhost:8080/actuator/health
curl http://localhost:8000/docs
```

## Azure setup

1. Create a storage account.
2. Use a private container named `events`.
3. Copy the storage connection string.
4. Optionally create a stored access policy for SAS control.

Example:

```bash
az storage container policy create \
  --container-name events \
  --name grabpic-policy \
  --account-name grabpicstorage \
  --expiry $(date -u -d "1 year" '+%Y-%m-%dT%H:%MZ') \
  --permissions rlw
```

## Reverse proxy

Use Nginx in production:
- `/` → frontend
- `/events/` → backend
- `/ai/` → AI service (internal only)
- `client_max_body_size 100M`

Enable with `nginx -t` and restart Nginx after adding the site.

## SSL/TLS

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo certbot renew --dry-run
```

## Monitoring

- `docker stats`
- `docker-compose logs -f backend`
- `docker-compose logs -f ai-service`

Suggested log rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

AI health response:

```json
{ "status": "healthy", "version": "1.0.0" }
```

## Backup and recovery

- Enable blob soft delete/versioning.
- Back up `/app/data` from the AI service.
- Compress backups after export.

## Troubleshooting

### AI service OOM
- Raise container memory limits.

### Blob upload failures
- Check the connection string.
- Verify Azure access with `az storage blob list`.

### FAISS index corruption
- Delete the event index and re-upload photos.

### Rate limiting
- Reduce concurrent requests.
- Adjust the limiter in `app/core/limiter.py` if needed.

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security checklist

- Change `IMAGE_TOKEN_SECRET`
- Enable blob soft delete
- Use HTTPS only
- Monitor logs
- Back up regularly
- Rotate access keys
- Review Azure recommendations

## Maintenance

| Task | Frequency | Command |
|---|---|---|
| Update images | Weekly | `docker-compose pull && docker-compose up -d` |
| Review logs | Daily | `docker-compose logs` |
| Backup data | Daily | Backup script |
| Rotate secrets | Quarterly | Update `.env` |
| Update dependencies | Monthly | Check for CVEs |

Zero-downtime path: scale up new containers, wait for health checks, then scale back to one replica.
