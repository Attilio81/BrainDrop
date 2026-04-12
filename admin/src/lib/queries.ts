import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { supabase } from '@/lib/supabase'
import type { Filters, Idea, IdeaPatch, Tab } from '@/types'

// ── READ ──────────────────────────────────────────────────────────────────

export function useIdeas(tab: Tab, filters: Filters) {
  return useQuery({
    queryKey: ['ideas', tab, filters],
    queryFn: async () => {
      let q = supabase.from('ideas').select('*').order('created_at', { ascending: false })

      if (tab === 'inbox')     q = q.eq('published', false).is('deleted_at', null)
      if (tab === 'published') q = q.eq('published', true).is('deleted_at', null)
      if (tab === 'trash')     q = q.not('deleted_at', 'is', null)

      if (filters.text)        q = q.or(`title.ilike.%${filters.text}%,summary.ilike.%${filters.text}%`)
      if (filters.category)    q = q.eq('category', filters.category)
      if (filters.tags.length) q = q.contains('tags', filters.tags)

      const { data, error } = await q
      if (error) throw error
      return data as Idea[]
    },
  })
}

export function useInboxCount() {
  return useQuery({
    queryKey: ['ideas', 'inbox-count'],
    queryFn: async () => {
      const { count, error } = await supabase
        .from('ideas')
        .select('*', { count: 'exact', head: true })
        .eq('published', false)
        .is('deleted_at', null)
      if (error) throw error
      return count ?? 0
    },
  })
}

// ── MUTATIONS ──────────────────────────────────────────────────────────────

export function useTogglePublish() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (idea: Idea) => {
      const now = new Date().toISOString()
      const { error } = await supabase
        .from('ideas')
        .update({
          published: !idea.published,
          published_at: idea.published ? null : now,
        })
        .eq('id', idea.id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante la pubblicazione'),
  })
}

export function useUpdateIdea() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, patch }: { id: string; patch: IdeaPatch }) => {
      const { error } = await supabase
        .from('ideas')
        .update({ ...patch, updated_at: new Date().toISOString() })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ideas'] })
      toast.success('Modifiche salvate')
    },
    onError: () => toast.error('Errore durante il salvataggio'),
  })
}

export function useSoftDelete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from('ideas')
        .update({ deleted_at: new Date().toISOString() })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante lo spostamento nel cestino'),
  })
}

export function useRestore() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase
        .from('ideas')
        .update({ deleted_at: null })
        .eq('id', id)
      if (error) throw error
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ideas'] }),
    onError: () => toast.error('Errore durante il ripristino'),
  })
}

export function useHardDelete() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from('ideas').delete().eq('id', id)
      if (error) throw error
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ideas'] })
      toast.success('Eliminata definitivamente')
    },
    onError: () => toast.error("Errore durante l'eliminazione"),
  })
}
