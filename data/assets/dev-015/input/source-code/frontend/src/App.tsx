import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { RobotOutlined, DatabaseOutlined, ExperimentOutlined } from '@ant-design/icons'
import ModelsPage from './pages/ModelsPage'
import DatasetsPage from './pages/DatasetsPage'
import ExperimentsPage from './pages/ExperimentsPage'
import ExperimentDetailPage from './pages/ExperimentDetailPage'

const { Header, Sider, Content } = Layout

const menuItems = [
  {
    key: '/models',
    icon: <RobotOutlined />,
    label: <Link to="/models">模型管理</Link>,
  },
  {
    key: '/datasets',
    icon: <DatabaseOutlined />,
    label: <Link to="/datasets">评测集管理</Link>,
  },
  {
    key: '/experiments',
    icon: <ExperimentOutlined />,
    label: <Link to="/experiments">评测实验</Link>,
  },
]

function AppLayout() {
  const location = useLocation()
  const selectedKey = '/' + location.pathname.split('/')[1]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={200} theme="dark">
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 16,
          fontWeight: 600,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          评测平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          style={{ marginTop: 8 }}
        />
      </Sider>
      <Layout>
        <Content style={{ background: '#f0f2f5', minHeight: '100vh' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/models" replace />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}
