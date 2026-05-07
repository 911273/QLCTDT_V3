from .base_repository import BaseRepository


class StatisticsRepository(BaseRepository):
    def get_dashboard_stats(self) -> dict:
        total_hp = self.conn.execute("SELECT COUNT(*) FROM hoc_phan").fetchone()[0] or 0
        total_khoa = self.conn.execute("SELECT COUNT(*) FROM khoa").fetchone()[0] or 0
        total_gv = self.conn.execute("SELECT COUNT(*) FROM giang_vien").fetchone()[0] or 0
        total_ctdt = self.conn.execute("SELECT COUNT(*) FROM chuong_trinh_dao_tao").fetchone()[0] or 0
        total_clo = self.conn.execute("SELECT COUNT(*) FROM clo").fetchone()[0] or 0
        total_assessments = self.conn.execute("SELECT COUNT(*) FROM ke_hoach_kiem_tra").fetchone()[0] or 0

        return {
            "total_hp": total_hp,
            "total_khoa": total_khoa,
            "total_gv": total_gv,
            "total_ctdt": total_ctdt,
            "total_clo": total_clo,
            "total_assessments": total_assessments,
        }

    def get_hp_ids_by_nature(self, nature: str) -> list[int]:
        rows = self.conn.execute(
            "SELECT id FROM hoc_phan WHERE tinh_chat=? ORDER BY ten_viet",
            (nature,),
        ).fetchall()
        return [r["id"] for r in rows]

