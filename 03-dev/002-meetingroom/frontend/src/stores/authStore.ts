import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresIn: number
}

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  resetPassword: (email: string, newPassword: string, token: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  getCurrentUser: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}

export interface RegisterData {
  username: string
  email: string
  password: string
  role?: 'admin' | 'manager' | 'user'
  department?: string
  phone?: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api'

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
          })

          const data = await response.json()

          if (!response.ok) {
            throw new Error(data.message || '登录失败')
          }

          const { tokens } = data.data
          
          set({ 
            tokens,
            isAuthenticated: true,
            isLoading: false 
          })

          // 获取用户信息
          await get().getCurrentUser()
          
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '登录失败',
            isLoading: false 
          })
          throw error
        }
      },

      register: async (userData: RegisterData) => {
        set({ isLoading: true, error: null })
        
        try {
          console.log('Register API URL:', `${API_BASE_URL}/auth/register`)
          console.log('Register request data:', userData)
          
          const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
          })

          console.log('Register response status:', response.status)
          console.log('Register response headers:', response.headers)
          
          const data = await response.json()
          console.log('Register response data:', data)

          if (!response.ok) {
            throw new Error(data.message || '注册失败')
          }

          set({ isLoading: false })
          
        } catch (error) {
          console.error('Register error:', error)
          set({ 
            error: error instanceof Error ? error.message : '注册失败',
            isLoading: false 
          })
          throw error
        }
      },

      resetPassword: async (email: string, newPassword: string, token: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, newPassword, token }),
          })
          const data = await response.json()
          if (!response.ok) {
            throw new Error(data.message || '重置失败')
          }
          set({ isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '重置失败',
            isLoading: false
          })
          throw error
        }
      },

      logout: async () => {
        const { tokens } = get()
        
        if (tokens?.refreshToken) {
          try {
            await fetch(`${API_BASE_URL}/auth/logout`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refreshToken: tokens.refreshToken }),
            })
          } catch (error) {
            console.error('Logout API call failed:', error)
          }
        }

        set({ 
          user: null,
          tokens: null,
          isAuthenticated: false,
          error: null 
        })
      },

      refreshToken: async () => {
        const { tokens } = get()
        
        if (!tokens?.refreshToken) {
          throw new Error('没有刷新令牌')
        }

        try {
          const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refreshToken: tokens.refreshToken }),
          })

          const data = await response.json()

          if (!response.ok) {
            throw new Error(data.message || '刷新令牌失败')
          }

          const { tokens: newTokens } = data.data
          
          set({ tokens: newTokens })
          
        } catch (error) {
          // 刷新令牌失败，需要重新登录
          set({ 
            user: null,
            tokens: null,
            isAuthenticated: false 
          })
          throw error
        }
      },

      getCurrentUser: async () => {
        const { tokens } = get()
        
        if (!tokens?.accessToken) {
          return
        }

        try {
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${tokens.accessToken}`,
            },
          })

          const data = await response.json()

          if (!response.ok) {
            if (response.status === 401) {
              // 尝试刷新令牌
              try {
                await get().refreshToken()
                // 重新获取用户信息
                const retryResponse = await fetch(`${API_BASE_URL}/auth/me`, {
                  headers: {
                    'Authorization': `Bearer ${get().tokens?.accessToken}`,
                  },
                })
                
                if (retryResponse.ok) {
                  const retryData = await retryResponse.json()
                  set({ user: retryData.data.user })
                  return
                }
              } catch {
                // 刷新失败，需要重新登录
                set({ 
                  user: null,
                  tokens: null,
                  isAuthenticated: false 
                })
                return
              }
            }
            throw new Error(data.message || '获取用户信息失败')
          }

          set({ user: data.data.user })
          
        } catch (error) {
          console.error('获取用户信息失败:', error)
          set({ 
            user: null,
            tokens: null,
            isAuthenticated: false 
          })
        }
      },

      clearError: () => set({ error: null }),
      
      setLoading: (loading: boolean) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)