/**
 * 数据看板 — 数据导出工具
 * 提供 CSV / JSON 格式的数据导出能力
 */

import { formatDateStr } from './dateUtils.js'
import { groupByField } from './dataTransformer.js'
import { METRIC_PRECISION, EXPORT_FORMATS } from '../constants/index.js'

/**
 * 将数据数组格式化为 CSV 字符串
 * @param {Object[]} data - 数据数组
 * @param {string[]} columns - 列名列表
 * @param {Object} [options] - { delimiter, includeHeader }
 * @returns {string} CSV 格式字符串
 */
export function formatAsCSV(data, columns, options = {}) {
  const delimiter = options.delimiter || ','
  const includeHeader = options.includeHeader !== false
  const lines = []

  if (includeHeader) {
    lines.push(columns.join(delimiter))
  }

  data.forEach(item => {
    const row = columns.map(col => {
      const val = item[col]
      if (val === null || val === undefined) return ''
      if (typeof val === 'string' && (val.includes(delimiter) || val.includes('"') || val.includes('\n'))) {
        return `"${val.replace(/"/g, '""')}"`
      }
      if (typeof val === 'number') return Number(val.toFixed(METRIC_PRECISION))
      return String(val)
    })
    lines.push(row.join(delimiter))
  })

  return lines.join('\n')
}

/**
 * 将数据格式化为带日期处理的 JSON 字符串
 * @param {Object[]} data - 数据数组
 * @param {Object} [options] - { indent, dateFields }
 * @returns {string} JSON 字符串
 */
export function formatAsJSON(data, options = {}) {
  const indent = options.indent || 2
  const dateFields = options.dateFields || []

  const processed = data.map(item => {
    const obj = { ...item }
    dateFields.forEach(field => {
      if (obj[field]) {
        obj[field] = formatDateStr(obj[field])
      }
    })
    return obj
  })

  return JSON.stringify(processed, null, indent)
}

/**
 * 构建导出文件名
 * @param {string} prefix - 文件名前缀
 * @param {string} [period] - 可选的周期标识
 * @param {string} [extension] - 文件扩展名
 * @returns {string} 完整文件名
 */
export function buildExportFilename(prefix, period = '', extension = EXPORT_FORMATS.CSV) {
  const timestamp = formatDateStr(new Date())
  const parts = [prefix, period, timestamp].filter(Boolean)
  return `${parts.join('_')}.${extension}`
}

/**
 * 按分组字段预聚合后导出
 * @param {Object[]} data - 原始数据
 * @param {string} groupField - 分组字段
 * @param {string} valueField - 数值字段
 * @returns {Object[]} [{ group, count, total, average }]
 */
export function aggregateForExport(data, groupField, valueField) {
  const groups = groupByField(data, groupField)
  return Object.entries(groups).map(([key, items]) => {
    const values = items.map(item => Number(item[valueField]) || 0)
    const total = values.reduce((a, b) => a + b, 0)
    return {
      group: key,
      count: items.length,
      total: Number(total.toFixed(METRIC_PRECISION)),
      average: Number((total / items.length).toFixed(METRIC_PRECISION))
    }
  })
}

/**
 * 批量导出：将多个数据集打包为命名导出对象
 * @param {Object} datasets - { name: Object[] }
 * @param {string[]} columns - 所有数据集共享的列定义
 * @param {string} format - 'csv' | 'json'
 * @returns {Object} { name: formattedString }
 */
export function batchExport(datasets, columns, format = EXPORT_FORMATS.CSV) {
  const result = {}
  Object.entries(datasets).forEach(([name, data]) => {
    if (format === EXPORT_FORMATS.JSON) {
      result[name] = formatAsJSON(data)
    } else {
      result[name] = formatAsCSV(data, columns)
    }
  })
  return result
}
