/**
 * 数据看板 — 全局常量
 */

/** 指标计算精度（小数位数）*/
export const METRIC_PRECISION = 2

/** 默认分页大小 */
export const DEFAULT_PAGE_SIZE = 20

/** 图表颜色方案 */
export const CHART_COLORS = {
  primary: ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452'],
  semantic: {
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#1890ff'
  }
}

/** 图表类型枚举 */
export const CHART_TYPES = {
  LINE: 'line',
  BAR: 'bar',
  PIE: 'pie',
  SCATTER: 'scatter',
  AREA: 'area'
}

/** 聚合周期枚举 */
export const PERIOD_TYPES = {
  DAY: 'day',
  WEEK: 'week',
  MONTH: 'month',
  QUARTER: 'quarter',
  YEAR: 'year'
}

/** 指标类型枚举 */
export const METRIC_TYPES = {
  COUNT: 'count',
  SUM: 'sum',
  AVERAGE: 'average',
  RATE: 'rate',
  PERCENTILE: 'percentile'
}

/** 导出格式枚举 */
export const EXPORT_FORMATS = {
  CSV: 'csv',
  JSON: 'json',
  EXCEL: 'xlsx'
}

/** 数据验证规则 */
export const VALIDATION_RULES = {
  MAX_PAGE_SIZE: 100,
  MIN_PAGE_SIZE: 1,
  MAX_DATE_RANGE_DAYS: 365,
  MAX_EXPORT_ROWS: 10000
}

/** 统计分析配置 */
export const STATISTICS_CONFIG = {
  OUTLIER_THRESHOLD: 1.5,
  DEFAULT_MOVING_WINDOW: 7,
  CONFIDENCE_LEVEL: 0.95
}
