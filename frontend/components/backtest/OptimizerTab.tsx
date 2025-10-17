'use client'

import { useState } from 'react'
import {
  AdjustmentsHorizontalIcon,
  PlayIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface OptimizerTabProps {
  run: any
}

export default function OptimizerTab({ run }: OptimizerTabProps) {
  const [optimizing, setOptimizing] = useState(false)
  const [optimizationResults, setOptimizationResults] = useState<any>(null)
  
  // Parameter ranges
  const [stopLossMin, setStopLossMin] = useState(1)
  const [stopLossMax, setStopLossMax] = useState(5)
  const [stopLossStep, setStopLossStep] = useState(0.5)
  
  const [takeProfitMin, setTakeProfitMin] = useState(2)
  const [takeProfitMax, setTakeProfitMax] = useState(10)
  const [takeProfitStep, setTakeProfitStep] = useState(1)
  
  const [positionSizeMin, setPositionSizeMin] = useState(50)
  const [positionSizeMax, setPositionSizeMax] = useState(100)
  const [positionSizeStep, setPositionSizeStep] = useState(10)

  const runOptimization = async () => {
    setOptimizing(true)
    try {
      const token = localStorage.getItem('tq_session')
      
      const parameter_ranges = {
        stop_loss_pct: {
          min: stopLossMin,
          max: stopLossMax,
          step: stopLossStep
        },
        take_profit_pct: {
          min: takeProfitMin,
          max: takeProfitMax,
          step: takeProfitStep
        },
        position_size_pct: {
          min: positionSizeMin,
          max: positionSizeMax,
          step: positionSizeStep
        }
      }
      
      const response = await fetch(`/api/v1/backtest/v2/runs/${run.id}/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ parameter_ranges })
      })
      
      if (response.ok) {
        const data = await response.json()
        setOptimizationResults(data)
        toast.success('Optimization complete!')
      } else {
        toast.error('Optimization failed')
      }
    } catch (error) {
      console.error('Optimization error:', error)
      toast.error('Error running optimization')
    } finally {
      setOptimizing(false)
    }
  }

  const estimatedCombinations = 
    Math.ceil((stopLossMax - stopLossMin) / stopLossStep + 1) *
    Math.ceil((takeProfitMax - takeProfitMin) / takeProfitStep + 1) *
    Math.ceil((positionSizeMax - positionSizeMin) / positionSizeStep + 1)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AdjustmentsHorizontalIcon className="h-6 w-6 text-green-600 dark:text-green-400 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-green-900 dark:text-green-200 mb-1">
              Strategy Parameter Optimizer
            </h4>
            <p className="text-sm text-green-800 dark:text-green-300">
              Find optimal parameters by testing different combinations on your existing trades.
              This simulates what would have happened with different stop loss, take profit, and position sizes.
            </p>
          </div>
        </div>
      </div>

      {/* Parameter Configuration */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Configure Parameter Ranges
        </h3>

        <div className="space-y-6">
          {/* Stop Loss */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Stop Loss % Range
            </label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Min</label>
                <input
                  type="number"
                  value={stopLossMin}
                  onChange={(e) => setStopLossMin(parseFloat(e.target.value))}
                  step="0.5"
                  min="0.5"
                  max="20"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Max</label>
                <input
                  type="number"
                  value={stopLossMax}
                  onChange={(e) => setStopLossMax(parseFloat(e.target.value))}
                  step="0.5"
                  min="0.5"
                  max="20"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Step</label>
                <input
                  type="number"
                  value={stopLossStep}
                  onChange={(e) => setStopLossStep(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  max="2"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
            </div>
          </div>

          {/* Take Profit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Take Profit % Range
            </label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Min</label>
                <input
                  type="number"
                  value={takeProfitMin}
                  onChange={(e) => setTakeProfitMin(parseFloat(e.target.value))}
                  step="0.5"
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Max</label>
                <input
                  type="number"
                  value={takeProfitMax}
                  onChange={(e) => setTakeProfitMax(parseFloat(e.target.value))}
                  step="0.5"
                  min="1"
                  max="50"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Step</label>
                <input
                  type="number"
                  value={takeProfitStep}
                  onChange={(e) => setTakeProfitStep(parseFloat(e.target.value))}
                  step="0.5"
                  min="0.5"
                  max="5"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
            </div>
          </div>

          {/* Position Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Position Size % Range
            </label>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Min</label>
                <input
                  type="number"
                  value={positionSizeMin}
                  onChange={(e) => setPositionSizeMin(parseFloat(e.target.value))}
                  step="5"
                  min="10"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Max</label>
                <input
                  type="number"
                  value={positionSizeMax}
                  onChange={(e) => setPositionSizeMax(parseFloat(e.target.value))}
                  step="5"
                  min="10"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Step</label>
                <input
                  type="number"
                  value={positionSizeStep}
                  onChange={(e) => setPositionSizeStep(parseFloat(e.target.value))}
                  step="5"
                  min="5"
                  max="20"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Will test <strong>{estimatedCombinations}</strong> parameter combinations
          </p>
          <button
            onClick={runOptimization}
            disabled={optimizing}
            className="px-6 py-3 bg-gradient-to-r from-brand-dark-teal to-brand-bright-yellow text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {optimizing ? (
              <>
                <ArrowPathIcon className="h-5 w-5 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <PlayIcon className="h-5 w-5" />
                Run Optimization
              </>
            )}
          </button>
        </div>
      </div>

      {/* Optimization Results */}
      {optimizationResults && (
        <>
          {/* Best Parameters */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border-2 border-green-200 dark:border-green-800 p-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <ChartBarIcon className="h-6 w-6 text-green-600" />
              Optimal Parameters Found
            </h3>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Stop Loss</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {optimizationResults.best_parameters?.stop_loss_pct?.toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Take Profit</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {optimizationResults.best_parameters?.take_profit_pct?.toFixed(1)}%
                </p>
              </div>
              <div className="text-center p-4 bg-white dark:bg-gray-800 rounded-lg">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Position Size</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {optimizationResults.best_parameters?.position_size_pct?.toFixed(0)}%
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Sharpe Ratio</p>
                <p className="text-lg font-bold">{optimizationResults.best_metrics?.sharpe_ratio?.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Total Return</p>
                <p className="text-lg font-bold">{optimizationResults.best_metrics?.total_return_pct?.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Max DD</p>
                <p className="text-lg font-bold">{optimizationResults.best_metrics?.max_drawdown_pct?.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Win Rate</p>
                <p className="text-lg font-bold">{optimizationResults.best_metrics?.win_rate_pct?.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          {/* Improvement vs Original */}
          {optimizationResults.improvement_vs_original && (
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Improvement vs Original Strategy
              </h3>

              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Sharpe Improvement</p>
                  <p className={`text-2xl font-bold ${
                    optimizationResults.improvement_vs_original.sharpe_improvement_pct > 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {optimizationResults.improvement_vs_original.sharpe_improvement_pct > 0 ? '+' : ''}
                    {optimizationResults.improvement_vs_original.sharpe_improvement_pct.toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Return Improvement</p>
                  <p className={`text-2xl font-bold ${
                    optimizationResults.improvement_vs_original.return_improvement_pct > 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {optimizationResults.improvement_vs_original.return_improvement_pct > 0 ? '+' : ''}
                    {optimizationResults.improvement_vs_original.return_improvement_pct.toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">DD Improvement</p>
                  <p className={`text-2xl font-bold ${
                    optimizationResults.improvement_vs_original.dd_improvement_pct < 0 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {optimizationResults.improvement_vs_original.dd_improvement_pct.toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">(negative is better)</p>
                </div>
              </div>
            </div>
          )}

          {/* Top 10 Configurations */}
          {optimizationResults.top_10_configurations && (
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Top 10 Parameter Configurations
              </h3>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Rank</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Stop Loss %</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Take Profit %</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Position %</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400">Sharpe</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400">Return %</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400">Max DD %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {optimizationResults.top_10_configurations.map((config: any, i: number) => (
                      <tr key={i} className={i === 0 ? 'bg-green-50 dark:bg-green-900/20' : ''}>
                        <td className="px-4 py-2 text-sm font-medium">{i + 1}</td>
                        <td className="px-4 py-2 text-sm">{config.parameters.stop_loss_pct.toFixed(1)}</td>
                        <td className="px-4 py-2 text-sm">{config.parameters.take_profit_pct.toFixed(1)}</td>
                        <td className="px-4 py-2 text-sm">{config.parameters.position_size_pct.toFixed(0)}</td>
                        <td className="px-4 py-2 text-sm text-right font-medium">{config.sharpe_ratio.toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-right">{config.total_return_pct.toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm text-right">{config.max_drawdown_pct.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Kelly Criterion */}
          {optimizationResults.kelly_criterion && !optimizationResults.kelly_criterion.error && (
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-2 mb-4">
                <CurrencyDollarIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Kelly Criterion - Optimal Position Sizing
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-6 mb-4">
                <div className="text-center p-6 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Full Kelly</p>
                  <p className="text-5xl font-bold text-green-600 dark:text-green-400">
                    {optimizationResults.kelly_criterion.kelly_percentage.toFixed(1)}%
                  </p>
                </div>
                <div className="text-center p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Safe Kelly (Recommended)</p>
                  <p className="text-5xl font-bold text-blue-600 dark:text-blue-400">
                    {optimizationResults.kelly_criterion.safe_kelly_percentage.toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <p className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  Recommendation:
                </p>
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  {optimizationResults.kelly_criterion.recommendation}
                </p>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Win Rate:</span>
                  <span className="ml-2 font-medium">{(optimizationResults.kelly_criterion.win_rate * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Avg Win:</span>
                  <span className="ml-2 font-medium">${optimizationResults.kelly_criterion.avg_win.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Avg Loss:</span>
                  <span className="ml-2 font-medium">${optimizationResults.kelly_criterion.avg_loss.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

