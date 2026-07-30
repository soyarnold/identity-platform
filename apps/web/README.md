# Identity Platform — auth dashboard

Vite + React app for first-party register/login (password + passkeys), passkey management, and session revoke.

## Run

```bash
# API must be up on :8000 with Compose + migrations
cd apps/web
cp .env.example .env   # if needed
npm install
npm run dev
```

Open http://localhost:5173

## Routes

- `/login`, `/register`
- `/` overview (authed)
- `/passkeys`, `/sessions`
