# QuantCore AI — Automated Trading Platform

Institutional-grade automated trading system combining fundamental and technical analysis with ML-driven signal generation.

## Architecture

```
quantcore/
├── backend/           # FastAPI + Python trading engine
│   ├── app/
│   │   ├── core/      # Config, DB, Security
│   │   ├── models/    # SQLAlchemy ORM (User, Account, Trade, Signal)
│   │   ├── trading/   # State machine, Controller, Risk, Execution
│   │   ├── strategies/
│   │   │   ├── fundamental/   # F1-F6 strategies
│   │   │   └── technical/     # T1-T5 strategies
│   │   ├── brokers/   # Alpaca, OANDA, IB adapters
│   │   ├── api/       # FastAPI routers (auth, trading, positions, accounts, reports)
│   │   ├── reports/   # PDF generation (ReportLab + Plotly + Claude API)
│   │   └── tasks/     # Celery tasks (reports, notifications)
│   └── requirements.txt
├── frontend/          # React 18 + TypeScript SPA
│   └── src/
│       ├── screens/   # 9 screens (Login, CreateAccount, Dashboard, etc.)
│       ├── components/
│       │   ├── charts/   # SmartChartCard (TradingView Lightweight Charts)
│       │   ├── trading/  # TradingControlPanel
│       │   └── ui/       # Sidebar
│       ├── store/        # Zustand stores (auth, trading)
│       └── hooks/        # WebSocket, API client
├── infra/             # Prometheus config
├── scripts/           # setup.sh
└── docker-compose.yml # Full stack: Postgres/TimescaleDB, Redis, API, Celery, Frontend, Monitoring
```

## Quick Start

```bash
cd quantcore
./scripts/setup.sh
docker compose up
```

Access points:
- **Dashboard**: http://localhost:5173
- **API + Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001

## Trading State Machine

```
OFFLINE → CONNECTED → ACTIVE → PAUSED / WINDING_DOWN / EMERGENCY
```

- **SOFT STOP**: Blocks new entries, cancels pending orders, manages existing positions to natural close
- **HARD STOP**: Immediate market-close of all positions
- **PAUSE**: Freezes signal scanning only; positions remain active
- **EMERGENCY**: Closes everything, disconnects all brokers, requires manual restart

## Strategies

| ID | Name | Type |
|----|------|------|
| F1 | Earnings Surprise Momentum | Fundamental |
| F2 | Value / DCF Mean Reversion | Fundamental |
| F3 | Macro Economic Calendar | Fundamental |
| F4 | Dividend Capture & Income | Fundamental |
| F5 | Insider Trading Signal Replication | Fundamental |
| F6 | Sentiment & News Flow Alpha | Fundamental |
| T1 | Momentum Breakout | Technical |
| T2 | Mean Reversion Pairs | Technical |
| T3 | Options Theta Decay | Technical |
| T4 | HF Scalping (Forex 1m–5m) | Technical |
| T5 | Macro Trend Following | Technical |

## Risk Framework

| Parameter | Default |
|-----------|---------|
| Max risk per trade | 1% of equity |
| Max daily drawdown | 3% → Auto SOFT STOP |
| Max weekly drawdown | 5% → HARD STOP + 48h review |
| Circuit breaker | -7% single day → Emergency |
| Max open positions | 8 (corr r < 0.75) |
| Position sizing | Half-Kelly Criterion |

## Security

- JWT with 15-min rotating access tokens
- TOTP 2FA mandatory for live accounts
- TLS 1.3 for all broker connections
- AES-256 at-rest encryption
- All API keys via HashiCorp Vault / AWS Secrets Manager (never hardcoded)

## Production Checklist

- [ ] Paper trade every strategy ≥30 days before live
- [ ] Run ≥1,000 Monte Carlo simulations per strategy
- [ ] Walk-forward backtest ≥3 years of data
- [ ] Co-locate on Equinix NY4/NY5 (US) or LD4 (Forex/Europe)
- [ ] Configure PagerDuty for circuit breaker alerts
- [ ] Replace `.env` with HashiCorp Vault / AWS Secrets Manager
- [ ] Enable immutable audit logs (PostgreSQL + S3 archive)
