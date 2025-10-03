# TradeQuest - Path to Profitability Platform (P3)

> **No gurus. No signals. Just your data, real analysis, and disciplined growth.**

TradeQuest is a comprehensive trading platform designed for young traders who want data-driven insights, not hype. Connect your brokers, journal your trades, backtest strategies, and get AI coaching that actually helps you improve.

## 🚀 Features

### Core Functionality
- **Broker Integration**: Read-only connections to Kraken and Coinbase Advanced
- **Smart Journaling**: Auto-import trades via CSV, add notes, tags, and screenshots
- **Market Data**: Real-time OHLCV data with trade context analysis
- **Backtesting Engine**: SMA cross, RSI mean-revert, and ATR trailing stop strategies
- **AI Coach**: Concise, actionable feedback on your trades with market context
- **Analytics**: Win rate, P&L, drawdown, and performance insights

### AI-Powered Tools
- Trade execution quality analysis
- Market context around your trades
- Strategy backtesting with Monte Carlo simulation
- Session performance coaching
- Risk management insights

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Authentication**: Magic link login with JWT tokens
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for market data and job queues
- **Broker APIs**: CCXT integration for Kraken and Coinbase
- **AI Services**: Custom coaching engine with market analysis

### Frontend (Next.js + React)
- **Dashboard**: Portfolio manager style with charts and metrics
- **Chat Interface**: AI coach with tool calling capabilities
- **Journal**: Trade analysis and CSV import
- **Backtesting**: Strategy testing with visual results

### Infrastructure
- **Docker**: Containerized development and deployment
- **Database**: PostgreSQL 15 with proper indexing
- **Caching**: Redis 7 for performance
- **Security**: Encrypted API keys, rate limiting, CORS

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TradeQuest
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Development Setup

1. **Backend Development**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend Development**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/magic-link` - Send magic link
- `POST /api/v1/auth/consume` - Consume magic link token
- `GET /api/v1/auth/me` - Get current user

### Broker Integration
- `POST /api/v1/broker/connect/{venue}` - Connect broker
- `GET /api/v1/broker/fills` - Get trade fills
- `GET /api/v1/broker/positions` - Get positions
- `POST /api/v1/broker/sync` - Manual sync

### Market Data
- `GET /api/v1/market/ohlcv` - Get OHLCV data
- `POST /api/v1/market/context` - Get trade context
- `GET /api/v1/market/symbols` - Available symbols

### Journal & Analytics
- `POST /api/v1/journal/ingest_csv` - Import CSV trades
- `GET /api/v1/journal/trades` - Get trades
- `POST /api/v1/journal/entry` - Create journal entry
- `GET /api/v1/journal/analytics` - Get KPIs

### Backtesting
- `POST /api/v1/backtest/run` - Run backtest
- `POST /api/v1/backtest/quick` - Quick backtest
- `GET /api/v1/backtest/strategies` - Get strategies
- `GET /api/v1/backtest/templates` - Strategy templates

### AI Tools
- `GET /api/v1/ai/tools/get_ohlcv` - AI tool: OHLCV data
- `GET /api/v1/ai/tools/get_trades` - AI tool: Recent trades
- `POST /api/v1/ai/tools/get_trade_context` - AI tool: Trade context
- `POST /api/v1/ai/tools/backtest_quick` - AI tool: Quick backtest
- `POST /api/v1/ai/tools/coach_trade` - AI tool: Trade coaching
- `POST /api/v1/ai/tools/coach_session` - AI tool: Session coaching

## 🎯 Strategy Templates

### SMA Crossover
```json
{
  "type": "sma_cross",
  "fast_period": 10,
  "slow_period": 20,
  "position_size": 1.0
}
```

### RSI Mean Reversion
```json
{
  "type": "rsi_revert",
  "rsi_period": 14,
  "oversold": 30,
  "overbought": 70,
  "position_size": 1.0
}
```

### ATR Trailing Stop
```json
{
  "type": "atr_trail",
  "atr_period": 14,
  "atr_multiplier": 2.0,
  "position_size": 1.0
}
```

## 📈 Data Model

### Core Tables
- `users` - User accounts and authentication
- `subscriptions` - Billing and plan information
- `api_keys` - Encrypted broker API credentials
- `trades` - Normalized trade data
- `journal_entries` - Trade notes and analysis
- `strategies` - Saved trading strategies
- `backtests` - Backtest results and metrics
- `daily_metrics` - Cached performance KPIs

### Trade Schema
```json
{
  "id": "uuid",
  "account": "spot",
  "venue": "KRAKEN",
  "symbol": "BTC/USDT",
  "side": "buy",
  "qty": 0.25,
  "avg_price": 60999.5,
  "fees": 3.12,
  "pnl": -42.5,
  "submitted_at": "2025-09-24T14:31:00Z",
  "filled_at": "2025-09-24T14:31:05Z",
  "order_ref": "A1B2C3"
}
```

## 🔒 Security

- **API Keys**: AES-GCM encrypted at rest
- **Authentication**: JWT tokens with short expiration
- **Rate Limiting**: Per-user request limits
- **CORS**: Configured for frontend domains
- **Input Validation**: Pydantic schemas for all endpoints

## 🚀 Deployment

### Production Setup
1. **Environment Variables**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:port/db
   REDIS_URL=redis://host:port
   JWT_SECRET=your-secret-key
   STRIPE_SECRET_KEY=sk_live_...
   ```

2. **Database Migration**
   ```bash
   alembic upgrade head
   ```

3. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 📝 CSV Import Formats

### Supported Brokers
- **Binance**: Trade history export
- **Kraken**: Trades CSV
- **Coinbase Pro**: Fills export
- **Bybit**: Trade history
- **Generic**: Auto-detection of common columns

### Example CSV Headers
```csv
Date,Symbol,Side,Size,Price,Fee,Order ID
2024-01-01,BTC/USDT,BUY,0.1,45000,2.25,12345
```

## 🤖 AI Coach Examples

### Trade Analysis
```
User: "Analyze my last trade"
AI: "You bought BTC at $45,000 into a strong uptrend. Execution was excellent - you got within 0.5% of the candle low. However, you're buying into resistance at the daily high. Consider waiting for a pullback or using a smaller position size."
```

### Strategy Backtesting
```
User: "Backtest SMA cross on BTC"
AI: "I'll test a 10/20 SMA crossover on BTC 1m data. Running backtest... Results: 45% win rate, 1.2 Sharpe ratio, $2,340 total return over 1000 trades. The strategy works well in trending markets but struggles in sideways action."
```

## 📊 Performance Metrics

### Key KPIs
- **Win Rate**: Percentage of profitable trades
- **Average R**: Risk/reward ratio
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss
- **Consistency Score**: Discipline + Risk hygiene + Expectancy

## 🛠️ Development

### Adding New Strategies
1. Implement strategy logic in `BacktestEngine`
2. Add strategy template to `/backtest/strategies/templates`
3. Update frontend strategy selector

### Adding New Brokers
1. Add broker service in `BrokerService`
2. Update CSV parser for broker format
3. Add broker to supported venues list

### AI Coach Customization
1. Modify prompts in `AICoach`
2. Add new analysis methods
3. Update tool endpoints

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**Educational Only**: This platform is for educational purposes only and does not constitute financial advice. Trading involves risk of loss. Users should conduct their own research and consider their risk tolerance before trading.

**Age Restriction**: This platform is intended for users 16 years and older. Users under 18 should have parental guidance.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support, email support@tradequest.com or join our Discord community.

---

**TradeQuest** - Where data meets discipline. 🚀
