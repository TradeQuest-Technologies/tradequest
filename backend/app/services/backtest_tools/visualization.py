"""
Visualization Tools for Backtest Copilot
Tools for generating charts and visualizations.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import io
import base64
import uuid
from pathlib import Path

import structlog

logger = structlog.get_logger()


class VisualizationTools:
    """Tools for generating charts and visualizations"""
    
    def __init__(self, chart_dir: Path):
        self.chart_dir = chart_dir
        self.chart_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_chart(
        self,
        chart_type: str,
        title: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate a custom chart.
        
        Args:
        - chart_type: 'line', 'bar', 'scatter', 'heatmap'
        - title: Chart title
        - data: Chart data (format depends on chart_type)
        - options: Additional chart options (colors, labels, etc.)
        
        Returns:
        - chart_id: Unique ID for the chart
        - url: URL to access the chart
        - path: File path of saved chart
        """
        chart_id = str(uuid.uuid4())
        options = options or {}
        
        # Create figure
        fig, ax = plt.subplots(figsize=options.get('figsize', (12, 6)))
        
        try:
            if chart_type == 'line':
                self._create_line_chart(ax, data, options)
            elif chart_type == 'bar':
                self._create_bar_chart(ax, data, options)
            elif chart_type == 'scatter':
                self._create_scatter_chart(ax, data, options)
            elif chart_type == 'heatmap':
                self._create_heatmap(ax, data, options)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Set title and labels
            ax.set_title(title, fontsize=14, fontweight='bold')
            if 'xlabel' in options:
                ax.set_xlabel(options['xlabel'])
            if 'ylabel' in options:
                ax.set_ylabel(options['ylabel'])
            
            # Grid
            if options.get('grid', True):
                ax.grid(True, alpha=0.3)
            
            # Legend
            if options.get('legend', True) and chart_type != 'heatmap':
                ax.legend()
            
            # Save chart
            chart_path = self.chart_dir / f"{chart_id}.png"
            plt.tight_layout()
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            return {
                "chart_id": chart_id,
                "url": f"/api/v1/backtest/v2/charts/{chart_id}",
                "path": str(chart_path)
            }
        
        except Exception as e:
            plt.close(fig)
            logger.error(f"Chart generation failed: {e}")
            raise
    
    def _create_line_chart(self, ax, data: Dict[str, Any], options: Dict[str, Any]):
        """Create a line chart"""
        x = data.get('x', [])
        y_data = data.get('y', {})  # Dict of {label: values}
        
        if isinstance(y_data, dict):
            for label, values in y_data.items():
                ax.plot(x, values, label=label, linewidth=2)
        else:
            ax.plot(x, y_data, linewidth=2)
        
        # Format x-axis if timestamps
        if x and isinstance(x[0], (str, datetime)):
            try:
                dates = [datetime.fromisoformat(str(d).replace('Z', '+00:00')) for d in x]
                ax.plot(dates, list(y_data.values())[0] if isinstance(y_data, dict) else y_data)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.xticks(rotation=45)
            except:
                pass
    
    def _create_bar_chart(self, ax, data: Dict[str, Any], options: Dict[str, Any]):
        """Create a bar chart"""
        x = data.get('x', [])
        y = data.get('y', [])
        
        colors = options.get('colors', 'steelblue')
        ax.bar(x, y, color=colors, alpha=0.7)
        
        # Rotate labels if needed
        if len(x) > 10:
            plt.xticks(rotation=45, ha='right')
    
    def _create_scatter_chart(self, ax, data: Dict[str, Any], options: Dict[str, Any]):
        """Create a scatter plot"""
        x = data.get('x', [])
        y = data.get('y', [])
        
        colors = data.get('colors', 'steelblue')
        sizes = data.get('sizes', 50)
        
        ax.scatter(x, y, c=colors, s=sizes, alpha=0.6)
    
    def _create_heatmap(self, ax, data: Dict[str, Any], options: Dict[str, Any]):
        """Create a heatmap"""
        matrix = data.get('matrix', [])
        x_labels = data.get('x_labels', [])
        y_labels = data.get('y_labels', [])
        
        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto')
        
        # Set ticks
        if x_labels:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels)
        
        # Colorbar
        plt.colorbar(im, ax=ax)
    
    def annotate_equity_curve(
        self,
        equity_data: List[Dict[str, Any]],
        annotations: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Create an annotated equity curve.
        
        annotations format:
        [
          {"timestamp": "2024-01-01", "text": "Major drawdown", "color": "red"},
          {"timestamp": "2024-02-01", "text": "Recovery", "color": "green"}
        ]
        """
        if not equity_data:
            raise ValueError("No equity data provided")
        
        # Extract data
        timestamps = [datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00')) for point in equity_data]
        equity = [point['equity'] for point in equity_data]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(timestamps, equity, linewidth=2, color='steelblue', label='Equity')
        
        # Add annotations
        for annotation in annotations:
            anno_time = datetime.fromisoformat(annotation['timestamp'].replace('Z', '+00:00'))
            # Find closest timestamp
            idx = min(range(len(timestamps)), key=lambda i: abs((timestamps[i] - anno_time).total_seconds()))
            
            ax.annotate(
                annotation['text'],
                xy=(timestamps[idx], equity[idx]),
                xytext=(10, 20),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc=annotation.get('color', 'yellow'), alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
            )
        
        ax.set_title('Annotated Equity Curve', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Equity ($)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Save
        chart_id = str(uuid.uuid4())
        chart_path = self.chart_dir / f"{chart_id}.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return {
            "chart_id": chart_id,
            "url": f"/api/v1/backtest/v2/charts/{chart_id}",
            "path": str(chart_path)
        }
    
    def create_comparison_chart(
        self,
        runs_data: List[Dict[str, Any]],
        metric: str = 'total_return'
    ) -> Dict[str, str]:
        """
        Create a visual comparison of multiple runs.
        
        Args:
        - runs_data: List of dicts with 'id', 'metrics', 'config'
        - metric: Metric to compare
        """
        if not runs_data:
            raise ValueError("No runs data provided")
        
        # Extract data
        run_labels = [f"Run {i+1}" for i in range(len(runs_data))]
        metric_values = [run['metrics'].get(metric, 0) for run in runs_data]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['green' if v > 0 else 'red' for v in metric_values]
        bars = ax.bar(run_labels, metric_values, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}',
                   ha='center', va='bottom' if height > 0 else 'top')
        
        ax.set_title(f'Comparison: {metric.replace("_", " ").title()}', fontsize=14, fontweight='bold')
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.grid(True, alpha=0.3, axis='y')
        
        # Save
        chart_id = str(uuid.uuid4())
        chart_path = self.chart_dir / f"{chart_id}.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return {
            "chart_id": chart_id,
            "url": f"/api/v1/backtest/v2/charts/{chart_id}",
            "path": str(chart_path)
        }
    
    def get_chart_path(self, chart_id: str) -> Optional[Path]:
        """Get the file path for a chart by ID"""
        chart_path = self.chart_dir / f"{chart_id}.png"
        return chart_path if chart_path.exists() else None

