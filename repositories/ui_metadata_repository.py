from .base_repository import BaseRepository


class UIMetadataRepository(BaseRepository):
    def get_field_meta(self, section_key: str) -> dict:
        rows = self.conn.execute(
            """
            SELECT field_key, nhan_tuy_bien, thu_tu, an_truong
            FROM ui_field_meta
            WHERE section_key=?
            """,
            (section_key,),
        ).fetchall()
        return {
            r["field_key"]: {
                "nhan_tuy_bien": r["nhan_tuy_bien"],
                "thu_tu": r["thu_tu"],
                "an_truong": bool(r["an_truong"]),
            }
            for r in rows
        }

