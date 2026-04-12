from datetime import datetime, timezone

from supabase import acreate_client, AsyncClient

from db.models import Idea, IdeaCreate


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
        # Fetch current state
        res = (
            await self._db.table("ideas")
            .select("id, published")
            .like("id", f"{short_id}%")
            .execute()
        )
        row = res.data[0]
        new_published = not row["published"]
        update_data: dict = {"published": new_published}
        if new_published:
            update_data["published_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update_data["published_at"] = None

        res2 = (
            await self._db.table("ideas")
            .update(update_data)
            .like("id", f"{short_id}%")
            .execute()
        )
        return Idea(**res2.data[0])

    async def soft_delete(self, short_id: str) -> None:
        await (
            self._db.table("ideas")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .like("id", f"{short_id}%")
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

    async def resolve_short_id(self, short_id: str) -> str:
        res = (
            await self._db.table("ideas")
            .select("id")
            .like("id", f"{short_id}%")
            .execute()
        )
        return res.data[0]["id"]
