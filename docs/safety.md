# Safety & Guardrails — Trader

Loops amplify judgment — good and bad. Minimum bar for any loop that touches code or external systems.

## Path Denylist (never auto-edit)

```
.env
.env.*
**/secrets/**
**/credentials/**
**/*_key*
**/*_secret*
**/*api*key*
auth/**
payments/**
billing/**
wallet/**
exchange/**
**/keys/**
.terraform/**
k8s/production/**
**/migrations/**
```

Trading-specific: exchange API keys, wallet seeds, broker credentials, live order configs — **human only**.

## Auto-Merge Policy

**Default: no auto-merge.**

| Allowed (L2+ only, after checklist) | Not allowed |
|-------------------------------------|-------------|
| Typo in comment/docs | Behavior / strategy changes |
| Lint auto-fix in tests only | Dependency major bumps |
| Import ordering | Lockfile without human |
| Config in allowlisted `docs/` | Any denylist path |
| — | Live trading parameters |

## MCP / Connector Least Privilege

| Connector | Read | Write |
|-----------|------|-------|
| GitHub | issues, PRs, checks | comment, label (not merge) |
| Slack / chat | history | `#loop-escalations` only |
| Exchange / broker APIs | — | **never from loops** |
| Database | — | no production write from loops |

## Human Gates (required)

- Security, authentication, authorization  
- Payments, billing, PII  
- Infrastructure / prod deploy  
- Dependency majors / high-sev CVEs  
- Changes >10 files  
- Third failed attempt on same item  
- Anything that can place, cancel, or size live orders  

## Secrets in prompts & logs

- Never paste API keys into scheduler prompts  
- Redact secrets before writing state  
- State files may be committed — **no credentials in `STATE.md` or `*-state.md`**

## Flake & test safety

- Do not disable tests to make CI green  
- Do not raise timeouts without root-cause note  
- Quarantine flakes only with human approval  

## Incident response

1. Pause all loops (`loop-pause-all`)  
2. Revert bad merge if any  
3. Log in `loop-run-log.md` + High Priority in `STATE.md`  
4. Tighten verifier / shrink scope before restart  

## Pre-flight before L3

- [ ] Denylist in skills and `loop-constraints.md`  
- [ ] Auto-merge off  
- [ ] Connector scopes reviewed  
- [ ] Human gates in `LOOP.md`  
- [ ] Kill switch known  
- [ ] `loop-budget.md` + `loop-run-log.md` in use  
- [ ] Proven L1/L2 runs committed  

Runtime rules: `loop-constraints.md` (binding for every run).
