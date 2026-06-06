export type SourceType = 'video' | 'audio' | 'pdf' | 'image' | 'text' | 'url' | 'youtube'
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Document {
  id: string
  title: string
  source_type: SourceType
  source_url?: string
  status: DocumentStatus
  created_at: string
}

export interface ProcessingJob {
  id: string
  document_id: string
  status: JobStatus
  progress: number // 0-100
  current_stage: string
  error_message?: string
  started_at?: string
  completed_at?: string
}

export interface AudioSegment {
  id: string
  chunk_index: number
  start_time: number
  end_time: number
  transcript: string
}

export interface VisualFrame {
  id: string
  timestamp: number
  image_url: string
  slide_number: number
  slide_title?: string
  ocr_text: string
}

export interface NoteSection {
  slide_number: number
  slide_title: string
  timestamp_start: number
  timestamp_end: number
  image_url?: string
  content: string[]
  audio_segments: AudioSegment[]
}

export interface Notes {
  id: string
  document_id: string
  document_title: string
  sections: NoteSection[]
  generated_at: string
}
