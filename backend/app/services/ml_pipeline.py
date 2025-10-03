"""
ML Training Pipeline for Backtesting
Feature engineering, model training, and inference
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog
import joblib
from pathlib import Path

logger = structlog.get_logger()

# Try to import ML libraries (graceful degradation if not available)
try:
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. ML features will be limited.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False


class MLPipeline:
    """Machine learning pipeline for strategy signals"""
    
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def engineer_features(
        self,
        ohlcv: pd.DataFrame,
        feature_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Engineer features from OHLCV data
        
        Args:
            ohlcv: OHLCV DataFrame with columns [open, high, low, close, volume]
            feature_config: Configuration for feature engineering
            
        Returns:
            DataFrame with engineered features
        """
        
        features = pd.DataFrame(index=ohlcv.index)
        
        # Price features
        features['returns'] = ohlcv['close'].pct_change()
        features['log_returns'] = np.log(ohlcv['close'] / ohlcv['close'].shift(1))
        
        # Lagged returns
        for lag in [1, 2, 3, 5, 10]:
            features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
        
        # Rolling statistics
        for window in [5, 10, 20, 50]:
            features[f'sma_{window}'] = ohlcv['close'].rolling(window).mean()
            features[f'std_{window}'] = ohlcv['close'].rolling(window).std()
            features[f'volume_sma_{window}'] = ohlcv['volume'].rolling(window).mean()
        
        # Price momentum
        features['momentum_5'] = ohlcv['close'] / ohlcv['close'].shift(5) - 1
        features['momentum_10'] = ohlcv['close'] / ohlcv['close'].shift(10) - 1
        features['momentum_20'] = ohlcv['close'] / ohlcv['close'].shift(20) - 1
        
        # Volume features
        features['volume_change'] = ohlcv['volume'].pct_change()
        features['volume_ratio'] = ohlcv['volume'] / ohlcv['volume'].rolling(20).mean()
        
        # Volatility
        features['realized_vol_5'] = features['returns'].rolling(5).std() * np.sqrt(252)
        features['realized_vol_20'] = features['returns'].rolling(20).std() * np.sqrt(252)
        
        # Range features
        features['high_low_ratio'] = ohlcv['high'] / ohlcv['low']
        features['close_open_ratio'] = ohlcv['close'] / ohlcv['open']
        
        # RSI
        delta = ohlcv['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = ohlcv['close'].ewm(span=12, adjust=False).mean()
        ema_26 = ohlcv['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # Time features
        if isinstance(ohlcv.index, pd.DatetimeIndex):
            features['hour'] = ohlcv.index.hour
            features['day_of_week'] = ohlcv.index.dayofweek
            features['day_of_month'] = ohlcv.index.day
        
        return features
    
    def create_labels(
        self,
        ohlcv: pd.DataFrame,
        label_config: Dict[str, Any]
    ) -> pd.Series:
        """
        Create labels for training
        
        Args:
            ohlcv: OHLCV DataFrame
            label_config: Label configuration
            
        Returns:
            Series of labels (0 or 1 for classification)
        """
        
        label_type = label_config.get('type', 'next_bar_sign')
        
        if label_type == 'next_bar_sign':
            # Label: 1 if next bar is up, 0 if down
            next_returns = ohlcv['close'].pct_change().shift(-1)
            labels = (next_returns > 0).astype(int)
        
        elif label_type == 'threshold':
            # Label: 1 if next return exceeds threshold
            threshold = label_config.get('threshold', 0.01)
            next_returns = ohlcv['close'].pct_change().shift(-1)
            labels = (next_returns > threshold).astype(int)
        
        elif label_type == 'triple_barrier':
            # Triple barrier method (profit take, stop loss, max holding)
            profit_take = label_config.get('profit_take', 0.02)
            stop_loss = label_config.get('stop_loss', -0.01)
            max_hold = label_config.get('max_hold', 48)
            
            labels = pd.Series(0, index=ohlcv.index)
            
            for i in range(len(ohlcv) - max_hold):
                entry_price = ohlcv.iloc[i]['close']
                
                for j in range(1, max_hold + 1):
                    if i + j >= len(ohlcv):
                        break
                    
                    current_price = ohlcv.iloc[i + j]['close']
                    ret = (current_price - entry_price) / entry_price
                    
                    if ret >= profit_take:
                        labels.iloc[i] = 1
                        break
                    elif ret <= stop_loss:
                        labels.iloc[i] = 0
                        break
        
        else:
            raise ValueError(f"Unknown label type: {label_type}")
        
        return labels
    
    def train_model(
        self,
        features: pd.DataFrame,
        labels: pd.Series,
        model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Train ML model
        
        Args:
            features: Feature DataFrame
            labels: Target labels
            model_config: Model configuration
            
        Returns:
            Dict with model, metrics, and metadata
        """
        
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not available")
        
        # Clean data
        data = features.join(labels.rename('target')).dropna()
        X = data.drop('target', axis=1)
        y = data['target']
        
        # Train/test split
        test_size = model_config.get('test_size', 0.2)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Select model type
        model_type = model_config.get('model_type', 'random_forest')
        
        if model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 10),
                random_state=42
            )
        
        elif model_type == 'gradient_boosting':
            model = GradientBoostingClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 5),
                learning_rate=model_config.get('learning_rate', 0.1),
                random_state=42
            )
        
        elif model_type == 'xgboost' and XGBOOST_AVAILABLE:
            model = xgb.XGBClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 5),
                learning_rate=model_config.get('learning_rate', 0.1),
                random_state=42
            )
        
        elif model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            model = lgb.LGBMClassifier(
                n_estimators=model_config.get('n_estimators', 100),
                max_depth=model_config.get('max_depth', 5),
                learning_rate=model_config.get('learning_rate', 0.1),
                random_state=42
            )
        
        else:
            raise ValueError(f"Unknown or unavailable model type: {model_type}")
        
        # Train
        logger.info(f"Training {model_type} on {len(X_train)} samples")
        model.fit(X_train, y_train)
        
        # Evaluate
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)
        
        try:
            y_train_proba = model.predict_proba(X_train)[:, 1]
            y_test_proba = model.predict_proba(X_test)[:, 1]
            train_auc = roc_auc_score(y_train, y_train_proba)
            test_auc = roc_auc_score(y_test, y_test_proba)
        except:
            train_auc = test_auc = None
        
        # Feature importances
        if hasattr(model, 'feature_importances_'):
            importances = dict(zip(X.columns, model.feature_importances_))
            importances = {k: float(v) for k, v in sorted(importances.items(), key=lambda x: -x[1])}
        else:
            importances = {}
        
        metrics = {
            'train': {
                'accuracy': float(train_acc),
                'auc': float(train_auc) if train_auc else None
            },
            'test': {
                'accuracy': float(test_acc),
                'auc': float(test_auc) if test_auc else None
            }
        }
        
        logger.info(f"Model trained - Test Acc: {test_acc:.3f}, Test AUC: {test_auc:.3f if test_auc else 'N/A'}")
        
        return {
            'model': model,
            'metrics': metrics,
            'feature_importances': importances,
            'features': list(X.columns),
            'trained_at': datetime.utcnow().isoformat()
        }
    
    def save_model(self, model_data: Dict[str, Any], model_id: str) -> Path:
        """Save trained model to disk"""
        
        model_path = self.workspace_dir / f"{model_id}.joblib"
        joblib.dump(model_data, model_path)
        
        logger.info(f"Model saved to {model_path}")
        
        return model_path
    
    def load_model(self, model_id: str) -> Dict[str, Any]:
        """Load trained model from disk"""
        
        model_path = self.workspace_dir / f"{model_id}.joblib"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        model_data = joblib.load(model_path)
        
        logger.info(f"Model loaded from {model_path}")
        
        return model_data
    
    def predict(
        self,
        model_data: Dict[str, Any],
        features: pd.DataFrame
    ) -> np.ndarray:
        """Make predictions with trained model"""
        
        model = model_data['model']
        required_features = model_data['features']
        
        # Ensure features match training
        missing = set(required_features) - set(features.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        X = features[required_features].fillna(0)
        
        try:
            predictions = model.predict_proba(X)[:, 1]
        except:
            predictions = model.predict(X)
        
        return predictions

