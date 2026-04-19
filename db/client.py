from datetime import datetime, timezone

from supabase import acreate_client, AsyncClient

from db.models import Idea, IdeaCreate


def _short_id_range(short_id: str) -> tuple[str, str]:
    """Return (lo, hi) UUID bounds matching any UUID starting with short_id."""
    return (
        f"{short_id}-0000-0000-0000-000000000000",
        f"{short_id}-ffff-ffff-ffff-ffffffffffff",
    )


class SupabaseClient:
    def __init__(self, supabase: AsyncClient):
        self._db = supabase

    @classmethod
    async def create(cls, url: str, key: str) -> "SupabaseClient":
        client = await acreate_client(url, key)
        return cls(supabase=client)

    async def save_idea(self, idea: IdeaCreate) -> Idea:
        row = idea.model_dump()
        res = await self._db.table("ideas").insert(row).execute()
        return Idea(**res.data[0])

    async def save_raw(self, content: str, source_type: str) -> Idea:
        idea = IdeaCreate(
            title=content[:60] + ("…" if len(content) > 60 else ""),
            summary="(Non elaborato — arricchimento fallito)",
            original_content=content,
            source_type=source_type,
            category="other",
            tags=[],
        )
        return await self.save_idea(idea)

    async def list_ideas(self, limit: int = 10) -> list[Idea]:
        res = (
            await self._db.table("ideas")
            .select("*")
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [Idea(**row) for row in res.data]

    async def toggle_publish(self, short_id: str) -> Idea:
        lo, hi = _short_id_range(short_id)
        res = (
            await self._db.table("ideas")
            .select("id, published")
            .gte("id", lo)
            .lte("id", hi)
            .execute()
        )
        full_id = res.data[0]["id"]
        new_published = not res.data[0]["published"]
        update_data: dict = {"published": new_published}
        if new_published:
            update_data["published_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update_data["published_at"] = None

        await self._db.table("ideas").update(update_data).eq("id", full_id).execute()

        res2 = await self._db.table("ideas").select("*").eq("id", full_id).execute()
        return Idea(**res2.data[0])

    async def soft_delete(self, short_id: str) -> None:
        lo, hi = _short_id_range(short_id)
        await (
            self._db.table("ideas")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .gte("id", lo)
            .lte("id", hi)
            .execute()
        )

    async def clear_all(self) -> int:
        """Hard-delete all ideas. Returns count of deleted rows."""
        res = await self._db.table("ideas").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return len(res.data)

    async def find_by_source_url(self, url: str) -> Idea | None:
        res = (
            await self._db.table("ideas")
            .select("*")
            .eq("source_url", url)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )
        return Idea(**res.data[0]) if res.data else None

    async def update_embedding(self, idea_id: str, embedding: list[float]) -> None:
        """Store the embedding vector for an idea."""
        await (
            self._db.table("ideas")
            .update({"embedding": embedding})
            .eq("id", idea_id)
            .execute()
        )

    async def resolve_short_id(self, short_id: str) -> str:
        lo, hi = _short_id_range(short_id)
        res = (
            await self._db.table("ideas")
            .select("id")
            .gte("id", lo)
            .lte("id", hi)
            .execute()
        )
        return res.data[0]["id"]
