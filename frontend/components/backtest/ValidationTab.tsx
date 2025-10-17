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
  BeakerIcon,
  CheckBadgeIcon,
  ChartBarIcon,
  SparklesIcon,
  ShieldExclamationIcon
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

interface ValidationTabProps {
  run: any
}

export default function ValidationTab({ run }: ValidationTabProps) {
  const [validationData, setValidationData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (run && run.id) {
      fetchValidation()
    }
  }, [run?.id])

  const fetchValidation = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('tq_session')
      const response = await fetch(`/api/v1/backtest/v2/runs/${run.id}/validate`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setValidationData(data)
      } else {
        toast.error('Failed to load validation')
      }
    } catch (error) {
      console.error('Validation error:', error)
      toast.error('Error loading validation')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-dark-teal mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Running statistical validation...</p>
        </div>
      </div>
    )
  }

  if (!validationData) {
    return (
      <div className="text-center py-12">
        <BeakerIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-600 dark:text-gray-400">No validation data available</p>
      </div>
    )
  }

  const monteCarlo = validationData.monte_carlo
  const overfitting = validationData.overfitting
  const bootstrap = validationData.bootstrap
  const luckVsSkill = validationData.luck_vs_skill
  const hypothesisTests = validationData.hypothesis_tests

  // Monte Carlo histogram
  const monteCarloChart = monteCarlo?.equity_distribution?.histogram && {
    labels: monteCarlo.equity_distribution.histogram.bin_centers.map((v: number) => v.toFixed(1) + '%'),
    datasets: [{
      label: 'Frequency',
      data: monteCarlo.equity_distribution.histogram.counts,
      backgroundColor: 'rgba(59, 130, 246, 0.5)',
      borderColor: 'rgb(59, 130, 246)',
      borderWidth: 1
    }]
  }

  // Confidence bands chart
  const confidenceBandsChart = monteCarlo?.confidence_bands && {
    labels: monteCarlo.confidence_bands.timestamps || [],
    datasets: [
      {
        label: '95th Percentile',
        data: monteCarlo.confidence_bands.percentile_95,
        borderColor: 'rgba(34, 197, 94, 0.3)',
        borderWidth: 1,
        fill: false,
        pointRadius: 0
      },
      {
        label: 'Actual Equity',
        data: monteCarlo.confidence_bands.actual_equity,
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 2,
        fill: false,
        pointRadius: 0
      },
      {
        label: '5th Percentile',
        data: monteCarlo.confidence_bands.percentile_5,
        borderColor: 'rgba(239, 68, 68, 0.3)',
        borderWidth: 1,
        fill: false,
        pointRadius: 0
      }
    ]
  }

  const getOverfittingColor = (score: number) => {
    if (score < 20) return 'text-green-600 dark:text-green-400'
    if (score < 40) return 'text-yellow-600 dark:text-yellow-400'
    if (score < 60) return 'text-orange-600 dark:text-orange-400'
    return 'text-red-600 dark:text-red-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <BeakerIcon className="h-6 w-6 text-purple-600 dark:text-purple-400 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-purple-900 dark:text-purple-200 mb-1">
              Statistical Validation Suite
            </h4>
            <p className="text-sm text-purple-800 dark:text-purple-300">
              Validate if your results are statistically significant or just luck using Monte Carlo simulation,
              bootstrap analysis, overfitting detection, and hypothesis testing.
            </p>
          </div>
        </div>
      </div>

      {/* Luck vs Skill */}
      {luckVsSkill && !luckVsSkill.error && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border-2 border-purple-200 dark:border-purple-800 p-6">
          <div className="flex items-center gap-3 mb-4">
            <SparklesIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Luck vs Skill Analysis</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{luckVsSkill.classification}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-4">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Probability of Skill</p>
              <p className="text-5xl font-bold text-green-600 dark:text-green-400">
                {luckVsSkill.probability_skill_pct.toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Probability of Luck</p>
              <p className="text-5xl font-bold text-red-600 dark:text-red-400">
                {luckVsSkill.probability_luck_pct.toFixed(1)}%
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {luckVsSkill.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* Monte Carlo Simulation */}
      {monteCarlo && !monteCarlo.error && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Monte Carlo Simulation ({monteCarlo.simulations_run} simulations)
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Your Result</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {monteCarlo.actual_vs_simulated?.actual_return_pct.toFixed(2)}%
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {monteCarlo.actual_vs_simulated?.actual_percentile.toFixed(0)}th percentile
              </p>
            </div>
            
            <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Median Outcome</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {((monteCarlo.equity_distribution.median - run.config.initial_capital) / run.config.initial_capital * 100).toFixed(2)}%
              </p>
            </div>
            
            <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">95th Percentile</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {((monteCarlo.equity_distribution.percentile_95 - run.config.initial_capital) / run.config.initial_capital * 100).toFixed(2)}%
              </p>
            </div>
            
            <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">5th Percentile</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {((monteCarlo.equity_distribution.percentile_5 - run.config.initial_capital) / run.config.initial_capital * 100).toFixed(2)}%
              </p>
            </div>
          </div>

          {monteCarloChart && (
            <div className="mb-6" style={{ height: '250px' }}>
              <Bar
                data={monteCarloChart}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Distribution of Possible Returns' }
                  },
                  scales: {
                    y: { title: { display: true, text: 'Frequency' } },
                    x: { title: { display: true, text: 'Return %' } }
                  }
                }}
              />
            </div>
          )}

          {confidenceBandsChart && (
            <div style={{ height: '300px' }}>
              <Line
                data={confidenceBandsChart}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Equity Curve with Confidence Bands' }
                  },
                  scales: {
                    y: {
                      title: { display: true, text: 'Equity $' },
                      ticks: { callback: (value: any) => '$' + value.toLocaleString() }
                    },
                    x: { display: false }
                  }
                }}
              />
            </div>
          )}

          <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {monteCarlo.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* Overfitting Detection */}
      {overfitting && !overfitting.error && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Overfitting Risk Assessment
          </h3>

          <div className="flex items-center justify-center mb-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Overfitting Risk Score</p>
              <p className={`text-6xl font-bold ${getOverfittingColor(overfitting.overfitting_risk_score)}`}>
                {overfitting.overfitting_risk_score.toFixed(0)}
              </p>
              <p className="text-lg font-semibold text-gray-600 dark:text-gray-400 mt-2">
                {overfitting.risk_level} Risk
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-4">
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <h4 className="font-semibold text-green-900 dark:text-green-200 mb-3">In-Sample (Training)</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <span className="font-medium">{overfitting.train_performance.avg_sharpe.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Win Rate:</span>
                  <span className="font-medium">{(overfitting.train_performance.avg_win_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg PnL:</span>
                  <span className="font-medium">${overfitting.train_performance.avg_pnl.toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-3">Out-of-Sample (Test)</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <span className="font-medium">{overfitting.test_performance.avg_sharpe.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Win Rate:</span>
                  <span className="font-medium">{(overfitting.test_performance.avg_win_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg PnL:</span>
                  <span className="font-medium">${overfitting.test_performance.avg_pnl.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
            <p className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
              Performance Degradation
            </p>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-yellow-800 dark:text-yellow-300">Sharpe Degradation: </span>
                <span className="font-medium">{overfitting.performance_degradation.sharpe_degradation_pct.toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-yellow-800 dark:text-yellow-300">Win Rate Degradation: </span>
                <span className="font-medium">{overfitting.performance_degradation.win_rate_degradation_pct.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="mt-4 bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong>Interpretation:</strong> {overfitting.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* Bootstrap Confidence Intervals */}
      {bootstrap && !bootstrap.error && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Bootstrap Confidence Intervals
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Win Rate</h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {(bootstrap.win_rate.mean * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                95% CI: [{(bootstrap.win_rate.ci_95_lower * 100).toFixed(1)}%, {(bootstrap.win_rate.ci_95_upper * 100).toFixed(1)}%]
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {bootstrap.interpretation?.win_rate}
              </p>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Sharpe Ratio</h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {bootstrap.sharpe_ratio.mean.toFixed(2)}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                95% CI: [{bootstrap.sharpe_ratio.ci_95_lower.toFixed(2)}, {bootstrap.sharpe_ratio.ci_95_upper.toFixed(2)}]
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {bootstrap.interpretation?.sharpe}
              </p>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Profit Factor</h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {bootstrap.profit_factor.mean.toFixed(2)}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                95% CI: [{bootstrap.profit_factor.ci_95_lower.toFixed(2)}, {bootstrap.profit_factor.ci_95_upper.toFixed(2)}]
              </p>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Expectancy</h4>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                ${bootstrap.expectancy.mean.toFixed(2)}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                95% CI: [${bootstrap.expectancy.ci_95_lower.toFixed(2)}, ${bootstrap.expectancy.ci_95_upper.toFixed(2)}]
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hypothesis Tests */}
      {hypothesisTests && !hypothesisTests.error && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Statistical Hypothesis Tests
          </h3>

          <div className="space-y-4">
            {Object.entries(hypothesisTests).map(([testName, testData]: [string, any]) => (
              <div key={testName} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white capitalize">
                    {testName.replace(/_/g, ' ')}
                  </h4>
                  {testData.is_significant ? (
                    <CheckBadgeIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
                  ) : (
                    <ShieldExclamationIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {testData.null_hypothesis}
                </p>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {testData.conclusion}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

