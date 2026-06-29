/**
 * 数据看板 — 图表配置工具
 */

import { CHART_COLORS, CHART_TYPES } from '../constants/index.js'
import { groupByField } from './dataTransformer.js'

/**
 * 根据数据系列数量获取颜色列表
 * @param {number} count - 系列数量
 * @returns {string[]}
 */
export function getColorPalette(count) {
  const colors = CHART_COLORS.primary
  if (count <= colors.length) return colors.slice(0, count)
  const result = []
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length])
  }
  return result
}

/**
 * 构建坐标轴配置
 * @param {Object} options
 * @returns {Object} ECharts 兼容的 axis 配置
 */
export function buildAxisConfig({ type = 'category', data = [], name = '', formatter = null }) {
  const config = {
    type,
    name,
    nameGap: 30,
    nameTextStyle: { fontSize: 12 }
  }
  if (type === 'category') {
    config.data = data
    config.axisTick = { alignWithLabel: true }
  }
  if (formatter) {
    config.axisLabel = { formatter }
  }
  return config
}

/**
 * 格式化 tooltip 内容
 * @param {Object|Object[]} params - ECharts tooltip params
 * @param {string} valuePrefix - 数值前缀（如 ¥）
 * @param {string} valueSuffix - 数值后缀（如 %）
 * @returns {string} HTML 字符串
 */
export function formatTooltip(params, valuePrefix = '', valueSuffix = '') {
  if (!Array.isArray(params)) params = [params]
  let html = `<div style="font-weight:bold">${params[0].axisValue || params[0].name}</div>`
  params.forEach(item => {
    const marker = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${item.color};margin-right:5px"></span>`
    html += `<div>${marker}${item.seriesName}: ${valuePrefix}${item.value}${valueSuffix}</div>`
  })
  return html
}

/**
 * 根据图表类型生成默认系列配置
 * @param {string} chartType
 * @param {Object} data
 * @returns {Object}
 */
export function buildSeriesConfig(chartType, { name, data, stack = null }) {
  const base = { name, data, type: chartType }
  switch (chartType) {
    case CHART_TYPES.LINE:
      return { ...base, smooth: true, showSymbol: false }
    case CHART_TYPES.BAR:
      return { ...base, barMaxWidth: 40, ...(stack ? { stack } : {}) }
    case CHART_TYPES.PIE:
      return { ...base, type: 'pie', radius: ['40%', '70%'], label: { show: true } }
    case CHART_TYPES.AREA:
      return { ...base, type: 'line', smooth: true, areaStyle: { opacity: 0.3 } }
    default:
      return base
  }
}

/**
 * 构建图例配置
 * @param {string[]} seriesNames - 系列名称列表
 * @param {Object} [options]
 * @returns {Object} ECharts legend 配置
 */
export function buildLegendConfig(seriesNames, options = {}) {
  return {
    show: options.show !== false,
    type: options.type || 'scroll',
    orient: options.orient || 'horizontal',
    data: seriesNames,
    bottom: options.bottom || 0,
    textStyle: { fontSize: 12, color: '#666' }
  }
}

/**
 * 构建网格配置
 * @param {Object} [options]
 * @returns {Object} ECharts grid 配置
 */
export function buildGridConfig(options = {}) {
  return {
    left: options.left || '3%',
    right: options.right || '4%',
    bottom: options.bottom || '15%',
    top: options.top || '10%',
    containLabel: true
  }
}

/**
 * 按分组字段构建多系列图表数据
 * @param {Object[]} data - 原始数据
 * @param {string} groupField - 分组字段
 * @param {string} xField - X 轴字段
 * @param {string} yField - Y 轴字段
 * @returns {Object} { categories, series }
 */
export function buildGroupedSeriesData(data, groupField, xField, yField) {
  const groups = groupByField(data, groupField)
  const categories = [...new Set(data.map(item => item[xField]))]
  const series = Object.entries(groups).map(([name, items]) => {
    const valueMap = {}
    items.forEach(item => { valueMap[item[xField]] = item[yField] })
    return {
      name,
      data: categories.map(cat => valueMap[cat] ?? null)
    }
  })
  return { categories, series }
}

/**
 * 深度合并图表配置
 * @param {Object} base - 基础配置
 * @param  {...Object} overrides - 覆盖配置
 * @returns {Object}
 */
export function mergeChartOptions(base, ...overrides) {
  const result = { ...base }
  for (const override of overrides) {
    for (const [key, value] of Object.entries(override)) {
      if (
        value && typeof value === 'object' && !Array.isArray(value) &&
        result[key] && typeof result[key] === 'object'
      ) {
        result[key] = mergeChartOptions(result[key], value)
      } else {
        result[key] = value
      }
    }
  }
  return result
}
