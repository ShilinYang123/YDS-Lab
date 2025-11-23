import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Play, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  TrendingUp,
  Video
} from 'lucide-react'
import { toast } from 'sonner'

interface Stats {
  total_tasks: number
  pending_tasks: number
  processing_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
}

interface RecentTask {
  id: string
  name: string
  status: string
  task_type: string
  created_at: string
  processing_time?: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    fetchRecentTasks()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      } else {
        toast.error('获取统计数据失败')
      }
    } catch (error) {
      console.error('获取统计数据失败:', error)
      toast.error('网络连接失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchRecentTasks = async () => {
    try {
      const response = await fetch('/api/tasks?limit=5')
      if (response.ok) {
        const data = await response.json()
        setRecentTasks(data)
      }
    } catch (error) {
      console.error('获取最近任务失败:', error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'processing':
        return <Play className="w-5 h-5 text-blue-500" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">仪表盘</h1>
          <p className="text-gray-600 mt-1">数字员工系统运行概览</p>
        </div>
        <Link
          to="/tasks"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          创建新任务
        </Link>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">总任务数</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_tasks}</p>
              </div>
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">待处理</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending_tasks}</p>
              </div>
              <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">处理中</p>
                <p className="text-2xl font-bold text-blue-600">{stats.processing_tasks}</p>
              </div>
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg">
                <Play className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">成功率</p>
                <p className="text-2xl font-bold text-green-600">{stats.success_rate}%</p>
              </div>
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 最近任务 */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">最近任务</h2>
          <p className="text-sm text-gray-600 mt-1">最近创建的任务列表</p>
        </div>
        
        <div className="divide-y">
          {recentTasks.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Video className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无任务记录</p>
              <Link
                to="/tasks"
                className="inline-block mt-4 text-blue-600 hover:text-blue-700"
              >
                创建第一个任务
              </Link>
            </div>
          ) : (
            recentTasks.map((task) => (
              <div key={task.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(task.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{task.name}</h3>
                      <p className="text-sm text-gray-600 capitalize">{task.task_type.replace('_', ' ')}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(task.status)}`}>
                      {task.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        
        {recentTasks.length > 0 && (
          <div className="p-4 border-t">
            <Link
              to="/tasks"
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              查看所有任务 →
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard