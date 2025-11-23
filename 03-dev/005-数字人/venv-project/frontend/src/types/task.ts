export interface Task {
  id: string
  name: string
  description?: string
  status: string
  task_type: string
  input_text?: string
  reference_video_path?: string
  reference_audio_path?: string
  output_video_path?: string
  output_audio_path?: string
  lse_c_score?: string
  lse_d_score?: string
  mos_score?: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  processing_time?: number
  error_message?: string
  retry_count: number
  user_id?: string
  is_public: boolean
}

export interface TaskCreate {
  name: string
  description?: string
  task_type: string
  input_text?: string
  reference_video_path?: string
  reference_audio_path?: string
  is_public?: boolean
}

export interface TaskResponse extends Task {}

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
export type TaskType = 'text_to_speech' | 'lip_sync' | 'full_pipeline'