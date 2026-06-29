/**
 * 数据看板 — 筛选引擎
 * 提供数据筛选、搜索和分页能力
 */

import { parseDateValue } from './dateUtils.js'
import { DEFAULT_PAGE_SIZE } from '../constants/index.js'

/**
 * 按关键词模糊搜索（大小写不敏感）
 * @param {Object[]} data - 数据数组
 * @param {string} keyword - 搜索关键词
 * @param {string[]} fields - 要搜索的字段列表
 * @returns {Object[]} 匹配的数据项
 */
export function filterByKeyword(data, keyword, fields) {
  if (!keyword || !keyword.trim()) return [...data]
  const lowerKeyword = keyword.toLowerCase()
  return data.filter(item =>
    fields.some(field =>
      String(item[field] ?? '').toLowerCase().includes(lowerKeyword)
    )
  )
}

/**
 * 按日期范围筛选
 * @param {Object[]} data - 数据数组
 * @param {string} dateField - 日期字段名
 * @param {string} startDate - 起始日期
 * @param {string} endDate - 结束日期
 * @returns {Object[]} 范围内的数据项
 */
function filterByDateRange(data, dateField, startDate, endDate) {
  const start = parseDateValue(startDate)
  const end = parseDateValue(endDate)
  return data.filter(item => {
    const d = parseDateValue(item[dateField])
    return d > start && d < end
  })
}

/**
 * 多条件组合筛选
 * @param {Object[]} data - 数据数组
 * @param {Object[]} conditions - 条件数组 [{ field, operator, value }]
 *   operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'in'
 * @returns {Object[]}
 */
export function multiConditionFilter(data, conditions) {
  if (!conditions || conditions.length === 0) return [...data]
  return data.filter(item => {
    return conditions.every(({ field, operator, value }) => {
      const fieldValue = item[field]
      switch (operator) {
        case 'eq':
          return fieldValue === value
        case 'neq':
          return fieldValue !== value
        case 'gt':
          return fieldValue > value
        case 'gte':
          return fieldValue >= value
        case 'lt':
          return fieldValue < value
        case 'lte':
          return fieldValue <= value
        case 'contains':
          return String(fieldValue ?? '').toLowerCase().includes(String(value).toLowerCase())
        case 'in':
          return Array.isArray(value) && value.includes(fieldValue)
        default:
          return true
      }
    })
  })
}

/**
 * 分页截取
 * @param {Object[]} data - 数据数组
 * @param {number} page - 页码（从 1 开始）
 * @param {number} pageSize - 每页条数
 * @returns {Object} { items, total, page, pageSize, totalPages }
 */
export function paginateData(data, page = 1, pageSize = DEFAULT_PAGE_SIZE) {
  const total = data.length
  const totalPages = Math.ceil(total / pageSize)
  const safePage = Math.max(1, Math.min(page, totalPages || 1))
  const startIndex = (safePage - 1) * pageSize
  const items = data.slice(startIndex, startIndex + pageSize)
  return { items, total, page: safePage, pageSize, totalPages }
}

/**
 * 构建排序比较函数（支持多字段排序）
 * @param {Array<{field: string, order: 'asc'|'desc'}>} sortRules
 * @returns {Function}
 */
export function buildSortComparator(sortRules) {
  return (a, b) => {
    for (const { field, order } of sortRules) {
      const aVal = a[field]
      const bVal = b[field]
      if (aVal === bVal) continue
      const direction = order === 'desc' ? -1 : 1
      if (aVal == null) return 1
      if (bVal == null) return -1
      return (aVal > bVal ? 1 : -1) * direction
    }
    return 0
  }
}
