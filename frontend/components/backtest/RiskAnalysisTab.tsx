'use client'

import { useState, useEffect } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  BarElement,
  BarController,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import {
  ShieldExclamationIcon,
  ChartBarIcon,
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  LineController,
  BarElement,
  BarController,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface RiskAnalysisTabProps {
  run: any
}

export default function RiskAnalysisTab({ run }: RiskAnalysisTabProps) {
  const [riskData, setRiskData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [selectedConfidence, setSelectedConfidence] = useState('95%')

  useEffect(() => {
    if (run && run.id) {
      fetchRiskAnalysis()
    }
  }, [run?.id])

  const fetchRiskAnalysis = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/backtest/v2/runs/${run.id}/risk-analysis`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setRiskData(data)
      } else {
        toast.error('Failed to load risk analysis')
      }
    } catch (error) {
      console.error('Risk analysis error:', error)
      toast.error('Error loading risk analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Analyzing risk metrics...</p>
        </div>
      </div>
    )
  }

  if (!riskData) {
    return (
      <div className="text-center py-12">
        <ShieldExclamationIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 dark:text-gray-400">No risk data available</p>
      </div>
    )
  }

  const varData = riskData.var_analysis?.[selectedConfidence]
  const cvarData = riskData.cvar_analysis?.[selectedConfidence]
  const drawdownAnalysis = riskData.drawdown_analysis
  const riskMetrics = riskData.risk_metrics
  const tailRisk = riskData.tail_risk
  const stressTests = riskData.stress_tests

  // Drawdown chart data
  const drawdownChartData = drawdownAnalysis && {
    labels: drawdownAnalysis.timestamps || [],
    datasets: [
      {
        label: 'Drawdown %',
        data: drawdownAnalysis.drawdown_series || [],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.1
      }
    ]
  }

  const getRiskLevelColor = (value: number, thresholds: {good: number, warning: number}) => {
    if (value < thresholds.good) return 'text-green-600 dark:text-green-400'
    if (value < thresholds.warning) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  return (
    <div className="space-y-6">
      {/* Header Alert */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <InformationCircleIcon className="h-6 w-6 text-blue-600 dark:text-blue-400 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-1">
              Professional Risk Analysis
            </h4>
            <p className="text-sm text-blue-800 dark:text-blue-300">
              Comprehensive risk metrics including VaR, CVaR, stress testing, and drawdown analysis.
              These metrics help you understand the downside risk of your strategy.
            </p>
          </div>
        </div>
      </div>

      {/* VaR & CVaR Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Value-at-Risk */}
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Value-at-Risk (VaR)</h3>
            <select
              value={selectedConfidence}
              onChange={(e) => setSelectedConfidence(e.target.value)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 bg-white dark:bg-gray-800"
            >
              <option value="95%">95% Confidence</option>
              <option value="99%">99% Confidence</option>
            </select>
          </div>
          
          {varData && (
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Historical VaR</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(varData.historical * 100).toFixed(2)}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  ${Math.abs(varData.historical_dollar).toLocaleString()}
                </p>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Interpretation:</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {varData.interpretation}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Parametric VaR</p>
                  <p className="text-sm font-semibold">{(varData.parametric * 100).toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Monte Carlo VaR</p>
                  <p className="text-sm font-semibold">{(varData.monte_carlo * 100).toFixed(2)}%</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Conditional VaR */}
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Conditional VaR (CVaR)
          </h3>
          
          {cvarData && (
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Expected Shortfall</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {(cvarData.cvar * 100).toFixed(2)}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  ${Math.abs(cvarData.cvar_dollar).toLocaleString()}
                </p>
              </div>
              
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3">
                <p className="text-xs text-yellow-800 dark:text-yellow-300 mb-2">What is CVaR?</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-400">
                  {cvarData.interpretation}
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Tail Trades</p>
                <p className="text-sm font-semibold">
                  {cvarData.tail_trade_count} trades exceed VaR threshold
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Risk Metrics Dashboard */}
      {riskMetrics && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Risk-Adjusted Performance
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Sharpe Ratio</p>
              <p className={`text-2xl font-bold ${getRiskLevelColor(riskMetrics.sharpe_ratio, {good: 1, warning: 0.5})}`}>
                {riskMetrics.sharpe_ratio?.toFixed(2) || 'N/A'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {riskMetrics.interpretation?.sharpe}
              </p>
            </div>
            
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Sortino Ratio</p>
              <p className={`text-2xl font-bold ${getRiskLevelColor(riskMetrics.sortino_ratio, {good: 1, warning: 0.5})}`}>
                {riskMetrics.sortino_ratio?.toFixed(2) || 'N/A'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {riskMetrics.interpretation?.sortino}
              </p>
            </div>
            
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Volatility</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(riskMetrics.volatility * 100)?.toFixed(2)}%
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {riskMetrics.interpretation?.volatility}
              </p>
            </div>
            
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Downside Vol</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {(riskMetrics.downside_volatility * 100)?.toFixed(2)}%
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Downside risk only
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Drawdown Analysis */}
      {drawdownAnalysis && drawdownChartData && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <ArrowTrendingDownIcon className="h-5 w-5" />
              Drawdown Analysis
            </h3>
            <div className="text-right">
              <p className="text-xs text-gray-600 dark:text-gray-400">Max Drawdown</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {drawdownAnalysis.max_drawdown_pct?.toFixed(2)}%
              </p>
            </div>
          </div>
          
          <div className="mb-6" style={{ height: '300px' }}>
            <Line 
              data={drawdownChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    callbacks: {
                      label: (context: any) => `Drawdown: ${context.parsed.y.toFixed(2)}%`
                    }
                  }
                },
                scales: {
                  y: {
                    title: { display: true, text: 'Drawdown %' },
                    ticks: {
                      callback: (value: any) => value.toFixed(1) + '%'
                    }
                  },
                  x: { display: false }
                }
              }}
            />
          </div>

          {/* Top 5 Drawdowns */}
          {drawdownAnalysis.top_5_drawdowns && drawdownAnalysis.top_5_drawdowns.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Worst Drawdowns</h4>
              <div className="space-y-2">
                {drawdownAnalysis.top_5_drawdowns.map((dd: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">
                        {dd.max_dd_pct.toFixed(2)}% drawdown
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        Duration: {dd.duration_hours.toFixed(1)} hours
                        {dd.recovered && ` • Recovered in ${dd.recovery_time_hours.toFixed(1)} hours`}
                      </p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      dd.recovered 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                    }`}>
                      {dd.recovered ? 'Recovered' : 'Ongoing'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stress Tests */}
      {stressTests && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldExclamationIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Stress Test Scenarios
            </h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(stressTests).map(([scenario, data]: [string, any]) => (
              <div key={scenario} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white capitalize">
                    {scenario.replace('_', ' ')}
                  </h4>
                  <span className="text-sm font-medium text-red-600 dark:text-red-400">
                    {data.market_drop_pct.toFixed(0)}% market drop
                  </span>
                </div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Strategy Impact:</span>
                    <span className="font-medium">{data.estimated_strategy_impact_pct.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Projected Loss:</span>
                    <span className="font-medium text-red-600 dark:text-red-400">
                      ${data.projected_loss.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Recovery Trades:</span>
                    <span className="font-medium">{data.recovery_trades_needed}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tail Risk */}
      {tailRisk && !tailRisk.error && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Tail Risk Analysis
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Skewness</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {tailRisk.skewness.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {tailRisk.skewness_interpretation}
              </p>
            </div>
            
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Kurtosis</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {tailRisk.kurtosis.toFixed(3)}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {tailRisk.kurtosis_interpretation}
              </p>
            </div>
            
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Extreme Events</p>
              <p className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                {tailRisk.extreme_events_count}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {tailRisk.extreme_events_pct.toFixed(1)}% of trades
              </p>
            </div>
            
            <div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Distribution</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {tailRisk.is_normally_distributed ? 'Normal' : 'Non-normal'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                p={tailRisk.jarque_bera_pvalue.toFixed(4)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

