import React, { useState, useEffect, useCallback } from 'react'
import {
  Table, Button, Input, Select, Space, Modal, Form, Tag, message,
  Typography, InputNumber
} from 'antd'
import { PlusOutlined, SearchOutlined, EyeOutlined, StopOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { experimentApi, modelApi, datasetApi, type Experiment, type Model, type Dataset } from '../api'
import dayjs from 'dayjs'

const { Option } = Select
const { TextArea } = Input

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'default',
  RUNNING: 'processing',
  COMPLETED: 'success',
  FAILED: 'error',
  CANCELLED: 'warning',
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: '待执行',
  RUNNING: '执行中',
  COMPLETED: '已完成',
  FAILED: '失败',
  CANCELLED: '已取消',
}

export default function ExperimentsPage() {
  const navigate = useNavigate()
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [searchName, setSearchName] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | undefined>()

  // 创建弹窗
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [models, setModels] = useState<Model[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])

  const fetchExperiments = useCallback(async () => {
    setLoading(true)
    try {
      const res = await experimentApi.list({
        name: searchName || undefined,
        status: filterStatus,
        page,
        page_size: pageSize,
      })
      setExperiments(res.data.items)
      setTotal(res.data.total)
    } finally {
      setLoading(false)
    }
  }, [searchName, filterStatus, page, pageSize])

  useEffect(() => { fetchExperiments() }, [fetchExperiments])

  // 轮询刷新（有 RUNNING 状态时每 3 秒刷新）
  useEffect(() => {
    const hasRunning = experiments.some((e) => e.status === 'RUNNING')
    if (!hasRunning) return
    const timer = setInterval(fetchExperiments, 3000)
    return () => clearInterval(timer)
  }, [experiments, fetchExperiments])

  const handleCreate = async () => {
    form.resetFields()
    form.setFieldsValue({ concurrency: 5, timeout_seconds: 30 })
    // 加载模型和评测集列表
    try {
      const [mRes, dRes] = await Promise.all([
        modelApi.list({ status: 'ACTIVE', page: 1, page_size: 100 }),
        datasetApi.list({ page: 1, page_size: 100 }),
      ])
      setModels(mRes.data.items)
      setDatasets(dRes.data.items)
    } catch {}
    setModalOpen(true)
  }

  const handleCancel = async (id: number) => {
    try {
      await experimentApi.cancel(id)
      message.success('已发起取消')
      fetchExperiments()
    } catch {}
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      await experimentApi.create(values)
      message.success('评测实验已发起')
      setModalOpen(false)
      fetchExperiments()
    } catch {
    } finally {
      setSubmitting(false)
    }
  }

  const columns: ColumnsType<Experiment> = [
    { title: '实验名称', dataIndex: 'name', key: 'name', width: 180, ellipsis: true },
    {
      title: '关联模型', dataIndex: 'model_name', key: 'model_name', width: 140,
      render: (v, r) => r.model_deleted ? <span style={{ color: '#999' }}>{v}（已删除）</span> : v,
    },
    {
      title: '关联评测集', dataIndex: 'dataset_name', key: 'dataset_name', width: 160,
      render: (v, r) => r.dataset_deleted ? <span style={{ color: '#999' }}>{v}（已删除）</span> : v,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v) => <Tag color={STATUS_COLORS[v]}>{STATUS_LABELS[v] || v}</Tag>,
    },
    { title: '创建人', dataIndex: 'created_by', key: 'created_by', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160,
      render: (v) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '完成时间', dataIndex: 'completed_at', key: 'completed_at', width: 160,
      render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作', key: 'action', width: 140, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/experiments/${record.id}`)}>
            详情
          </Button>
          {record.status === 'RUNNING' && (
            <Button size="small" danger icon={<StopOutlined />} onClick={() => handleCancel(record.id)}>
              取消
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Typography.Title level={4} style={{ margin: 0 }}>评测实验</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>发起评测</Button>
      </div>

      <div className="search-bar">
        <Input
          placeholder="搜索实验名称"
          prefix={<SearchOutlined />}
          style={{ width: 220 }}
          value={searchName}
          onChange={(e) => { setSearchName(e.target.value); setPage(1) }}
          allowClear
        />
        <Select
          placeholder="状态筛选"
          style={{ width: 120 }}
          allowClear
          value={filterStatus}
          onChange={(v) => { setFilterStatus(v); setPage(1) }}
        >
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <Option key={k} value={k}>{v}</Option>
          ))}
        </Select>
      </div>

      <Table
        columns={columns}
        dataSource={experiments}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1100 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: false,
          showTotal: (t) => `共 ${t} 条`,
          onChange: setPage,
        }}
      />

      {/* 发起评测弹窗 */}
      <Modal
        title="发起评测实验"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="实验名称"
            rules={[{ required: true, message: '请输入实验名称' }, { max: 100, message: '最长 100 字符' }]}
          >
            <Input placeholder="请输入实验名称" />
          </Form.Item>
          <Form.Item
            name="model_id"
            label="选择模型"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Select placeholder="请选择模型" showSearch optionFilterProp="children">
              {models.map((m) => (
                <Option key={m.id} value={m.id}>{m.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="dataset_id"
            label="选择评测集"
            rules={[{ required: true, message: '请选择评测集' }]}
          >
            <Select placeholder="请选择评测集" showSearch optionFilterProp="children">
              {datasets.map((d) => (
                <Option key={d.id} value={d.id}>{d.name}（{d.item_count} 条）</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ max: 500, message: '最长 500 字符' }]}>
            <TextArea rows={2} placeholder="请输入描述（选填）" />
          </Form.Item>
          <Space style={{ width: '100%' }} size={16}>
            <Form.Item name="concurrency" label="并发数" style={{ flex: 1 }}>
              <InputNumber min={1} max={20} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="timeout_seconds" label="超时时间（秒）" style={{ flex: 1 }}>
              <InputNumber min={5} max={300} style={{ width: '100%' }} />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}
