'use client'
import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Log in development for immediate feedback
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Web Vitals] ${metric.name}:`, {
        value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
        rating: metric.rating, // 'good' | 'needs-improvement' | 'poor'
        id: metric.id
      })
    }

    // TODO: Send to analytics in production (Vercel Analytics, GA4, etc.)
    // For now, just log to console
  })

  return null
}
