import React, { useState, useEffect, useCallback } from 'react'
import {
  Table, Button, Input, Space, Modal, Form, message, Popconfirm,
  Drawer, Descriptions, Typography, Upload, Radio, Tabs
} from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, EyeOutlined, UploadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { UploadFile } from 'antd/es/upload'
import { datasetApi, type Dataset, type DatasetItem } from '../api'
import dayjs from 'dayjs'

const { TextArea } = Input

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [searchName, setSearchName] = useState('')

  // 创建/编辑弹窗
  const [modalOpen, setModalOpen] = useState(false)
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  // 导入弹窗
  const [importOpen, setImportOpen] = useState(false)
  const [importDatasetId, setImportDatasetId] = useState<number | null>(null)
  const [importMode, setImportMode] = useState<'append' | 'overwrite'>('append')
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [importing, setImporting] = useState(false)

  // 详情抽屉
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [detailDataset, setDetailDataset] = useState<any>(null)
  const [items, setItems] = useState<DatasetItem[]>([])
  const [itemsTotal, setItemsTotal] = useState(0)
  const [itemsPage, setItemsPage] = useState(1)
  const [itemsLoading, setItemsLoading] = useState(false)

  const fetchDatasets = useCallback(async () => {
    setLoading(true)
    try {
      const res = await datasetApi.list({ name: searchName || undefined, page, page_size: pageSize })
      setDatasets(res.data.items)
      setTotal(res.data.total)
    } finally {
      setLoading(false)
    }
  }, [searchName, page, pageSize])

  useEffect(() => { fetchDatasets() }, [fetchDatasets])

  const fetchItems = useCallback(async (datasetId: number, p: number) => {
    setItemsLoading(true)
    try {
      const res = await datasetApi.listItems(datasetId, { page: p, page_size: 50 })
      setItems(res.data.items)
      setItemsTotal(res.data.total)
    } finally {
      setItemsLoading(false)
    }
  }, [])

  const handleCreate = () => {
    setEditingDataset(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: Dataset) => {
    setEditingDataset(record)
    form.setFieldsValue({ name: record.name, version: record.version, description: record.description })
    setModalOpen(true)
  }

  const handleViewDetail = async (record: Dataset) => {
    try {
      const res = await datasetApi.get(record.id)
      setDetailDataset(res.data)
      setItemsPage(1)
      await fetchItems(record.id, 1)
      setDrawerOpen(true)
    } catch {}
  }

  const handleDelete = async (id: number) => {
    try {
      await datasetApi.delete(id)
      message.success('删除成功')
      fetchDatasets()
    } catch {}
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      if (editingDataset) {
        await datasetApi.update(editingDataset.id, values)
        message.success('更新成功')
      } else {
        await datasetApi.create(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchDatasets()
    } catch {
    } finally {
      setSubmitting(false)
    }
  }

  const handleOpenImport = (id: number) => {
    setImportDatasetId(id)
    setImportMode('append')
    setFileList([])
    setImportOpen(true)
  }

  const handleImport = async () => {
    if (!fileList.length || !importDatasetId) {
      message.warning('请选择 JSON 文件')
      return
    }
    const file = fileList[0].originFileObj as File
    setImporting(true)
    try {
      const res = await datasetApi.importItems(importDatasetId, file, importMode)
      message.success(`导入成功，共导入 ${res.data.imported_count} 条，总计 ${res.data.total_count} 条`)
      setImportOpen(false)
      fetchDatasets()
    } catch {
    } finally {
      setImporting(false)
    }
  }

  const columns: ColumnsType<Dataset> = [
    { title: '评测集名称', dataIndex: 'name', key: 'name', width: 180 },
    { title: '数据量', dataIndex: 'item_count', key: 'item_count', width: 90, render: (v) => `${v} 条` },
    { title: '版本号', dataIndex: 'version', key: 'version', width: 100 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '创建人', dataIndex: 'created_by', key: 'created_by', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160,
      render: (v) => dayjs(v).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作', key: 'action', width: 220, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
          <Button size="small" icon={<UploadOutlined />} onClick={() => handleOpenImport(record.id)}>导入</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确认删除该评测集？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const itemColumns: ColumnsType<DatasetItem> = [
    { title: '序号', dataIndex: 'seq', key: 'seq', width: 70 },
    { title: 'input', dataIndex: 'input_text', key: 'input_text', ellipsis: true },
    { title: 'expected_output', dataIndex: 'expected_output', key: 'expected_output', ellipsis: true, render: (v) => v || '-' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <Typography.Title level={4} style={{ margin: 0 }}>评测集管理</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>创建评测集</Button>
      </div>

      <div className="search-bar">
        <Input
          placeholder="搜索评测集名称"
          prefix={<SearchOutlined />}
          style={{ width: 220 }}
          value={searchName}
          onChange={(e) => { setSearchName(e.target.value); setPage(1) }}
          allowClear
        />
      </div>

      <Table
        columns={columns}
        dataSource={datasets}
        rowKey="id"
        loading={loading}
        scroll={{ x: 900 }}
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
        title={editingDataset ? '编辑评测集' : '创建评测集'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitting}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="评测集名称"
            rules={[
              { required: true, message: '请输入评测集名称' },
              { max: 100, message: '最长 100 字符' },
            ]}
          >
            <Input placeholder="请输入评测集名称" />
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
        </Form>
      </Modal>

      {/* 导入数据弹窗 */}
      <Modal
        title="导入评测集数据"
        open={importOpen}
        onOk={handleImport}
        onCancel={() => setImportOpen(false)}
        confirmLoading={importing}
        okText="开始导入"
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <Typography.Text strong>导入模式：</Typography.Text>
            <Radio.Group value={importMode} onChange={(e) => setImportMode(e.target.value)} style={{ marginLeft: 12 }}>
              <Radio value="append">追加（保留现有数据）</Radio>
              <Radio value="overwrite">覆盖（清空后重新导入）</Radio>
            </Radio.Group>
          </div>
          <Upload
            accept=".json"
            maxCount={1}
            fileList={fileList}
            beforeUpload={() => false}
            onChange={({ fileList: fl }) => setFileList(fl)}
          >
            <Button icon={<UploadOutlined />}>选择 JSON 文件（最大 50MB）</Button>
          </Upload>
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            JSON 格式：数组，每个元素包含 input（必填）和 expected_output（选填）字段
          </Typography.Text>
        </div>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title="评测集详情"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={700}
      >
        {detailDataset && (
          <Tabs
            items={[
              {
                key: 'info',
                label: '基本信息',
                children: (
                  <>
                    <Descriptions column={2} bordered size="small">
                      <Descriptions.Item label="评测集名称" span={2}>{detailDataset.name}</Descriptions.Item>
                      <Descriptions.Item label="版本号">{detailDataset.version || '-'}</Descriptions.Item>
                      <Descriptions.Item label="数据量">{detailDataset.item_count} 条</Descriptions.Item>
                      <Descriptions.Item label="描述" span={2}>{detailDataset.description || '-'}</Descriptions.Item>
                      <Descriptions.Item label="创建人">{detailDataset.created_by}</Descriptions.Item>
                      <Descriptions.Item label="创建时间">{dayjs(detailDataset.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
                    </Descriptions>
                    {detailDataset.recent_experiments?.length > 0 && (
                      <>
                        <Typography.Title level={5} style={{ marginTop: 24, marginBottom: 12 }}>关联实验历史</Typography.Title>
                        <Table
                          size="small"
                          dataSource={detailDataset.recent_experiments}
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
                ),
              },
              {
                key: 'data',
                label: `数据条目（${detailDataset.item_count} 条）`,
                children: (
                  <Table
                    columns={itemColumns}
                    dataSource={items}
                    rowKey="id"
                    loading={itemsLoading}
                    size="small"
                    pagination={{
                      current: itemsPage,
                      pageSize: 50,
                      total: itemsTotal,
                      showSizeChanger: false,
                      showTotal: (t) => `共 ${t} 条`,
                      onChange: (p) => {
                        setItemsPage(p)
                        fetchItems(detailDataset.id, p)
                      },
                    }}
                  />
                ),
              },
            ]}
          />
        )}
      </Drawer>
    </div>
  )
}
