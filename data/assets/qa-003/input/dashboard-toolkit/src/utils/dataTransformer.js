/**
 * 数据看板 — 数据转换工具
 * 将原始数据转换为图表所需的格式
 */

import { getPeriodKey } from './dateUtils.js'

/**
 * 按指定字段分组
 * @param {Object[]} data - 数据数组
 * @param {string} field - 分组字段名
 * @returns {Object} 分组结果 { fieldValue: [items] }
 */
export function groupByField(data, field) {
  return data.reduce((groups, item) => {
    const key = item[field]
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
    return groups
  }, {})
}

/**
 * 按指定字段排序
 * @param {Object[]} data - 数据数组
 * @param {string} field - 排序字段名
 * @param {'asc'|'desc'} order - 排序方向
 * @returns {Object[]} 排序后的新数组
 */
export function sortByField(data, field, order = 'asc') {
  const sorted = data.sort((a, b) => {
    if (order === 'asc') return a[field] > b[field] ? 1 : -1
    return a[field] < b[field] ? 1 : -1
  })
  return sorted
}

/**
 * 将原始数据格式化为时间序列
 * @param {Object[]} data - 数据数组
 * @param {string} dateField - 日期字段名
 * @param {string} valueField - 数值字段名
 * @returns {Object[]} [{ date, value }]
 */
export function formatTimeSeries(data, dateField, valueField) {
  return data.map(item => ({
    date: item[dateField],
    value: item[valueField]
  }))
}

/**
 * 按时间周期聚合数据
 * @param {Object[]} data - 数据数组
 * @param {string} dateField - 日期字段名
 * @param {string} valueField - 数值字段名
 * @param {'day'|'week'|'month'|'quarter'|'year'} period - 聚合周期
 * @param {'sum'|'average'|'count'|'max'|'min'} aggregation - 聚合方式
 * @returns {Object[]} [{ period, value }]
 */
export function aggregateByPeriod(data, dateField, valueField, period = 'month', aggregation = 'sum') {
  const buckets = {}

  data.forEach(item => {
    const key = getPeriodKey(item[dateField], period)
    if (!buckets[key]) buckets[key] = []
    buckets[key].push(Number(item[valueField]) || 0)
  })

  return Object.entries(buckets).map(([periodKey, values]) => {
    let value
    switch (aggregation) {
      case 'sum':
        value = values.reduce((a, b) => a + b, 0)
        break
      case 'average':
        value = values.reduce((a, b) => a + b, 0) / values.length
        break
      case 'count':
        value = values.length
        break
      case 'max':
        value = Math.max(...values)
        break
      case 'min':
        value = Math.min(...values)
        break
      default:
        value = values.reduce((a, b) => a + b, 0)
    }
    return { period: periodKey, value }
  }).sort((a, b) => a.period.localeCompare(b.period))
}

/**
 * 构建数据透视表
 * @param {Object[]} data - 数据数组
 * @param {string} rowField - 行字段
 * @param {string} colField - 列字段
 * @param {string} valueField - 值字段
 * @param {'sum'|'count'|'average'} aggregation - 聚合方式
 * @returns {Object} { rows, columns, cells }
 */
export function pivotData(data, rowField, colField, valueField, aggregation = 'sum') {
  const rows = [...new Set(data.map(item => item[rowField]))]
  const columns = [...new Set(data.map(item => item[colField]))]

  const cells = {}
  rows.forEach(row => {
    cells[row] = {}
    columns.forEach(col => {
      cells[row][col] = null
    })
  })

  const buckets = {}
  data.forEach(item => {
    const key = `${item[rowField]}__${item[colField]}`
    if (!buckets[key]) buckets[key] = []
    buckets[key].push(Number(item[valueField]) || 0)
  })

  Object.entries(buckets).forEach(([key, values]) => {
    const [rowKey, colKey] = key.split('__')
    switch (aggregation) {
      case 'sum':
        cells[rowKey][colKey] = values.reduce((a, b) => a + b, 0)
        break
      case 'count':
        cells[rowKey][colKey] = values.length
        break
      case 'average':
        cells[rowKey][colKey] = values.reduce((a, b) => a + b, 0) / values.length
        break
    }
  })

  return { rows, columns, cells }
}

/**
 * 将嵌套分组结果展平为列表
 * @param {Object} groupedData - groupByField 的输出
 * @param {string} groupLabel - 分组字段名称
 * @returns {Object[]}
 */
export function flattenNestedGroups(groupedData, groupLabel = 'group') {
  const result = []
  Object.entries(groupedData).forEach(([key, items]) => {
    items.forEach(item => {
      result.push({ [groupLabel]: key, ...item })
    })
  })
  return result
}
