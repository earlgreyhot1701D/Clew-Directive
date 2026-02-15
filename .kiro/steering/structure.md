# File Structure Rules — Clew Directive

## Layout
```
clew-directive/
├── .kiro/steering/          # Product, tech, structure context
├── .kiro/hooks/             # Dev-time automation (test, security, cost, docs)
├── .kiro/specs/             # Kiro-generated specs
├── backend/agents/          # Strands agent definitions
├── backend/tools/           # Strands tools (invoked by agents)
├── backend/curator/         # Scheduled freshness Lambda
├── backend/interfaces/      # Abstraction layer for future swaps
├── backend/config/          # Centralized configuration
├── backend/templates/       # Jinja2 HTML templates for PDF
├── backend/tests/           # QA-First test suite with mocks/
├── frontend/src/app/        # Next.js App Router
├── frontend/src/components/ # React terminal UI components
├── frontend/src/styles/     # CSS with WCAG 2.1 AA compliance
├── infrastructure/lib/      # CDK stack definitions
├── infrastructure/bin/      # CDK app entry
├── data/                    # directory.json (curated resources)
├── docs/                    # accessibility.md, etc.
```

## Rules
1. One file, one job. No cross-domain files.
2. Dependencies flow one direction: orchestrator → agents → tools → interfaces.
3. Interface contracts are explicit with type hints and docstrings.
4. Every source file has a corresponding test file.
5. Config is centralized in config/settings.py — never hardcoded.
6. Frontend communicates with backend only through API Gateway.
7. No PII in logs, storage, metrics, or temporary files.
8. All UI components must meet WCAG 2.1 AA standards.
