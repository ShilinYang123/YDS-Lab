import { create } from 'zustand'
import { useAuthStore } from './authStore'

export interface MeetingRoom {
  id: string;
  name: string;
  description?: string;
  capacity: number;
  location: string;
  floor: number;
  building: string;
  equipment: string[];
  images: string[];
  status: 'available' | 'occupied' | 'maintenance' | 'disabled';
  hourlyRate: number;
  openTime: string;
  closeTime: string;
  workingDays: number[];
  managerId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateMeetingRoomData {
  name: string;
  description?: string;
  capacity: number;
  location: string;
  floor: number;
  building: string;
  equipment?: string[];
  images?: string[];
  hourlyRate: number;
  openTime: string;
  closeTime: string;
  workingDays?: number[];
  managerId: string;
}

export interface Booking {
  id: string;
  roomId: string;
  userId: string;
  startTime: string;
  endTime: string;
  title: string;
  description?: string;
  participants: string[];
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  createdAt: string;
  updatedAt: string;
  user?: {
    id: string;
    name: string;
    email: string;
  };
}

export interface CreateBookingData {
  roomId: string;
  startTime: string;
  endTime: string;
  title: string;
  description?: string;
  participants?: string[];
}

interface MeetingRoomState {
  meetingRooms: MeetingRoom[];
  currentRoom: MeetingRoom | null;
  currentBookings: Booking[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchMeetingRooms: (filters?: Record<string, unknown>) => Promise<void>;
  fetchMeetingRoomById: (id: string) => Promise<void>;
  createMeetingRoom: (data: CreateMeetingRoomData) => Promise<void>;
  updateMeetingRoom: (id: string, data: Partial<CreateMeetingRoomData>) => Promise<void>;
  deleteMeetingRoom: (id: string) => Promise<void>;
  updateMeetingRoomStatus: (id: string, status: MeetingRoom['status']) => Promise<void>;
  searchMeetingRooms: (query: string) => Promise<void>;
  
  // Booking actions
  fetchBookings: (roomId: string) => Promise<void>;
  createBooking: (data: CreateBookingData) => Promise<void>;
  cancelBooking: (bookingId: string) => Promise<void>;
  
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  getAuthHeaders: () => Record<string, string>;
}

const API_BASE_URL = 'http://localhost:3000/api'

export const useMeetingRoomStore = create<MeetingRoomState>()((set, get) => ({
  meetingRooms: [],
  currentRoom: null,
  currentBookings: [],
  isLoading: false,
  error: null,

  // Helper function to get auth token
  getAuthHeaders: () => {
    const { tokens } = useAuthStore.getState()
    const accessToken = tokens?.accessToken
    
    if (!accessToken) {
      throw new Error('未登录或令牌已过期')
    }
    
    return {
      'Authorization': `Bearer ${accessToken}`,
    }
  },

  fetchMeetingRooms: async (filters = {}) => {
    set({ isLoading: true, error: null })
    
    try {
      const queryParams = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          const v = String(value)
          if (v !== '') {
            queryParams.append(key, v)
          }
        }
      })

      const response = await fetch(`${API_BASE_URL}/meeting-rooms?${queryParams}`, {
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('获取会议室列表失败')
      }

      const data = await response.json()
      set({ meetingRooms: data.data.meetingRooms, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取会议室列表失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  fetchMeetingRoomById: async (id: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${id}`, {
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('获取会议室详情失败')
      }

      const data = await response.json()
      set({ currentRoom: data.data.meetingRoom, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取会议室详情失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  createMeetingRoom: async (data: CreateMeetingRoomData) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...get().getAuthHeaders(),
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '创建会议室失败')
      }

      const result = await response.json()
      
      // 更新会议室列表
      const { meetingRooms } = get()
      set({ 
        meetingRooms: [...meetingRooms, result.data.meetingRoom], 
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '创建会议室失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  updateMeetingRoom: async (id: string, data: Partial<CreateMeetingRoomData>) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...get().getAuthHeaders(),
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '更新会议室失败')
      }

      const result = await response.json()
      
      // 更新会议室列表
      const { meetingRooms } = get()
      const updatedRooms = meetingRooms.map(room => 
        room.id === id ? result.data.meetingRoom : room
      )
      set({ 
        meetingRooms: updatedRooms, 
        currentRoom: get().currentRoom?.id === id ? result.data.meetingRoom : get().currentRoom,
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '更新会议室失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  deleteMeetingRoom: async (id: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${id}`, {
        method: 'DELETE',
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '删除会议室失败')
      }

      // 从列表中移除
      const { meetingRooms } = get()
      set({ 
        meetingRooms: meetingRooms.filter(room => room.id !== id),
        currentRoom: get().currentRoom?.id === id ? null : get().currentRoom,
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '删除会议室失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  updateMeetingRoomStatus: async (id: string, status: MeetingRoom['status']) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...get().getAuthHeaders(),
        },
        body: JSON.stringify({ status }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '更新会议室状态失败')
      }

      // 更新会议室列表中的状态
      const { meetingRooms } = get()
      const updatedRooms = meetingRooms.map(room => 
        room.id === id ? { ...room, status } : room
      )
      set({ 
        meetingRooms: updatedRooms, 
        currentRoom: get().currentRoom?.id === id ? { ...get().currentRoom!, status } : get().currentRoom,
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '更新会议室状态失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  searchMeetingRooms: async (query: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/search/${encodeURIComponent(query)}`, {
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('搜索会议室失败')
      }

      const data = await response.json()
      set({ meetingRooms: data.data.meetingRooms, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '搜索会议室失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  // Booking actions
  fetchBookings: async (roomId: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${roomId}/bookings`, {
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('获取预约列表失败')
      }

      const data = await response.json()
      set({ currentBookings: data.data.bookings, isLoading: false })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取预约列表失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  createBooking: async (data: CreateBookingData) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${data.roomId}/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...get().getAuthHeaders(),
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '创建预约失败')
      }

      const result = await response.json()
      
      // 更新当前预约列表
      const { currentBookings } = get()
      set({ 
        currentBookings: [...currentBookings, result.data.booking], 
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '创建预约失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  cancelBooking: async (bookingId: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const { currentRoom } = get()
      if (!currentRoom) {
        throw new Error('未选择会议室')
      }

      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${currentRoom.id}/bookings/${bookingId}`, {
        method: 'DELETE',
        headers: get().getAuthHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || '取消预约失败')
      }

      // 从当前预约列表中移除
      const { currentBookings } = get()
      set({ 
        currentBookings: currentBookings.filter(booking => booking.id !== bookingId), 
        isLoading: false 
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '取消预约失败'
      set({ error: errorMessage, isLoading: false })
      throw error
    }
  },

  clearError: () => set({ error: null }),
  
  setLoading: (loading: boolean) => set({ isLoading: loading }),
}))