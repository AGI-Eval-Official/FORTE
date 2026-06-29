import React, { useState, useEffect, useCallback } from 'react'
import {
  Table, Button, Tag, Space, Typography, Descriptions, Statistic, Row, Col,
  Card, Select, message, Breadcrumb, Spin, Modal
} from 'antd'
import { ArrowLeftOutlined, StopOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useParams, useNavigate } from 'react-router-dom'
import { experimentApi, type ExperimentDetail, type ExperimentResult } from '../api'
import dayjs from 'dayjs'

const { Option } = Select

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

export default function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const experimentId = Number(id)

  const [detail, setDetail] = useState<ExperimentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [resultStatus, setResultStatus] = useState<string | undefined>()
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  const fetchDetail = useCallback(async (p = page, rs = resultStatus) => {
    try {
      const res = await experimentApi.get(experimentId, { page: p, page_size: pageSize, result_status: rs })
      setDetail(res.data)
    } catch {
    } finally {
      setLoading(false)
    }
  }, [experimentId, page, pageSize, resultStatus])

  useEffect(() => { fetchDetail() }, [fetchDetail])

  // 轮询（执行中时每 3 秒刷新）
  useEffect(() => {
    if (detail?.status !== 'RUNNING') return
    const timer = setInterval(() => fetchDetail(), 3000)
    return () => clearInterval(timer)
  }, [detail?.status, fetchDetail])

  const handleCancel = async () => {
    try {
      await experimentApi.cancel(experimentId)
      message.success('已发起取消')
      fetchDetail()
    } catch {}
  }

  const handleExport = () => {
    const url = experimentApi.exportResults(experimentId)
    window.open(url, '_blank')
  }

  const resultColumns: ColumnsType<ExperimentResult> = [
    { title: '序号', dataIndex: 'seq', key: 'seq', width: 70 },
    {
      title: 'input',
      dataIndex: 'input_text',
      key: 'input_text',
      ellipsis: true,
      render: (v, r) => (
        <span
          style={{ cursor: 'pointer', color: '#1677ff' }}
          onClick={() => setExpandedRow(expandedRow === r.id ? null : r.id)}
        >
          {v}
        </span>
      ),
    },
    { title: 'expected_output', dataIndex: 'expected_output', key: 'expected_output', ellipsis: true, render: (v) => v || '-' },
    { title: 'actual_output', dataIndex: 'actual_output', key: 'actual_output', ellipsis: true, render: (v) => v || '-' },
    {
      title: '响应时间', dataIndex: 'response_time_ms', key: 'response_time_ms', width: 100,
      render: (v) => v != null ? `${v} ms` : '-',
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (v) => <Tag color={v === 'SUCCESS' ? 'success' : 'error'}>{v === 'SUCCESS' ? '成功' : '失败'}</Tag>,
    },
    {
      title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true,
      render: (v) => v ? <span style={{ color: '#ff4d4f' }}>{v}</span> : '-',
    },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!detail) return null

  const stats = detail.statistics

  return (
    <div className="page-container">
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <a onClick={() => navigate('/experiments')}>评测实验</a> },
          { title: detail.name },
        ]}
      />

      <div className="page-header">
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/experiments')}>返回</Button>
          <Typography.Title level={4} style={{ margin: 0 }}>{detail.name}</Typography.Title>
          <Tag color={STATUS_COLORS[detail.status]}>{STATUS_LABELS[detail.status] || detail.status}</Tag>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => fetchDetail()}>刷新</Button>
          {detail.status === 'RUNNING' && (
            <Button danger icon={<StopOutlined />} onClick={handleCancel}>取消实验</Button>
          )}
          {(detail.status === 'COMPLETED' || detail.status === 'CANCELLED') && (
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出结果</Button>
          )}
        </Space>
      </div>

      {/* 基本信息 */}
      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={3} size="small">
          <Descriptions.Item label="关联模型">
            {detail.model_name}
            {detail.model_deleted && <Tag color="default" style={{ marginLeft: 4 }}>已删除</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label="关联评测集">
            {detail.dataset_name}
            {detail.dataset_deleted && <Tag color="default" style={{ marginLeft: 4 }}>已删除</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label="并发数">{detail.concurrency}</Descriptions.Item>
          <Descriptions.Item label="超时时间">{detail.timeout_seconds} 秒</Descriptions.Item>
          <Descriptions.Item label="创建人">{detail.created_by}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{dayjs(detail.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          {detail.completed_at && (
            <Descriptions.Item label="完成时间">{dayjs(detail.completed_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          )}
          {detail.description && (
            <Descriptions.Item label="描述" span={3}>{detail.description}</Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* 统计指标 */}
      {stats.total_count != null && (
        <Card title="评测统计" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={4}>
              <Statistic title="总条数" value={stats.total_count} />
            </Col>
            <Col span={4}>
              <Statistic title="成功条数" value={stats.success_count ?? 0} valueStyle={{ color: '#52c41a' }} />
            </Col>
            <Col span={4}>
              <Statistic title="失败条数" value={stats.failed_count ?? 0} valueStyle={{ color: '#ff4d4f' }} />
            </Col>
            <Col span={4}>
              <Statistic title="平均响应时间" value={stats.avg_response_ms ?? '-'} suffix={stats.avg_response_ms != null ? 'ms' : ''} />
            </Col>
            <Col span={4}>
              <Statistic title="P50" value={stats.p50_ms ?? '-'} suffix={stats.p50_ms != null ? 'ms' : ''} />
            </Col>
            <Col span={4}>
              <Statistic title="P90 / P99" value={`${stats.p90_ms ?? '-'} / ${stats.p99_ms ?? '-'}`} suffix="ms" />
            </Col>
          </Row>
          <Typography.Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
            {stats.note}
          </Typography.Text>
        </Card>
      )}

      {/* 逐条结果 */}
      <Card
        title="逐条评测结果"
        extra={
          <Select
            placeholder="状态筛选"
            style={{ width: 120 }}
            allowClear
            value={resultStatus}
            onChange={(v) => {
              setResultStatus(v)
              setPage(1)
              fetchDetail(1, v)
            }}
          >
            <Option value="SUCCESS">成功</Option>
            <Option value="FAILED">失败</Option>
          </Select>
        }
      >
        <Table
          columns={resultColumns}
          dataSource={detail.results.items}
          rowKey="id"
          size="small"
          scroll={{ x: 1000 }}
          expandable={{
            expandedRowKeys: expandedRow != null ? [expandedRow] : [],
            expandedRowRender: (record) => (
              <div style={{ padding: '8px 0' }}>
                <Typography.Text strong>input：</Typography.Text>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: '4px 0 12px' }}>{record.input_text}</pre>
                {record.expected_output && (
                  <>
                    <Typography.Text strong>expected_output：</Typography.Text>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: '4px 0 12px' }}>{record.expected_output}</pre>
                  </>
                )}
                {record.actual_output && (
                  <>
                    <Typography.Text strong>actual_output：</Typography.Text>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: '4px 0' }}>{record.actual_output}</pre>
                  </>
                )}
              </div>
            ),
            onExpand: (expanded, record) => setExpandedRow(expanded ? record.id : null),
          }}
          pagination={{
            current: page,
            pageSize,
            total: detail.results.total,
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p) => {
              setPage(p)
              fetchDetail(p, resultStatus)
            },
          }}
        />
      </Card>
    </div>
  )
}
