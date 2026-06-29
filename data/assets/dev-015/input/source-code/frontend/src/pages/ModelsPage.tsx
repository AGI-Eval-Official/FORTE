import React, { useState, useEffect, useCallback } from 'react'
import {
  Table, Button, Input, Select, Space, Modal, Form, Tag, message,
  Popconfirm, Drawer, Descriptions, Typography, Badge
} from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { modelApi, type Model } from '../api'
import dayjs from 'dayjs'

const { Option } = Select
const { TextArea } = Input

const MODEL_TYPE_LABELS: Record<string, string> = {
  LLM: 'LLM',
  CLASSIFICATION: '分类模型',
  REGRESSION: '回归模型',
  OTHER: '其他',
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'green',
  DISABLED: 'red',
}

export default function ModelsPage() {
  const [models, setModels] = useState<Model[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [searchName, setSearchName] = useState('')
  const [filterType, setFilterType] = useState<string | undefined>()
  const [filterStatus, setFilterStatus] = useState<string | undefined>()

  // 创建/编辑弹窗
  const [modalOpen, setModalOpen] = useState(false)
  const [editingModel, setEditingModel] = useState<Model | null>(null)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  // 详情抽屉
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailModel, setDetailModel] = useState<any>(null)

  const fetchModels = useCallback(async () => {
    setLoading(true)
    try {
      const res = await modelApi.list({
        name: searchName || undefined,
        model_type: filterType,
        status: filterStatus,
        page,
        page_size: pageSize,
      })
      setModels(res.data.items)
      setTotal(res.data.total)
    } finally {
      setLoading(false)
    }
  }, [searchName, filterType, filterStatus, page, pageSize])

  useEffect(() => {
    fetchModels()
  }, [fetchModels])

  const handleCreate = () => {
    setEditingModel(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: Model) => {
    setEditingModel(record)
    form.setFieldsValue({
      model_type: record.model_type,
      version: record.version,
      description: record.description,
      endpoint_url: record.endpoint_url,
      status: record.status,
    })
    setModalOpen(true)
  }

  const handleViewDetail = async (record: Model) => {
    try {
      const res = await modelApi.get(record.id)
      setDetailModel(res.data)
      setDrawerOpen(true)
    } catch {}
  }

  const handleDelete = async (id: number) => {
    try {
      await modelApi.delete(id)
      message.success('删除成功')
      fetchModels()
    } catch {}
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      if (editingModel) {
        await modelApi.update(editingModel.id, values)
        message.success('更新成功')
      } else {
        await modelApi.create(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchModels()
    } catch {
    } finally {
      setSubmitting(false)
    }
  }

  const columns: ColumnsType<Model> = [
    { title: '模型名称', dataIndex: 'name', key: 'name', width: 160 },
    {
      title: '模型类型', dataIndex: 'model_type', key: 'model_type', width: 120,
      render: (v) => MODEL_TYPE_LABELS[v] || v,
    },
    { title: '版本号', dataIndex: 'version', key: 'version', width: 100 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '创建人', dataIndex: 'created_by', key: 'created_by', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160,
      render: (v) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (v) => <Tag color={STATUS_COLORS[v]}>{v === 'ACTIVE' ? '启用' : '禁用'}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 160, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确认删除该模型？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Typography.Title level={4} style={{ margin: 0 }}>模型管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>创建模型</Button>
      </div>

      <div className="search-bar">
        <Input
          placeholder="搜索模型名称"
          prefix={<SearchOutlined />}
          style={{ width: 220 }}
          value={searchName}
          onChange={(e) => { setSearchName(e.target.value); setPage(1) }}
          allowClear
        />
        <Select
          placeholder="模型类型"
          style={{ width: 140 }}
          allowClear
          value={filterType}
          onChange={(v) => { setFilterType(v); setPage(1) }}
        >
          {Object.entries(MODEL_TYPE_LABELS).map(([k, v]) => (
            <Option key={k} value={k}>{v}</Option>
          ))}
        </Select>
        <Select
          placeholder="状态"
          style={{ width: 100 }}
          allowClear
          value={filterStatus}
          onChange={(v) => { setFilterStatus(v); setPage(1) }}
        >
          <Option value="ACTIVE">启用</Option>
          <Option value="DISABLED">禁用</Option>
        </Select>
      </div>

      <Table
        columns={columns}
        dataSource={models}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1000 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: false,
          showTotal: (t) => `共 ${t} 条`,
          onChange: setPage,
        }}
      />

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingModel ? '编辑模型' : '创建模型'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          {!editingModel && (
            <Form.Item
              name="name"
              label="模型名称"
              rules={[
                { required: true, message: '请输入模型名称' },
                { max: 100, message: '最长 100 字符' },
              ]}
            >
              <Input placeholder="请输入模型名称" />
            </Form.Item>
          )}
          <Form.Item
            name="model_type"
            label="模型类型"
            rules={[{ required: !editingModel, message: '请选择模型类型' }]}
          >
            <Select placeholder="请选择模型类型">
              {Object.entries(MODEL_TYPE_LABELS).map(([k, v]) => (
                <Option key={k} value={k}>{v}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="version"
            label="版本号"
            rules={[{ pattern: /^v\d+\.\d+\.\d+$/, message: '格式应为 vX.Y.Z，如 v1.0.0' }]}
          >
            <Input placeholder="如 v1.0.0" />
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ max: 500, message: '最长 500 字符' }]}>
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item name="endpoint_url" label="模型端点 URL">
            <Input placeholder="https://..." />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder="输入新 API Key（留空则不修改）" />
          </Form.Item>
          {editingModel && (
            <Form.Item name="status" label="状态">
              <Select>
                <Option value="ACTIVE">启用</Option>
                <Option value="DISABLED">禁用</Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title="模型详情"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={600}
      >
        {detailModel && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="模型名称" span={2}>{detailModel.name}</Descriptions.Item>
              <Descriptions.Item label="模型类型">{MODEL_TYPE_LABELS[detailModel.model_type] || detailModel.model_type}</Descriptions.Item>
              <Descriptions.Item label="版本号">{detailModel.version || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_COLORS[detailModel.status]}>{detailModel.status === 'ACTIVE' ? '启用' : '禁用'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="API Key">{detailModel.api_key_masked || '-'}</Descriptions.Item>
              <Descriptions.Item label="端点 URL" span={2}>{detailModel.endpoint_url || '-'}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{detailModel.description || '-'}</Descriptions.Item>
              <Descriptions.Item label="创建人">{detailModel.created_by}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(detailModel.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
            </Descriptions>

            {detailModel.recent_experiments?.length > 0 && (
              <>
                <Typography.Title level={5} style={{ marginTop: 24, marginBottom: 12 }}>关联实验历史（最近 10 条）</Typography.Title>
                <Table
                  size="small"
                  dataSource={detailModel.recent_experiments}
                  rowKey="id"
                  pagination={false}
                  columns={[
                    { title: 'ID', dataIndex: 'id', width: 60 },
                    { title: '实验名称', dataIndex: 'name', ellipsis: true },
                    { title: '状态', dataIndex: 'status', width: 90 },
                    { title: '创建时间', dataIndex: 'created_at', width: 140, render: (v) => v ? dayjs(v).format('MM-DD HH:mm') : '-' },
                  ]}
                />
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  )
}
