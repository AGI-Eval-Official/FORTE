/**
 * 数据看板 — 指标计算工具
 * 提供各类业务 KPI 的计算方法
 */

import { METRIC_PRECISION } from '../constants/index.js'

/**
 * 内部工具：四舍五入到指定精度
 */
function roundTo(value, decimals = METRIC_PRECISION) {
  const factor = Math.pow(10, decimals)
  return Math.round(value * factor) / factor
}

/**
 * 计算增长率
 * @param {number} oldValue - 基期值
 * @param {number} newValue - 报告期值
 * @returns {number} 增长率（百分比）
 */
export function calculateGrowthRate(oldValue, newValue) {
  if (oldValue === 0) return newValue > 0 ? Infinity : 0
  return ((newValue - oldValue) / newValue) * 100
}

/**
 * 计算复合年增长率（CAGR）
 * @param {number} beginValue - 期初值
 * @param {number} endValue - 期末值
 * @param {number} periods - 期数
 * @returns {number} CAGR 百分比
 */
export function calculateCAGR(beginValue, endValue, periods) {
  if (beginValue <= 0 || periods <= 0) return 0
  return roundTo((Math.pow(endValue / beginValue, 1 / periods) - 1) * 100)
}

/**
 * 计算转化率
 * @param {number} conversions - 转化数
 * @param {number} total - 总数
 * @returns {number} 转化率（百分比）
 */
export function calculateConversionRate(conversions, total) {
  if (total === 0) return 0
  return (conversions / total) * 100
}

/**
 * 计算留存率
 * @param {number} initialUsers - 初始用户数
 * @param {number} remainingUsers - 留存用户数
 * @returns {number} 留存率（百分比）
 */
export function calculateRetentionRate(initialUsers, remainingUsers) {
  if (initialUsers === 0) return 0
  return roundTo((remainingUsers / initialUsers) * 100)
}

/**
 * 计算均值
 * @param {number[]} values - 数值数组
 * @returns {number} 算术平均值
 */
export function calculateAverage(values) {
  if (!values || values.length === 0) return 0
  return values.reduce((sum, val) => sum + val, 0) / values.length
}

/**
 * 计算加权均值
 * @param {number[]} values - 数值数组
 * @param {number[]} weights - 权重数组（长度必须与 values 一致）
 * @returns {number} 加权平均值
 */
export function calculateWeightedAverage(values, weights) {
  if (!values || !weights || values.length !== weights.length || values.length === 0) return 0
  const totalWeight = weights.reduce((sum, w) => sum + w, 0)
  if (totalWeight === 0) return 0
  const weightedSum = values.reduce((sum, val, i) => sum + val * weights[i], 0)
  return roundTo(weightedSum / totalWeight)
}

/**
 * 计算百分位数（线性插值法）
 * @param {number[]} values - 数值数组
 * @param {number} percentile - 百分位（0~100）
 * @returns {number}
 */
export function calculatePercentile(values, percentile) {
  if (!values || values.length === 0) return 0
  if (percentile < 0 || percentile > 100) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const index = (percentile / 100) * (sorted.length - 1)
  const lower = Math.floor(index)
  const upper = Math.ceil(index)
  if (lower === upper) return sorted[lower]
  const weight = index - lower
  return roundTo(sorted[lower] * (1 - weight) + sorted[upper] * weight)
}

/**
 * 计算 ARPU（每用户平均收入）
 * @param {number} totalRevenue - 总收入
 * @param {number} activeUsers - 活跃用户数
 * @returns {number}
 */
export function calculateARPU(totalRevenue, activeUsers) {
  if (activeUsers === 0) return 0
  return roundTo(totalRevenue / activeUsers)
}
