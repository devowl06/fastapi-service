To setup this service, add an env file:

### .env file

R2_ENDPOINT_URL=https://your-r2-endpoint
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=your-bucket-name
R2_TOKEN_VALUE=your-token-value

---

### Pre-requisites:
- python3.12.11 installed
- use linux

---

### Setup repo:
- python -m venv .venv
- source .venv/bin/activate
- pip install -r requirements.txt
- update the envs
- uvicorn main:app --port 8000 --reload

---
