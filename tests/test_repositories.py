# tests/test_repositories.py
"""
Unit tests cho Repositories (HocPhan, CLO, NoiDung, etc.)
Dùng in-memory SQLite để test độc lập.
"""
import unittest
import sqlite3
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Schema DDL (Matching Production Tables) ──────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS khoa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma TEXT UNIQUE,
    ten TEXT
);

CREATE TABLE IF NOT EXISTS giang_vien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT NOT NULL,
    email TEXT,
    sdt TEXT,
    khoa_id INTEGER REFERENCES khoa(id)
);

CREATE TABLE IF NOT EXISTS hoc_phan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma TEXT,
    ten_viet TEXT,
    ten_anh TEXT,
    khoa_id INTEGER REFERENCES khoa(id),
    ngay_tao TEXT,
    ngay_cap_nhat TEXT,
    tong_gio REAL DEFAULT 0,
    trang_thai TEXT DEFAULT 'nhap',
    gio_lt REAL DEFAULT 0,
    gio_bt REAL DEFAULT 0,
    gio_th REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    ma TEXT,
    mo_ta TEXT,
    cdr_ma TEXT,
    level_irm TEXT,
    nhom TEXT,
    la_tieu_de_nhom INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS muc_tieu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    ma_mt TEXT,
    mo_ta TEXT,
    cdr_ma TEXT,
    thu_tu INTEGER
);

CREATE TABLE IF NOT EXISTS noi_dung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    phan TEXT, -- 'LT' / 'TH'
    tieu_de TEXT,
    cap_do INTEGER DEFAULT 1,
    parent_id INTEGER,
    gio_lt REAL DEFAULT 0,
    gio_bt REAL DEFAULT 0,
    gio_th REAL DEFAULT 0,
    clo_ids TEXT
);

CREATE TABLE IF NOT EXISTS hoc_lieu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    loai TEXT,
    ten_tl TEXT,
    thu_tu INTEGER
);

CREATE TABLE IF NOT EXISTS ke_hoach_kiem_tra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    ma_bdg TEXT,
    thu_tu INTEGER
);

CREATE TABLE IF NOT EXISTS ctdt_hoc_phan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER REFERENCES hoc_phan(id) ON DELETE CASCADE,
    ctdt_id INTEGER
);

CREATE TABLE IF NOT EXISTS temp_draft (
    hp_id INTEGER PRIMARY KEY REFERENCES hoc_phan(id) ON DELETE CASCADE,
    data_json TEXT,
    updated_at TEXT,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER,
    table_name TEXT,
    record_id INTEGER,
    action TEXT,
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    total_files INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    details_json TEXT,
    user_action TEXT
);

CREATE TABLE IF NOT EXISTS ui_field_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_key TEXT,
    field_key TEXT,
    nhan_tuy_bien TEXT,
    thu_tu INTEGER,
    an_truong INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chuong_trinh_dao_tao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT,
    bac TEXT,
    khoa_id INTEGER
);
"""

class FakeDB:
    def __init__(self, conn):
        self.conn = conn
    
    def transaction(self):
        class Transaction:
            def __enter__(self): return None
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return Transaction()

def _make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    # Mock unaccent function
    conn.create_function("unaccent", 1, lambda s: s if s else "")
    return conn

# ═════════════════════════════════════════════════════════════════════════════
# Tests for HocPhanRepository
# ═════════════════════════════════════════════════════════════════════════════
class TestHocPhanRepository(unittest.TestCase):
    def setUp(self):
        self.conn = _make_conn()
        from repositories.hoc_phan_repository import HocPhanRepository
        self.repo = HocPhanRepository(FakeDB(self.conn))

    def tearDown(self):
        self.conn.close()
    
    def test_create_and_get(self):
        hp_id = self.repo.create({'ma': 'CS101', 'ten_viet': 'Lập trình C'})
        hp = self.repo.get_by_id(hp_id)
        self.assertIsNotNone(hp)
        self.assertEqual(hp['ma'], 'CS101')
    
    def test_update_hours(self):
        hp_id = self.repo.create({'ten_viet': 'Test'})
        self.repo.update(hp_id, {'gio_lt': 30, 'gio_bt': 15})
        hp = self.repo.get_by_id(hp_id)
        self.assertEqual(hp['tong_gio'], 45)

    def test_clone(self):
        hp_id = self.repo.create({'ma': 'ORIG', 'ten_viet': 'Original'})
        self.conn.execute("INSERT INTO clo (hp_id, ma) VALUES (?, ?)", (hp_id, 'CLO1'))
        
        new_id = self.repo.clone(hp_id)
        new_hp = self.repo.get_by_id(new_id)
        self.assertIn("(Bản sao)", new_hp['ten_viet'])
        
        clos = self.conn.execute("SELECT * FROM clo WHERE hp_id=?", (new_id,)).fetchall()
        self.assertEqual(len(clos), 1)

# ═════════════════════════════════════════════════════════════════════════════
# Tests for CLORepository
# ═════════════════════════════════════════════════════════════════════════════
class TestCLORepository(unittest.TestCase):
    def setUp(self):
        self.conn = _make_conn()
        from repositories.clo_repository import CLORepository
        self.repo = CLORepository(FakeDB(self.conn))
        # Create parent HP to satisfy FK
        self.hp_id = self.conn.execute("INSERT INTO hoc_phan (ten_viet) VALUES ('Parent')").lastrowid

    def tearDown(self):
        self.conn.close()
    
    def test_set_all(self):
        self.repo.set_all(self.hp_id, [{'ma': 'CLO1'}, {'ma': 'CLO2'}])
        rows = self.repo.get_by_hp(self.hp_id)
        self.assertEqual(len(rows), 2)

# ═════════════════════════════════════════════════════════════════════════════
# Tests for NoiDungRepository
# ═════════════════════════════════════════════════════════════════════════════
class TestNoiDungRepository(unittest.TestCase):
    def setUp(self):
        self.conn = _make_conn()
        from repositories.noidung_repository import NoiDungRepository
        self.repo = NoiDungRepository(FakeDB(self.conn))
        # Create parent HP
        self.hp_id = self.conn.execute("INSERT INTO hoc_phan (ten_viet) VALUES ('Parent')").lastrowid

    def tearDown(self):
        self.conn.close()
    
    def test_set_all_and_get(self):
        self.repo.set_all(self.hp_id, 'LT', [{'tieu_de': 'C1'}, {'tieu_de': 'C2'}])
        rows = self.repo.get_by_hp(self.hp_id, 'LT')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['tieu_de'], 'C1')

    def test_recursive_delete(self):
        p_id = self.conn.execute("INSERT INTO noi_dung (hp_id, tieu_de) VALUES (?, 'Parent')", (self.hp_id,)).lastrowid
        self.conn.execute("INSERT INTO noi_dung (hp_id, tieu_de, parent_id) VALUES (?, 'Child', ?)", (self.hp_id, p_id))
        
        self.repo.delete_recursive(p_id)
        count = self.conn.execute("SELECT COUNT(*) FROM noi_dung").fetchone()[0]
        self.assertEqual(count, 0)


class TestInfrastructureRepositories(unittest.TestCase):
    def setUp(self):
        self.conn = _make_conn()
        self.db = FakeDB(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_config_repository_get_set(self):
        from repositories.config_repository import ConfigRepository
        repo = ConfigRepository(self.db)

        self.assertEqual(repo.get("missing", "fallback"), "fallback")
        repo.set("theme", "flatly")

        self.assertEqual(repo.get("theme"), "flatly")
        self.assertEqual(repo.get_many(["theme"]), {"theme": "flatly"})

    def test_audit_repository_log_and_history(self):
        from repositories.audit_repository import AuditRepository
        repo = AuditRepository(self.db)

        audit_id = repo.log(1, "hoc_phan", details={"field": "ten_viet"})
        rows = repo.get_history(hp_id=1)

        self.assertIsInstance(audit_id, int)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["table_name"], "hoc_phan")

    def test_draft_repository_save_get_delete(self):
        from repositories.draft_repository import DraftRepository
        repo = DraftRepository(self.db)
        hp_id = self.conn.execute("INSERT INTO hoc_phan (ten_viet) VALUES ('Parent')").lastrowid

        repo.save(hp_id, '{"sec1": {}}')
        draft = repo.get(hp_id)
        self.assertEqual(draft["data_json"], '{"sec1": {}}')

        repo.delete(hp_id)
        self.assertIsNone(repo.get(hp_id))

    def test_import_history_repository_add_and_list(self):
        from repositories.import_history_repository import ImportHistoryRepository
        repo = ImportHistoryRepository(self.db)

        log_id = repo.add("IMPORT", 3, 2, 1, "[]", "manual")
        rows = repo.get_history()

        self.assertIsInstance(log_id, int)
        self.assertEqual(rows[0]["type"], "IMPORT")
        self.assertEqual(rows[0]["success_count"], 2)

    def test_ui_metadata_repository(self):
        from repositories.ui_metadata_repository import UIMetadataRepository
        self.conn.execute(
            """
            INSERT INTO ui_field_meta(section_key, field_key, nhan_tuy_bien, thu_tu, an_truong)
            VALUES ('sec1', 'ma', 'Mã HP', 1, 0)
            """
        )
        repo = UIMetadataRepository(self.db)

        meta = repo.get_field_meta("sec1")
        self.assertEqual(meta["ma"]["nhan_tuy_bien"], "Mã HP")
        self.assertFalse(meta["ma"]["an_truong"])

    def test_statistics_repository_dashboard(self):
        from repositories.statistics_repository import StatisticsRepository
        self.conn.execute("INSERT INTO khoa (ten) VALUES ('CNTT')")
        self.conn.execute("INSERT INTO giang_vien (ho_ten) VALUES ('GV A')")
        self.conn.execute("INSERT INTO chuong_trinh_dao_tao (ten) VALUES ('CTDT A')")
        self.conn.execute("INSERT INTO hoc_phan (ten_viet) VALUES ('HP A')")

        stats = StatisticsRepository(self.db).get_dashboard_stats()
        self.assertEqual(stats["total_hp"], 1)
        self.assertEqual(stats["total_khoa"], 1)
        self.assertEqual(stats["total_gv"], 1)
        self.assertEqual(stats["total_ctdt"], 1)


class TestCourseCRUDService(unittest.TestCase):
    def setUp(self):
        self.conn = _make_conn()
        from repositories.hoc_phan_repository import HocPhanRepository
        from services.course_crud_service import CourseCRUDService
        self.repo = HocPhanRepository(FakeDB(self.conn))
        self.service = CourseCRUDService(self.repo)

    def tearDown(self):
        self.conn.close()

    def test_course_crud_flow(self):
        hp_id = self.service.create_course({"ma": "CRUD101", "ten_viet": "CRUD"})
        self.assertEqual(self.service.get_course(hp_id)["ma"], "CRUD101")

        self.service.update_course(hp_id, {"ten_viet": "CRUD Updated"})
        self.assertEqual(self.service.get_course(hp_id)["ten_viet"], "CRUD Updated")

        courses = self.service.list_courses()
        self.assertEqual(len(courses), 1)

        self.service.delete_course(hp_id)
        self.assertIsNone(self.service.get_course(hp_id))

if __name__ == '__main__':
    unittest.main()
