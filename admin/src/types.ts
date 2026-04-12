export type SourceType =
  | 'url'
  | 'text'
  | 'instagram'
  | 'photo'
  | 'voice'
  | 'youtube'

export type Category =
  | 'tech'
  | 'programming'
  | 'ai'
  | 'crossfit'
  | 'travel'
  | 'food'
  | 'business'
  | 'personal'
  | 'other'

export const CATEGORIES: Category[] = [
  'tech', 'programming', 'ai', 'crossfit',
  'travel', 'food', 'business', 'personal', 'other',
]

export interface Idea {
  id: string
  created_at: string
  updated_at: string
  title: string
  summary: string
  details: string
  original_content: string
  enrichment_data: Record<string, unknown>
  source_type: SourceType
  category: Category
  tags: string[]
  media_url: string | null
  source_url: string | null
  thumbnail_url: string | null
  published: boolean
  published_at: string | null
  deleted_at: string | null
  notes: string | null
  sort_order: number
}

export type IdeaPatch = Partial<Pick<Idea, 'title' | 'summary' | 'category' | 'tags' | 'notes'>>

export type Tab = 'inbox' | 'published' | 'trash'

export interface Filters {
  text: string
  category: Category | ''
  tags: string[]
  semantic: boolean
}

export const DEFAULT_FILTERS: Filters = { text: '', category: '', tags: [], semantic: false }

export const SOURCE_TYPE_EMOJI: Record<SourceType, string> = {
  url: '🔗',
  text: '📝',
  instagram: '📸',
  photo: '🖼',
  voice: '🎙',
  youtube: '🎥',
}

export const CATEGORY_COLORS: Record<Category, { bg: string; text: string; border: string }> = {
  ai:          { bg: '#ede9ff', text: '#5b47d4', border: '#c4b9f5' },
  tech:        { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' },
  programming: { bg: '#e0e7ff', text: '#4338ca', border: '#a5b4fc' },
  crossfit:    { bg: '#dcfce7', text: '#15803d', border: '#86efac' },
  travel:      { bg: '#fef9c3', text: '#a16207', border: '#fde047' },
  food:        { bg: '#ffedd5', text: '#c2410c', border: '#fdba74' },
  business:    { bg: '#d1fae5', text: '#065f46', border: '#6ee7b7' },
  personal:    { bg: '#fce7f3', text: '#9d174d', border: '#f9a8d4' },
  other:       { bg: '#f3f4f6', text: '#374151', border: '#d1d5db' },
}
