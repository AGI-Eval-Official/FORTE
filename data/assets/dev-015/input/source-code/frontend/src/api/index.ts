import axios from 'axios'
import { message } from 'antd'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-User-Id': 'user_001',
  },
})

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code !== 0) {
      message.error(data.message || '操作失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || '网络错误'
    message.error(msg)
    return Promise.reject(error)
  }
)

export default api

// ==================== 模型管理 ====================

export interface Model {
  id: number
  name: string
  model_type: string
  version?: string
  description?: string
  endpoint_url?: string
  api_key_masked?: string
  status: string
  created_by: string
  updated_by?: string
  created_at: string
  updated_at: string
}

export interface ModelListParams {
  name?: string
  model_type?: string
  status?: string
  page?: number
  page_size?: number
}

export interface PageResult<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export const modelApi = {
  list: (params: ModelListParams) =>
    api.get<any, { code: number; data: PageResult<Model> }>('/models', { params }),

  create: (data: Partial<Model> & { api_key?: string }) =>
    api.post<any, { code: number; data: Model }>('/models', data),

  get: (id: number) =>
    api.get<any, { code: number; data: Model & { recent_experiments: any[] } }>(`/models/${id}`),

  update: (id: number, data: Partial<Model> & { api_key?: string }) =>
    api.put<any, { code: number; data: Model }>(`/models/${id}`, data),

  delete: (id: number) =>
    api.delete<any, { code: number; data: any }>(`/models/${id}`),
}

// ==================== 评测集管理 ====================

export interface Dataset {
  id: number
  name: string
  version?: string
  description?: string
  item_count: number
  created_by: string
  updated_by?: string
  created_at: string
  updated_at: string
}

export interface DatasetItem {
  id: number
  seq: number
  input_text: string
  expected_output?: string
}

export const datasetApi = {
  list: (params: { name?: string; page?: number; page_size?: number }) =>
    api.get<any, { code: number; data: PageResult<Dataset> }>('/datasets', { params }),

  create: (data: Partial<Dataset>) =>
    api.post<any, { code: number; data: Dataset }>('/datasets', data),

  get: (id: number) =>
    api.get<any, { code: number; data: Dataset & { recent_experiments: any[] } }>(`/datasets/${id}`),

  update: (id: number, data: Partial<Dataset>) =>
    api.put<any, { code: number; data: Dataset }>(`/datasets/${id}`, data),

  delete: (id: number) =>
    api.delete<any, { code: number; data: any }>(`/datasets/${id}`),

  importItems: (id: number, file: File, mode: 'append' | 'overwrite') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('mode', mode)
    return api.post<any, { code: number; data: any }>(`/datasets/${id}/items/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  listItems: (id: number, params: { page?: number; page_size?: number }) =>
    api.get<any, { code: number; data: PageResult<DatasetItem> }>(`/datasets/${id}/items`, { params }),
}

// ==================== 评测实验 ====================

export interface Experiment {
  id: number
  name: string
  model_id: number
  model_name?: string
  model_deleted?: boolean
  dataset_id: number
  dataset_name?: string
  dataset_deleted?: boolean
  description?: string
  concurrency: number
  timeout_seconds: number
  status: string
  created_by: string
  created_at: string
  completed_at?: string
}

export interface ExperimentResult {
  id: number
  seq: number
  input_text: string
  expected_output?: string
  actual_output?: string
  response_time_ms?: number
  status: string
  error_message?: string
}

export interface ExperimentDetail extends Experiment {
  statistics: {
    total_count?: number
    success_count?: number
    failed_count?: number
    avg_response_ms?: number
    p50_ms?: number
    p90_ms?: number
    p99_ms?: number
    note: string
  }
  results: PageResult<ExperimentResult>
}

export const experimentApi = {
  list: (params: { name?: string; status?: string; page?: number; page_size?: number }) =>
    api.get<any, { code: number; data: PageResult<Experiment> }>('/experiments', { params }),

  create: (data: {
    name: string
    model_id: number
    dataset_id: number
    description?: string
    concurrency?: number
    timeout_seconds?: number
  }) => api.post<any, { code: number; data: Experiment }>('/experiments', data),

  get: (id: number, params?: { page?: number; page_size?: number; result_status?: string }) =>
    api.get<any, { code: number; data: ExperimentDetail }>(`/experiments/${id}`, { params }),

  cancel: (id: number) =>
    api.post<any, { code: number; data: any }>(`/experiments/${id}/cancel`),

  listResults: (id: number, params: { page?: number; page_size?: number; result_status?: string }) =>
    api.get<any, { code: number; data: PageResult<ExperimentResult> }>(`/experiments/${id}/results`, { params }),

  exportResults: (id: number) =>
    `/api/v1/experiments/${id}/results/export`,
}
