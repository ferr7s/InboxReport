# InboxReport

Minimal Gmail daily digest:

```bash
cp .env.example .env
mkdir -p data
# put Google OAuth client JSON at data/credentials.json
docker build -t inbox-report .
docker run --rm -it --env-file .env -p 8080:8080 -v "$PWD/data:/data" inbox-report
```

The first run prints a Google OAuth URL. Open it, approve Gmail read-only access,
and the token is saved at `data/token.json`.
