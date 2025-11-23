import { useState } from 'react'
import { useMeetingRoomStore, CreateBookingData } from '../stores/meetingRoomStore'
import { Calendar, Clock, Users, X } from 'lucide-react'
import { toast } from 'sonner'

interface BookingFormProps {
  roomId: string
  roomName: string
  onClose: () => void
  onSuccess?: () => void
}

export default function BookingForm({ roomId, roomName, onClose, onSuccess }: BookingFormProps) {
  const { createBooking, isLoading } = useMeetingRoomStore()
  
  const [formData, setFormData] = useState<CreateBookingData>({
    roomId,
    startTime: '',
    endTime: '',
    title: '',
    description: '',
    participants: []
  })
  
  const [participantsInput, setParticipantsInput] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.startTime || !formData.endTime) {
      toast.error('请选择预约时间')
      return
    }
    
    if (new Date(formData.startTime) >= new Date(formData.endTime)) {
      toast.error('结束时间必须晚于开始时间')
      return
    }
    
    if (!formData.title.trim()) {
      toast.error('请输入会议标题')
      return
    }

    try {
      await createBooking(formData)
      toast.success('预约创建成功')
      onSuccess?.()
      onClose()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '预约创建失败'
      toast.error(errorMessage)
    }
  }

  const addParticipant = () => {
    const email = participantsInput.trim()
    if (email && !formData.participants?.includes(email)) {
      setFormData(prev => ({
        ...prev,
        participants: [...(prev.participants || []), email]
      }))
      setParticipantsInput('')
    }
  }

  const removeParticipant = (email: string) => {
    setFormData(prev => ({
      ...prev,
      participants: prev.participants?.filter(p => p !== email) || []
    }))
  }

  const getMinDateTime = () => {
    const now = new Date()
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
    return now.toISOString().slice(0, 16)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">预约会议室</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>会议室：</strong>{roomName}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Calendar className="w-4 h-4 inline mr-1" />
              开始时间
            </label>
            <input
              type="datetime-local"
              value={formData.startTime}
              onChange={(e) => setFormData(prev => ({ ...prev, startTime: e.target.value }))}
              min={getMinDateTime()}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Clock className="w-4 h-4 inline mr-1" />
              结束时间
            </label>
            <input
              type="datetime-local"
              value={formData.endTime}
              onChange={(e) => setFormData(prev => ({ ...prev, endTime: e.target.value }))}
              min={formData.startTime || getMinDateTime()}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              会议标题
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="请输入会议标题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              会议描述
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="请输入会议描述（可选）"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Users className="w-4 h-4 inline mr-1" />
              参与人员
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="email"
                value={participantsInput}
                onChange={(e) => setParticipantsInput(e.target.value)}
                placeholder="输入邮箱地址"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addParticipant()
                  }
                }}
              />
              <button
                type="button"
                onClick={addParticipant}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                添加
              </button>
            </div>
            
            {formData.participants && formData.participants.length > 0 && (
              <div className="space-y-1">
                {formData.participants.map((email) => (
                  <div key={email} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded">
                    <span className="text-sm text-gray-700">{email}</span>
                    <button
                      type="button"
                      onClick={() => removeParticipant(email)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              disabled={isLoading}
            >
              取消
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? '创建中...' : '创建预约'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}