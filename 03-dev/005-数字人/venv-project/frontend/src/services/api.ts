import { TaskCreate, TaskResponse } from '../types/task'

const API_BASE = '/api'

class TaskService {
  // 获取任务列表
  async getTasks(params?: { skip?: number; limit?: number; status?: string }): Promise<TaskResponse[]> {
    const queryParams = new URLSearchParams()
    if (params?.skip) queryParams.append('skip', params.skip.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.status) queryParams.append('status', params.status)

    const response = await fetch(`${API_BASE}/tasks?${queryParams}`)
    if (!response.ok) {
      throw new Error('获取任务列表失败')
    }
    return response.json()
  }

  // 获取任务详情
  async getTask(id: string): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE}/tasks/${id}`)
    if (!response.ok) {
      throw new Error('获取任务详情失败')
    }
    return response.json()
  }

  // 创建任务
  async createTask(task: TaskCreate): Promise<TaskResponse> {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(task),
    })
    if (!response.ok) {
      throw new Error('创建任务失败')
    }
    return response.json()
  }

  // 取消任务
  async cancelTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/tasks/${id}/cancel`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error('取消任务失败')
    }
  }

  // 获取统计数据
  async getStats(): Promise<{
    total_tasks: number
    pending_tasks: number
    processing_tasks: number
    completed_tasks: number
    failed_tasks: number
    success_rate: number
  }> {
    const response = await fetch(`${API_BASE}/stats`)
    if (!response.ok) {
      throw new Error('获取统计数据失败')
    }
    return response.json()
  }

  // 获取队列状态
  async getQueueStatus(): Promise<{
    queue_length: number
    processing_tasks: number
    timestamp: string
  }> {
    const response = await fetch(`${API_BASE}/queue/status`)
    if (!response.ok) {
      throw new Error('获取队列状态失败')
    }
    return response.json()
  }
}

// 文件上传服务
class FileService {
  // 上传视频文件
  async uploadVideo(file: File): Promise<{
    filename: string
    path: string
    size: number
    url: string
  }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/upload/video`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error('上传视频失败')
    }
    return response.json()
  }

  // 上传音频文件
  async uploadAudio(file: File): Promise<{
    filename: string
    path: string
    size: number
    url: string
  }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/upload/audio`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error('上传音频失败')
    }
    return response.json()
  }
}

export const taskService = new TaskService()
export const fileService = new FileService()