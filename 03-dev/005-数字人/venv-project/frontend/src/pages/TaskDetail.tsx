import React from 'react'
import { useParams } from 'react-router-dom'

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">任务详情</h1>
      <p className="text-gray-600 mt-2">任务ID: {id}</p>
      <div className="mt-6 bg-white rounded-lg shadow-sm border p-8 text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-4">任务详情功能开发中</h3>
        <p className="text-gray-600">此页面正在开发中，敬请期待...</p>
      </div>
    </div>
  )
}

export default TaskDetail