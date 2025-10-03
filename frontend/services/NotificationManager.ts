'use client'

import React from 'react'
import { useNotifications } from '../hooks/useNotifications'

export class NotificationManager {
  private static instance: NotificationManager
  private notificationHook: ReturnType<typeof useNotifications> | null = null

  static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager()
    }
    return NotificationManager.instance
  }

  setHook(hook: ReturnType<typeof useNotifications>) {
    this.notificationHook = hook
  }

  // Trade-related notifications
  async notifyTradeAlert(
    symbol: string,
    action: 'buy' | 'sell' | 'hold',
    price: number,
    reason?: string
  ) {
    const title = `Trade Alert: ${symbol.toUpperCase()}`
    const message = `${action.toUpperCase()} signal for ${symbol.toUpperCase()} at $${price}${reason ? ` - ${reason}` : ''}`
    
    return this.createNotification(
      title,
      message,
      'trade_alert',
      'high',
      ['in_app', 'email'],
      { symbol, action, price, reason }
    )
  }

  async notifyPriceAlert(
    symbol: string,
    currentPrice: number,
    targetPrice: number,
    direction: 'above' | 'below'
  ) {
    const title = `Price Alert: ${symbol.toUpperCase()}`
    const message = `${symbol.toUpperCase()} is now $${currentPrice}, ${direction} your target of $${targetPrice}`
    
    return this.createNotification(
      title,
      message,
      'price_alert',
      'medium',
      ['in_app', 'email'],
      { symbol, currentPrice, targetPrice, direction }
    )
  }

  // Security notifications
  async notifySecurityAlert(
    type: 'login' | 'password_change' | 'suspicious_activity',
    details?: string
  ) {
    const titles = {
      login: 'New Login Detected',
      password_change: 'Password Changed',
      suspicious_activity: 'Suspicious Activity Detected'
    }
    
    const messages = {
      login: 'A new login was detected on your account',
      password_change: 'Your password has been successfully changed',
      suspicious_activity: 'Suspicious activity detected on your account'
    }

    return this.createNotification(
      titles[type],
      `${messages[type]}${details ? ` - ${details}` : ''}`,
      'security_alert',
      'urgent',
      ['in_app', 'email', 'sms'],
      { type, details }
    )
  }

  // System notifications
  async notifySystemUpdate(
    title: string,
    message: string,
    priority: 'low' | 'medium' | 'high' | 'urgent' = 'medium'
  ) {
    return this.createNotification(
      title,
      message,
      'system_update',
      priority,
      ['in_app', 'email'],
      { systemUpdate: true }
    )
  }

  // Account notifications
  async notifyAccountUpdate(
    type: 'subscription' | 'billing' | 'profile',
    message: string
  ) {
    return this.createNotification(
      `Account Update: ${type.charAt(0).toUpperCase() + type.slice(1)}`,
      message,
      'account_update',
      'medium',
      ['in_app', 'email'],
      { type }
    )
  }

  // Market news notifications
  async notifyMarketNews(
    symbol: string,
    headline: string,
    impact: 'low' | 'medium' | 'high' = 'medium'
  ) {
    const priority = impact === 'high' ? 'high' : impact === 'medium' ? 'medium' : 'low'
    
    return this.createNotification(
      `Market News: ${symbol.toUpperCase()}`,
      headline,
      'market_news',
      priority,
      ['in_app', 'email'],
      { symbol, headline, impact }
    )
  }

  // Backtesting notifications
  async notifyBacktestComplete(
    strategyName: string,
    results: {
      totalTrades: number
      winRate: number
      profitLoss: number
    }
  ) {
    const title = `Backtest Complete: ${strategyName}`
    const message = `Strategy completed with ${results.totalTrades} trades, ${(results.winRate * 100).toFixed(1)}% win rate, ${results.profitLoss > 0 ? '+' : ''}$${results.profitLoss.toFixed(2)} P&L`
    
    return this.createNotification(
      title,
      message,
      'backtest_complete',
      'medium',
      ['in_app', 'email'],
      { strategyName, results }
    )
  }

  // Journal reminders
  async notifyJournalReminder(
    daysSinceLastEntry: number,
    suggestedAction?: string
  ) {
    const title = 'Journal Reminder'
    const message = `It's been ${daysSinceLastEntry} days since your last journal entry${suggestedAction ? `. ${suggestedAction}` : ''}`
    
    return this.createNotification(
      title,
      message,
      'journal_reminder',
      'low',
      ['in_app'],
      { daysSinceLastEntry, suggestedAction }
    )
  }

  // Subscription notifications
  async notifySubscriptionUpdate(
    type: 'upgrade' | 'downgrade' | 'renewal' | 'cancellation',
    plan: string,
    details?: string
  ) {
    const titles = {
      upgrade: 'Subscription Upgraded',
      downgrade: 'Subscription Downgraded',
      renewal: 'Subscription Renewed',
      cancellation: 'Subscription Cancelled'
    }

    return this.createNotification(
      titles[type],
      `Your subscription has been ${type}${details ? ` - ${details}` : ''}`,
      'subscription',
      'medium',
      ['in_app', 'email'],
      { type, plan, details }
    )
  }

  // Generic notification creator
  private async createNotification(
    title: string,
    message: string,
    type: string,
    priority: 'low' | 'medium' | 'high' | 'urgent',
    channels: string[],
    metadata?: any
  ) {
    if (!this.notificationHook) {
      console.warn('NotificationManager: Hook not initialized')
      return null
    }

    return this.notificationHook.createNotification(
      title,
      message,
      type,
      priority,
      channels,
      metadata
    )
  }

  // Utility methods
  getUnreadCount(): number {
    return this.notificationHook?.getUnreadCount() || 0
  }

  async markAsRead(notificationIds: string[]): Promise<boolean> {
    return this.notificationHook?.markAsRead(notificationIds) || false
  }

  async markAllAsRead(): Promise<boolean> {
    return this.notificationHook?.markAllAsRead() || false
  }

  getNotificationsByType(type: string) {
    return this.notificationHook?.getNotificationsByType(type) || []
  }

  getUnreadNotifications() {
    return this.notificationHook?.getUnreadNotifications() || []
  }
}

// Export singleton instance
export const notificationManager = NotificationManager.getInstance()

// Hook for initializing the notification manager
export const useNotificationManager = () => {
  const hook = useNotifications()
  
  React.useEffect(() => {
    notificationManager.setHook(hook)
  }, [hook])

  return notificationManager
}
