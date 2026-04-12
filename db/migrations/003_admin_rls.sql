-- Migration 003: RLS policy for authenticated admin users (Phase 3)
-- Grants full access to authenticated users (magic-link login via Supabase Auth)

CREATE POLICY "Authenticated users full access"
    ON ideas FOR ALL
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');
