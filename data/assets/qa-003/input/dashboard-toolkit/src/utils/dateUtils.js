/**
 * 数据看板 — 日期工具
 */

/**
 * 将各种格式的日期值解析为 Date 对象
 * @param {string|number|Date} value
 * @returns {Date}
 */
export function parseDateValue(value) {
  if (value instanceof Date) return value
  if (typeof value === 'number') return new Date(value)
  return new Date(value)
}

/**
 * 将 Date 对象格式化为 YYYY-MM-DD 字符串
 * @param {Date|string} date
 * @returns {string}
 */
export function formatDateStr(date) {
  const d = date instanceof Date ? date : new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 生成两个日期之间的日期序列
 * @param {string} start
 * @param {string} end
 * @returns {string[]} YYYY-MM-DD 格式的日期数组
 */
export function generateDateRange(start, end) {
  const dates = []
  const current = new Date(start)
  const endDate = new Date(end)
  while (current <= endDate) {
    dates.push(formatDateStr(current))
    current.setDate(current.getDate() + 1)
  }
  return dates
}

/**
 * 计算两个日期之间的天数差
 * @param {string|Date} date1
 * @param {string|Date} date2
 * @returns {number}
 */
export function getDaysBetween(date1, date2) {
  const d1 = parseDateValue(date1)
  const d2 = parseDateValue(date2)
  const diffMs = Math.abs(d2.getTime() - d1.getTime())
  return Math.floor(diffMs / (1000 * 60 * 60 * 24))
}

/**
 * 获取日期所在的周期标识
 * @param {string|Date} date
 * @param {'day'|'week'|'month'|'quarter'|'year'} period
 * @returns {string}
 */
export function getPeriodKey(date, period) {
  const d = parseDateValue(date)
  const year = d.getFullYear()
  const month = d.getMonth()

  switch (period) {
    case 'day':
      return formatDateStr(d)
    case 'week': {
      const firstDay = new Date(d)
      firstDay.setDate(d.getDate() - d.getDay())
      return formatDateStr(firstDay)
    }
    case 'month':
      return `${year}-${String(month + 1).padStart(2, '0')}`
    case 'quarter':
      return `${year}-Q${Math.floor(month / 3) + 1}`
    case 'year':
      return `${year}`
    default:
      return formatDateStr(d)
  }
}

/**
 * 获取相对时间描述
 * @param {string|Date} date
 * @param {Date} [now]
 * @returns {string}
 */
export function getRelativeTimeLabel(date, now = new Date()) {
  const d = parseDateValue(date)
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前`
  return `${Math.floor(diffDays / 365)}年前`
}

/**
 * 判断是否为工作日（周一~周五）
 * @param {string|Date} date
 * @returns {boolean}
 */
export function isBusinessDay(date) {
  const d = parseDateValue(date)
  const day = d.getDay()
  return day !== 0 && day !== 6
}

/**
 * 计算两个日期之间的工作日数
 * @param {string|Date} start
 * @param {string|Date} end
 * @returns {number}
 */
export function getBusinessDaysBetween(start, end) {
  const startDate = parseDateValue(start)
  const endDate = parseDateValue(end)
  let count = 0
  const current = new Date(startDate)
  while (current <= endDate) {
    if (isBusinessDay(current)) count++
    current.setDate(current.getDate() + 1)
  }
  return count
}

/**
 * 获取日期所在月份的第一天和最后一天
 * @param {string|Date} date
 * @returns {{ firstDay: string, lastDay: string }}
 */
export function getMonthBounds(date) {
  const d = parseDateValue(date)
  const firstDay = new Date(d.getFullYear(), d.getMonth(), 1)
  const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  return {
    firstDay: formatDateStr(firstDay),
    lastDay: formatDateStr(lastDay)
  }
}
