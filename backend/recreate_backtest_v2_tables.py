"""
Recreate Backtesting v2 tables (drop and recreate)
Use with caution - this will delete all existing backtest data!
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models.backtest_v2 import (
    StrategyGraph,
    BacktestRun,
    BacktestArtifact,
    MLModel,
    ParameterSweepResult,
    DataCache,
    BacktestTemplate
)
import structlog
from app.models.user import User

logger = structlog.get_logger()

def recreate_tables():
    """Drop and recreate all backtesting v2 tables"""
    
    try:
        logger.info("Connecting to database...")
        engine = create_engine(str(settings.DATABASE_URL))
        
        logger.info("[SETUP] Dropping existing Backtesting v2 tables...")
        
        # Drop tables in reverse order (respecting foreign keys)
        tables_to_drop = [
            "parameter_sweep_results",
            "backtest_artifacts",
            "backtest_runs",
            "ml_models",
            "data_cache",
            "backtest_templates",
            "strategy_graphs"
        ]
        
        with engine.connect() as conn:
            for table_name in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    conn.commit()
                    logger.info(f"  Dropped table: {table_name}")
                except Exception as e:
                    logger.warning(f"  Could not drop {table_name}: {e}")
        
        logger.info("[SETUP] Creating Backtesting v2 tables...")
        
        # Create tables
        tables_to_create = [
            StrategyGraph.__table__,
            BacktestRun.__table__,
            BacktestArtifact.__table__,
            MLModel.__table__,
            ParameterSweepResult.__table__,
            DataCache.__table__,
            BacktestTemplate.__table__
        ]
        
        for table in tables_to_create:
            logger.info(f"  Creating table: {table.name}")
        
        Base.metadata.create_all(bind=engine, tables=tables_to_create)
        
        logger.info("[SUCCESS] All tables created successfully!")
        
        # Insert template strategies
        logger.info("[SETUP] Inserting template strategies...")
        
        with engine.connect() as conn:
            try:
                conn.execute(text("""
                    INSERT INTO backtest_templates (
                        id, name, description, category, difficulty, 
                        graph_template, example_config, usage_count,
                        is_official, is_featured
                    )
                    VALUES 
                    (
                        'template_rsi_mean_reversion',
                        'RSI Mean Reversion',
                        'Classic mean reversion strategy using RSI oversold/overbought levels. Buy when RSI < 30, sell when RSI > 70.',
                        'mean_reversion',
                        'beginner',
                        '{"nodes": [{"id": "data1", "type": "data.loader", "params": {"symbol": "BTC/USDT", "timeframe": "1m"}}, {"id": "rsi1", "type": "feature.rsi", "params": {"period": 14}}, {"id": "sig1", "type": "signal.threshold", "params": {"feature": "rsi", "upper_threshold": 70, "lower_threshold": 30}}, {"id": "size1", "type": "sizing.fixed", "params": {"position_size": 1.0}}, {"id": "exec1", "type": "exec.market", "params": {"slippage_bps": 5, "fee_bps": 2}}]}',
                        '{"symbol": "BTC/USDT", "timeframe": "1m", "start_date": "2024-01-01", "end_date": "2024-03-31"}',
                        0,
                        1,
                        1
                    ),
                    (
                        'template_sma_crossover',
                        'SMA Crossover',
                        'Trend following strategy using fast and slow moving average crossovers',
                        'trend_following',
                        'beginner',
                        '{"nodes": [{"id": "data1", "type": "data.loader", "params": {"symbol": "ETH/USDT", "timeframe": "1h"}}, {"id": "ema_fast", "type": "feature.ema", "params": {"period": 10, "source": "close", "output_name": "ema_fast"}}, {"id": "ema_slow", "type": "feature.ema", "params": {"period": 30, "source": "close", "output_name": "ema_slow"}}, {"id": "sig1", "type": "signal.crossover", "params": {"fast_feature": "ema_fast", "slow_feature": "ema_slow"}}, {"id": "exec1", "type": "exec.market", "params": {"slippage_bps": 5, "fee_bps": 2}}]}',
                        '{"symbol": "BTC/USDT", "timeframe": "1h", "start_date": "2024-01-01", "end_date": "2024-12-31"}',
                        0,
                        1,
                        1
                    )
                """))
                conn.commit()
                
                logger.info("[SUCCESS] Templates inserted!")
            except Exception as e:
                logger.warning(f"[WARNING] Could not insert templates: {e}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("[COMPLETE] Backtesting v2 tables recreated!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Backend should auto-reload")
        logger.info("  2. Refresh frontend: http://localhost:3000/backtest-v2")
        logger.info("  3. Start building strategies!")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to recreate tables: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = recreate_tables()
    if not success:
        exit(1)

