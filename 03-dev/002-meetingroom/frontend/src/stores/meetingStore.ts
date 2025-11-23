import { create } from 'zustand'

export interface MeetingRoom {
  id: string
  name: string
  description?: string
  capacity: number
  floor?: number
  building?: string
  equipment: string[]
  status: 'available' | 'occupied' | 'maintenance' | 'disabled'
  hourlyRate: number
  images?: string[]
  createdAt: string
  updatedAt: string
}

export interface Meeting {
  id: string
  title: string
  description?: string
  meetingRoomId: string
  meetingRoom?: MeetingRoom
  organizerId: string
  organizer?: User
  startTime: string
  endTime: string
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled' | 'no_show'
  type: 'regular' | 'recurring' | 'emergency' | 'online'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  attendeeCount: number
  maxAttendees?: number
  notes?: string
  attachments?: string[]
  aiSummary?: string
  createdAt: string
  updatedAt: string
}

export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'manager' | 'user'
  department?: string
  phone?: string
  avatar?: string
  status: 'active' | 'inactive' | 'suspended'
  createdAt: string
  updatedAt: string
}

interface MeetingState {
  // State
  rooms: MeetingRoom[]
  meetings: Meeting[]
  currentRoom: MeetingRoom | null
  currentMeeting: Meeting | null
  isLoading: boolean
  error: string | null
  
  // Actions
  setRooms: (rooms: MeetingRoom[]) => void
  setMeetings: (meetings: Meeting[]) => void
  setCurrentRoom: (room: MeetingRoom | null) => void
  setCurrentMeeting: (meeting: Meeting | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  
  // API Actions
  fetchRooms: () => Promise<void>
  fetchMeetings: (params?: Record<string, unknown>) => Promise<void>
  fetchRoomById: (id: string) => Promise<void>
  fetchMeetingById: (id: string) => Promise<void>
  bookMeeting: (meetingData: Partial<Meeting>) => Promise<void>
  updateMeeting: (id: string, meetingData: Partial<Meeting>) => Promise<void>
  cancelMeeting: (id: string) => Promise<void>
}

const API_BASE_URL = 'http://localhost:3000/api'

export const useMeetingStore = create<MeetingState>((set, get) => ({
  // Initial state
  rooms: [],
  meetings: [],
  currentRoom: null,
  currentMeeting: null,
  isLoading: false,
  error: null,
  
  // Basic actions
  setRooms: (rooms) => set({ rooms }),
  setMeetings: (meetings) => set({ meetings }),
  setCurrentRoom: (currentRoom) => set({ currentRoom }),
  setCurrentMeeting: (currentMeeting) => set({ currentMeeting }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
  
  // API actions
  fetchRooms: async () => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '获取会议室列表失败')
      }
      
      set({ rooms: data.data.rooms, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取会议室列表失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  fetchMeetings: async (params = {}) => {
    set({ isLoading: true, error: null })
    
    try {
      const stringParams = Object.fromEntries(
        Object.entries(params).map(([key, value]) => [key, String(value ?? '')])
      )
      const queryString = new URLSearchParams(stringParams).toString()
      const response = await fetch(`${API_BASE_URL}/meetings?${queryString}`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '获取会议列表失败')
      }
      
      set({ meetings: data.data.meetings, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取会议列表失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  fetchRoomById: async (id: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meeting-rooms/${id}`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '获取会议室详情失败')
      }
      
      set({ currentRoom: data.data.room, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取会议室详情失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  fetchMeetingById: async (id: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${id}`)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '获取会议详情失败')
      }
      
      set({ currentMeeting: data.data.meeting, isLoading: false })
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '获取会议详情失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  bookMeeting: async (meetingData: Partial<Meeting>) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meetings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify(meetingData),
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '预订会议失败')
      }
      
      // 重新获取会议列表
      await get().fetchMeetings()
      set({ isLoading: false })
      
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '预订会议失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  updateMeeting: async (id: string, meetingData: Partial<Meeting>) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify(meetingData),
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '更新会议失败')
      }
      
      // 重新获取会议列表
      await get().fetchMeetings()
      set({ isLoading: false })
      
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '更新会议失败',
        isLoading: false 
      })
      throw error
    }
  },
  
  cancelMeeting: async (id: string) => {
    set({ isLoading: true, error: null })
    
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.message || '取消会议失败')
      }
      
      // 重新获取会议列表
      await get().fetchMeetings()
      set({ isLoading: false })
      
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '取消会议失败',
        isLoading: false 
      })
      throw error
    }
  },
}))

// Helper function to get auth token
function getAuthToken(): string {
  // This is a simplified version - in a real app, you'd get this from your auth store
  const authStore = localStorage.getItem('auth-storage')
  if (authStore) {
    try {
      const parsed = JSON.parse(authStore)
      return parsed.state?.tokens?.accessToken || ''
    } catch {
      return ''
    }
  }
  return ''
}