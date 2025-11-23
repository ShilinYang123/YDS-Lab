import { useState, useEffect, useCallback } from 'react'
import { useMeetingRoomStore, Booking } from '../stores/meetingRoomStore'
import { Calendar, Clock, Users, X, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

interface BookingListProps {
  roomId: string
  roomName: string
}

export default function BookingList({ roomId, roomName }: BookingListProps) {
  const { currentBookings, fetchBookings, cancelBooking, isLoading } = useMeetingRoomStore()
  const [isRefreshing, setIsRefreshing] = useState(false)

  

  const loadBookings = useCallback(async () => {
    try {
      setIsRefreshing(true)
      await fetchBookings(roomId)
    } catch {
      toast.error('加载预约列表失败')
    } finally {
      setIsRefreshing(false)
    }
  }, [roomId, fetchBookings])

  useEffect(() => {
    loadBookings()
  }, [loadBookings])

  const handleCancelBooking = async (bookingId: string) => {
    if (!confirm('确定要取消这个预约吗？')) {
      return
    }

    try {
      await cancelBooking(bookingId)
      toast.success('预约已取消')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '取消预约失败'
      toast.error(errorMessage)
    }
  }

  const formatDateTime = (dateTime: string) => {
    const date = new Date(dateTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status: Booking['status']) => {
    switch (status) {
      case 'confirmed':
        return 'text-green-600 bg-green-100'
      case 'pending':
        return 'text-yellow-600 bg-yellow-100'
      case 'cancelled':
        return 'text-red-600 bg-red-100'
      case 'completed':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusText = (status: Booking['status']) => {
    switch (status) {
      case 'confirmed':
        return '已确认'
      case 'pending':
        return '待确认'
      case 'cancelled':
        return '已取消'
      case 'completed':
        return '已完成'
      default:
        return '未知'
    }
  }

  const isBookingExpired = (endTime: string) => {
    return new Date(endTime) < new Date()
  }

  const canCancelBooking = (booking: Booking) => {
    return booking.status === 'pending' || booking.status === 'confirmed' && !isBookingExpired(booking.endTime)
  }

  if (isLoading && currentBookings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">加载中...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">预约记录</h3>
          <button
            onClick={loadBookings}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
          >
            <Calendar className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>
        <p className="text-sm text-gray-600 mt-1">{roomName} 的预约记录</p>
      </div>

      <div className="p-6">
        {currentBookings.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">暂无预约记录</p>
            <p className="text-sm text-gray-400 mt-1">点击"预约会议室"创建新的预约</p>
          </div>
        ) : (
          <div className="space-y-4">
            {currentBookings.map((booking) => (
              <div key={booking.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 mb-1">{booking.title}</h4>
                    {booking.description && (
                      <p className="text-sm text-gray-600 mb-2">{booking.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDateTime(booking.startTime)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{formatDateTime(booking.endTime)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(booking.status)}`}>
                      {getStatusText(booking.status)}
                    </span>
                    {isBookingExpired(booking.endTime) && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        已过期
                      </span>
                    )}
                  </div>
                </div>

                {booking.participants && booking.participants.length > 0 && (
                  <div className="mb-3">
                    <div className="flex items-center gap-1 text-sm text-gray-600 mb-1">
                      <Users className="w-4 h-4" />
                      <span>参与人员 ({booking.participants.length})</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {booking.participants.slice(0, 3).map((email, index) => (
                        <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          {email}
                        </span>
                      ))}
                      {booking.participants.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          +{booking.participants.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {booking.user && (
                  <div className="mb-3 text-sm text-gray-600">
                    <span>预约人：{booking.user.name} ({booking.user.email})</span>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>创建时间：{formatDateTime(booking.createdAt)}</span>
                  {canCancelBooking(booking) && (
                    <button
                      onClick={() => handleCancelBooking(booking.id)}
                      className="flex items-center gap-1 px-2 py-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                      disabled={isLoading}
                    >
                      <X className="w-3 h-3" />
                      取消预约
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}