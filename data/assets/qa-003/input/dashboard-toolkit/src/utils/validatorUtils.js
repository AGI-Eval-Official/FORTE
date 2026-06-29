/**
 * 数据看板 — 数据验证工具
 * 提供输入数据和参数的校验能力
 */

import { parseDateValue } from './dateUtils.js'
import { METRIC_TYPES, PERIOD_TYPES, VALIDATION_RULES } from '../constants/index.js'

/**
 * 验证数据数组是否符合 Schema
 * @param {Object[]} data - 数据数组
 * @param {Object} schema - { fieldName: 'string'|'number'|'date'|'boolean' }
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateDataSchema(data, schema) {
  const errors = []
  const typeCheckers = {
    string: v => typeof v === 'string',
    number: v => typeof v === 'number' && !isNaN(v),
    date: v => !isNaN(parseDateValue(v).getTime()),
    boolean: v => typeof v === 'boolean'
  }

  data.forEach((item, index) => {
    Object.entries(schema).forEach(([field, expectedType]) => {
      const value = item[field]
      if (value === undefined || value === null) {
        errors.push(`Row ${index}: missing required field "${field}"`)
        return
      }
      const checker = typeCheckers[expectedType]
      if (checker && !checker(value)) {
        errors.push(`Row ${index}: field "${field}" expected ${expectedType}, got ${typeof value}`)
      }
    })
  })

  return { valid: errors.length === 0, errors }
}

/**
 * 验证日期范围是否合法
 * @param {string} startDate - 起始日期
 * @param {string} endDate - 结束日期
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateDateRange(startDate, endDate) {
  const start = parseDateValue(startDate)
  const end = parseDateValue(endDate)

  if (isNaN(start.getTime())) return { valid: false, error: 'Invalid start date' }
  if (isNaN(end.getTime())) return { valid: false, error: 'Invalid end date' }
  if (start > end) return { valid: false, error: 'Start date must be before end date' }

  const diffDays = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays > VALIDATION_RULES.MAX_DATE_RANGE_DAYS) {
    return { valid: false, error: `Date range exceeds maximum of ${VALIDATION_RULES.MAX_DATE_RANGE_DAYS} days` }
  }

  return { valid: true }
}

/**
 * 验证指标配置对象
 * @param {Object} config - { type, field, period? }
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateMetricConfig(config) {
  const errors = []
  const validTypes = Object.values(METRIC_TYPES)
  const validPeriods = Object.values(PERIOD_TYPES)

  if (!config.type || !validTypes.includes(config.type)) {
    errors.push(`Invalid metric type "${config.type}". Valid: ${validTypes.join(', ')}`)
  }
  if (!config.field || typeof config.field !== 'string') {
    errors.push('Metric field must be a non-empty string')
  }
  if (config.period && !validPeriods.includes(config.period)) {
    errors.push(`Invalid period "${config.period}". Valid: ${validPeriods.join(', ')}`)
  }

  return { valid: errors.length === 0, errors }
}

/**
 * 净化用户筛选输入（防止 XSS / 非法字符）
 * @param {string} input - 用户原始输入
 * @returns {string} 净化后的字符串
 */
export function sanitizeFilterInput(input) {
  if (typeof input !== 'string') return ''
  return input
    .trim()
    .replace(/[<>]/g, '')
    .replace(/\s+/g, ' ')
    .slice(0, 200)
}

/**
 * 验证分页参数
 * @param {number} page - 页码
 * @param {number} pageSize - 每页条数
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validatePaginationParams(page, pageSize) {
  const errors = []
  if (!Number.isInteger(page) || page < 1) {
    errors.push('Page must be a positive integer')
  }
  if (
    !Number.isInteger(pageSize) ||
    pageSize < VALIDATION_RULES.MIN_PAGE_SIZE ||
    pageSize > VALIDATION_RULES.MAX_PAGE_SIZE
  ) {
    errors.push(
      `Page size must be between ${VALIDATION_RULES.MIN_PAGE_SIZE} and ${VALIDATION_RULES.MAX_PAGE_SIZE}`
    )
  }
  return { valid: errors.length === 0, errors }
}

/**
 * 验证排序规则数组
 * @param {Array<{field: string, order: string}>} sortRules
 * @param {string[]} allowedFields - 允许排序的字段白名单
 * @returns {{ valid: boolean, errors: string[] }}
 */
export function validateSortRules(sortRules, allowedFields) {
  const errors = []
  if (!Array.isArray(sortRules)) {
    return { valid: false, errors: ['Sort rules must be an array'] }
  }
  sortRules.forEach((rule, index) => {
    if (!rule.field || typeof rule.field !== 'string') {
      errors.push(`Rule ${index}: field must be a non-empty string`)
    } else if (allowedFields && !allowedFields.includes(rule.field)) {
      errors.push(`Rule ${index}: field "${rule.field}" is not allowed. Valid: ${allowedFields.join(', ')}`)
    }
    if (rule.order && !['asc', 'desc'].includes(rule.order)) {
      errors.push(`Rule ${index}: order must be "asc" or "desc"`)
    }
  })
  return { valid: errors.length === 0, errors }
}
