"use client";

import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi } from 'lightweight-charts';

interface ChartData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface AdvancedChartProps {
  data: ChartData[];
  symbol: string;
  height?: number;
  showVolume?: boolean;
  showIndicators?: boolean;
}

export default function AdvancedChart({ 
  data, 
  symbol, 
  height = 400, 
  showVolume = true,
  showIndicators = true 
}: AdvancedChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'white' },
        textColor: '#333',
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#cccccc',
      },
      timeScale: {
        borderColor: '#cccccc',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // Add volume series if enabled
    if (showVolume) {
      const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
      });
      volumeSeriesRef.current = volumeSeries;
    }

    // Set data
    if (data && data.length > 0) {
      const formattedData = data.map(d => ({
        time: d.time as any,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      candlestickSeries.setData(formattedData);

      if (showVolume && volumeSeriesRef.current && data[0].volume !== undefined) {
        const volumeData = data.map(d => ({
          time: d.time as any,
          value: d.volume || 0,
          color: d.close >= d.open ? '#26a69a' : '#ef5350',
        }));
        volumeSeriesRef.current.setData(volumeData);
      }
    }

    setIsLoading(false);

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [data, height, showVolume]);

  // Update data when props change
  useEffect(() => {
    if (candlestickSeriesRef.current && data && data.length > 0) {
      const formattedData = data.map(d => ({
        time: d.time as any,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      candlestickSeriesRef.current.setData(formattedData);

      if (showVolume && volumeSeriesRef.current && data[0].volume !== undefined) {
        const volumeData = data.map(d => ({
          time: d.time as any,
          value: d.volume || 0,
          color: d.close >= d.open ? '#26a69a' : '#ef5350',
        }));
        volumeSeriesRef.current.setData(volumeData);
      }
    }
  }, [data, showVolume]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading chart...</div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
        <div className="flex space-x-2">
          <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
            1D
          </button>
          <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
            1W
          </button>
          <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">
            1M
          </button>
        </div>
      </div>
      <div 
        ref={chartContainerRef} 
        className="w-full border border-gray-200 rounded-lg"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}
