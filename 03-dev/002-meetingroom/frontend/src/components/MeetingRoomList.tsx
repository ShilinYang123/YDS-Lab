import { useState, useEffect, useCallback } from 'react';
import { useMeetingRoomStore, type MeetingRoom } from '@/stores/meetingRoomStore';
import { useAuthStore } from '@/stores/authStore';
import { toast } from 'sonner';
import BookingForm from './BookingForm';
import BookingList from './BookingList';
import { 
  Building2 as BuildingOfficeIcon,
  Users as UsersIcon,
  Clock,
  CircleCheck as CheckCircleIcon,
  CircleX as XCircleIcon,
  TriangleAlert as ExclamationTriangleIcon,
  Ban as NoSymbolIcon,
  Banknote,
  CalendarPlus
} from 'lucide-react';

const statusConfig = {
  available: {
    label: '可用',
    icon: CheckCircleIcon,
    color: 'text-green-600 bg-green-100',
  },
  occupied: {
    label: '占用中',
    icon: XCircleIcon,
    color: 'text-red-600 bg-red-100',
  },
  maintenance: {
    label: '维护中',
    icon: ExclamationTriangleIcon,
    color: 'text-yellow-600 bg-yellow-100',
  },
  disabled: {
    label: '已禁用',
    icon: NoSymbolIcon,
    color: 'text-gray-600 bg-gray-100',
  },
};

export default function MeetingRoomList() {
  const { meetingRooms, fetchMeetingRooms, updateMeetingRoomStatus, isLoading } = useMeetingRoomStore();
  const { user } = useAuthStore();
  const [filters, setFilters] = useState({
    status: '',
    building: '',
    capacityMin: '',
    capacityMax: '',
  });
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [showBookingList, setShowBookingList] = useState<string | null>(null);



  const loadMeetingRooms = useCallback(async () => {
    try {
      await fetchMeetingRooms();
    } catch {
      toast.error('加载会议室列表失败');
    }
  }, [fetchMeetingRooms]);

  useEffect(() => {
    loadMeetingRooms();
  }, [loadMeetingRooms]);

  const handleStatusChange = async (roomId: string, newStatus: string) => {
    try {
      await updateMeetingRoomStatus(roomId, newStatus as MeetingRoom['status']);
      toast.success('会议室状态更新成功');
    } catch {
      toast.error('更新会议室状态失败');
    }
  };

  const handleBookingClick = (roomId: string) => {
    setSelectedRoom(roomId);
    setShowBookingForm(true);
  };

  const handleViewBookings = (roomId: string) => {
    setShowBookingList(roomId);
  };

  const handleBookingSuccess = () => {
    // 可以在这里添加刷新逻辑
    toast.success('预约创建成功');
  };

  const filteredRooms = meetingRooms.filter(room => {
    if (filters.status && room.status !== filters.status) return false;
    if (filters.building && !room.building.toLowerCase().includes(filters.building.toLowerCase())) return false;
    if (filters.capacityMin && room.capacity < parseInt(filters.capacityMin)) return false;
    if (filters.capacityMax && room.capacity > parseInt(filters.capacityMax)) return false;
    return true;
  });

  const uniqueBuildings = [...new Set(meetingRooms.map(room => room.building))];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 筛选器 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">筛选条件</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">全部状态</option>
              <option value="available">可用</option>
              <option value="occupied">占用中</option>
              <option value="maintenance">维护中</option>
              <option value="disabled">已禁用</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">建筑</label>
            <select
              value={filters.building}
              onChange={(e) => setFilters(prev => ({ ...prev, building: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">全部建筑</option>
              {uniqueBuildings.map(building => (
                <option key={building} value={building}>{building}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">最小容量</label>
            <input
              type="number"
              value={filters.capacityMin}
              onChange={(e) => setFilters(prev => ({ ...prev, capacityMin: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="最小人数"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">最大容量</label>
            <input
              type="number"
              value={filters.capacityMax}
              onChange={(e) => setFilters(prev => ({ ...prev, capacityMax: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="最大人数"
            />
          </div>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => setFilters({ status: '', building: '', capacityMin: '', capacityMax: '' })}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            重置筛选
          </button>
        </div>
      </div>

      {/* 会议室列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredRooms.map((room) => {
          const statusInfo = statusConfig[room.status];
          const StatusIcon = statusInfo.icon;
          
          return (
            <div key={room.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
              {/* 会议室图片占位符 */}
              <div className="h-48 bg-gradient-to-br from-blue-100 to-indigo-200 flex items-center justify-center">
                <BuildingOfficeIcon className="h-16 w-16 text-blue-500" />
              </div>
              
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">{room.name}</h3>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {statusInfo.label}
                  </span>
                </div>
                
                {room.description && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">{room.description}</p>
                )}
                
                <div className="space-y-2 mb-4">
                  <div className="flex items-center text-sm text-gray-500">
                    <BuildingOfficeIcon className="w-4 h-4 mr-2" />
                    <span>{room.building} - {room.location}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-500">
                    <UsersIcon className="w-4 h-4 mr-2" />
                    <span>容量: {room.capacity} 人</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="w-4 h-4 mr-2" />
                    <span>{room.openTime} - {room.closeTime}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-500">
                    <Banknote className="w-4 h-4 mr-2" />
                    <span>¥{room.hourlyRate}/小时</span>
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleBookingClick(room.id)}
                    disabled={room.status !== 'available'}
                    className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1"
                  >
                    <CalendarPlus className="w-4 h-4" />
                    预约
                  </button>
                  
                  <button
                    onClick={() => handleViewBookings(room.id)}
                    className="bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  >
                    预约记录
                  </button>
                  
                  {user?.role === 'admin' && (
                    <div className="relative">
                      <select
                        value={room.status}
                        onChange={(e) => handleStatusChange(room.id, e.target.value)}
                        className="bg-gray-100 text-gray-700 py-2 px-3 rounded-md text-sm border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="available">可用</option>
                        <option value="occupied">占用中</option>
                        <option value="maintenance">维护中</option>
                        <option value="disabled">禁用</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {filteredRooms.length === 0 && (
        <div className="text-center py-12">
          <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">没有找到会议室</h3>
          <p className="mt-1 text-sm text-gray-500">尝试调整筛选条件或联系管理员。</p>
        </div>
      )}
      
      {/* 预约表单模态框 */}
      {showBookingForm && selectedRoom && (
        <BookingForm
          roomId={selectedRoom}
          roomName={meetingRooms.find(room => room.id === selectedRoom)?.name || ''}
          onClose={() => {
            setShowBookingForm(false);
            setSelectedRoom(null);
          }}
          onSuccess={handleBookingSuccess}
        />
      )}
      
      {/* 预约列表模态框 */}
      {showBookingList && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                预约记录 - {meetingRooms.find(room => room.id === showBookingList)?.name}
              </h2>
              <button
                onClick={() => setShowBookingList(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XCircleIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <BookingList
                roomId={showBookingList}
                roomName={meetingRooms.find(room => room.id === showBookingList)?.name || ''}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}