# Identity Platform — AWS CDK (scaffold)

**Status: scaffold only — do not deploy to a real account yet.**

Local development still uses Docker Compose (Postgres + Redis) and runs the API/web/demo on the host. This package sketches the future AWS layout.

## Intended architecture

```text
Internet
   │
   ├─ CloudFront ──► S3 (apps/web static; optional apps/demo)
   │
   └─ ALB (HTTPS) ──► ECS Fargate (FastAPI)
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
         RDS Postgres           ElastiCache Redis
         (users, sessions,      (sid hot path, WebAuthn
          OAuth clients,         challenges, OAuth codes)
          audit, tokens)
```

| Stack | File | Future resources |
|-------|------|------------------|
| `IdentityNetwork` | `lib/network-stack.ts` | VPC, subnets, security groups |
| `IdentityData` | `lib/data-stack.ts` | RDS PostgreSQL, ElastiCache Redis |
| `IdentityApi` | `lib/api-stack.ts` | ECS/Fargate, ALB, task secrets/env |
| `IdentityFrontend` | `lib/frontend-stack.ts` | S3 + CloudFront for Vite apps |

## Commands (local synth only)

```bash
cd infra
npm install
npx cdk synth
```

`cdk deploy` is out of scope until stacks create real resources and env/secrets are designed (cookie domain, WebAuthn RP ID, CORS, `FRONTEND_URL`).

## Mapping from local env

| Local (Compose / `.env`) | AWS target (later) |
|--------------------------|--------------------|
| `DATABASE_URL` → Compose Postgres | RDS endpoint + Secrets Manager |
| `REDIS_URL` → Compose Redis | ElastiCache endpoint |
| API `:8000` | ALB → Fargate |
| Web `:5173` / Demo `:5174` | CloudFront (+ custom domains) |
| `CORS_ORIGINS` / `WEBAUTHN_*` | Production origins / RP ID |

## Out of scope (for now)

- Deployable networking/compute
- CI/CD deploy workflows
- Custom domains / ACM certificates
- WAF, multi-region, cost optimization
