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
}

export const DEFAULT_FILTERS: Filters = { text: '', category: '', tags: [] }

export const SOURCE_TYPE_EMOJI: Record<SourceType, string> = {
  url: '🔗',
  text: '📝',
  instagram: '📸',
  photo: '🖼',
  voice: '🎙',
  youtube: '🎥',
}

export const CATEGORY_COLORS: Record<Category, { bg: string; text: string; border: string }> = {
  ai:          { bg: '#1a1a30', text: '#a89fff', border: '#2a2a50' },
  tech:        { bg: '#1a2030', text: '#60a5fa', border: '#2a3050' },
  programming: { bg: '#1a1a2a', text: '#818cf8', border: '#2a2a40' },
  crossfit:    { bg: '#1a2a1a', text: '#4ade80', border: '#2a4a2a' },
  travel:      { bg: '#2a2010', text: '#fbbf24', border: '#4a3a10' },
  food:        { bg: '#2a1a10', text: '#fb923c', border: '#4a2a10' },
  business:    { bg: '#1a2020', text: '#34d399', border: '#2a3a30' },
  personal:    { bg: '#2a1a20', text: '#f472b6', border: '#4a2a30' },
  other:       { bg: '#1a1a1a', text: '#9ca3af', border: '#2a2a2a' },
}
