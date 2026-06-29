/**
 * 数据看板 — 统计分析引擎
 * 提供高级统计分析能力（标准差、相关系数、异常检测、移动平均等）
 */

import { calculateAverage, calculatePercentile } from './metricsCalculator.js'
import { multiConditionFilter } from './filterEngine.js'
import { STATISTICS_CONFIG } from '../constants/index.js'

/**
 * 计算样本标准差
 * @param {number[]} values - 数值数组
 * @returns {number}
 */
export function calculateStandardDeviation(values) {
  if (!values || values.length < 2) return 0
  const avg = calculateAverage(values)
  const squaredDiffs = values.map(v => Math.pow(v - avg, 2))
  return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / (values.length - 1))
}

/**
 * 计算 Pearson 相关系数
 * @param {number[]} xValues
 * @param {number[]} yValues
 * @returns {number} 范围 [-1, 1]
 */
export function calculateCorrelation(xValues, yValues) {
  if (!xValues || !yValues || xValues.length !== yValues.length || xValues.length < 2) return 0

  const n = xValues.length
  const avgX = calculateAverage(xValues)
  const avgY = calculateAverage(yValues)

  let sumXY = 0, sumX2 = 0, sumY2 = 0
  for (let i = 0; i < n; i++) {
    const dx = xValues[i] - avgX
    const dy = yValues[i] - avgY
    sumXY += dx * dy
    sumX2 += dx * dx
    sumY2 += dy * dy
  }

  const denominator = Math.sqrt(sumX2 * sumY2)
  if (denominator === 0) return 0
  return sumXY / denominator
}

/**
 * 基于四分位距（IQR）检测异常值
 * @param {number[]} values - 数值数组
 * @param {number} [threshold] - IQR 倍数阈值
 * @returns {{ outliers: number[], bounds: { lower: number, upper: number } }}
 */
export function detectOutliers(values, threshold = STATISTICS_CONFIG.OUTLIER_THRESHOLD) {
  if (!values || values.length < 4) return { outliers: [], bounds: { lower: 0, upper: 0 } }

  const q1 = calculatePercentile(values, 25)
  const q3 = calculatePercentile(values, 75)
  const iqr = q3 - q1
  const lower = q1 - threshold * iqr
  const upper = q3 + threshold * iqr

  return {
    outliers: values.filter(v => v < lower || v > upper),
    bounds: { lower, upper }
  }
}

/**
 * 计算移动平均
 * @param {number[]} values - 数值数组
 * @param {number} [windowSize] - 窗口大小
 * @returns {number[]}
 */
export function calculateMovingAverage(values, windowSize = STATISTICS_CONFIG.DEFAULT_MOVING_WINDOW) {
  if (!values || values.length === 0) return []
  if (windowSize < 1) windowSize = 1
  if (windowSize > values.length) windowSize = values.length

  const result = []
  for (let i = 0; i < values.length; i++) {
    const start = Math.max(0, i - windowSize + 1)
    const window = values.slice(start, i + 1)
    result.push(calculateAverage(window))
  }
  return result
}

/**
 * 生成数据统计摘要（支持预筛选条件）
 * @param {Object[]} data - 数据数组
 * @param {string} valueField - 数值字段名
 * @param {Object[]} [conditions] - multiConditionFilter 的条件格式
 * @returns {Object} { count, sum, average, min, max, median, stdDev }
 */
export function generateStatsSummary(data, valueField, conditions = []) {
  const filtered = conditions.length > 0
    ? multiConditionFilter(data, conditions)
    : data

  const values = filtered.map(item => Number(item[valueField]) || 0)
  if (values.length === 0) {
    return { count: 0, sum: 0, average: 0, min: 0, max: 0, median: 0, stdDev: 0 }
  }

  return {
    count: values.length,
    sum: values.reduce((a, b) => a + b, 0),
    average: calculateAverage(values),
    min: Math.min(...values),
    max: Math.max(...values),
    median: calculatePercentile(values, 50),
    stdDev: calculateStandardDeviation(values)
  }
}

/**
 * 计算同比/环比数据
 * @param {number[]} currentPeriod - 当期数据
 * @param {number[]} previousPeriod - 前期数据
 * @returns {{ current: number, previous: number, change: number, changeRate: number }}
 */
export function calculatePeriodComparison(currentPeriod, previousPeriod) {
  const currentSum = currentPeriod.reduce((a, b) => a + b, 0)
  const previousSum = previousPeriod.reduce((a, b) => a + b, 0)
  const change = currentSum - previousSum
  const changeRate = previousSum === 0
    ? (currentSum > 0 ? Infinity : 0)
    : (change / previousSum) * 100

  return {
    current: currentSum,
    previous: previousSum,
    change,
    changeRate
  }
}

/**
 * 数据分桶（直方图用）
 * @param {number[]} values - 数值数组
 * @param {number} bucketCount - 桶数量
 * @returns {Object[]} [{ min, max, count, percentage }]
 */
export function createHistogramBuckets(values, bucketCount = 10) {
  if (!values || values.length === 0) return []

  const min = Math.min(...values)
  const max = Math.max(...values)
  const bucketWidth = (max - min) / bucketCount || 1

  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    min: min + i * bucketWidth,
    max: min + (i + 1) * bucketWidth,
    count: 0,
    percentage: 0
  }))

  values.forEach(v => {
    let idx = Math.floor((v - min) / bucketWidth)
    if (idx >= bucketCount) idx = bucketCount - 1
    if (idx < 0) idx = 0
    buckets[idx].count++
  })

  const total = values.length
  buckets.forEach(b => {
    b.percentage = (b.count / total) * 100
  })

  return buckets
}
