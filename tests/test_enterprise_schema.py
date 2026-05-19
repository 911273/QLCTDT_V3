import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enterprise_schema import ACADEMIC_SYSTEM_SCHEMA, apply_enterprise_schema_upgrade
from repositories.enterprise_repository import EnterpriseRepository
from services.enterprise_schema_service import EnterpriseSchemaService


LEGACY_SCHEMA_SQL = """
CREATE TABLE schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    updated_at TEXT NOT NULL
);

CREATE TABLE khoa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma TEXT,
    ten TEXT NOT NULL
);

CREATE TABLE giang_vien (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT NOT NULL,
    hoc_vi TEXT,
    sdt TEXT,
    email TEXT,
    khoa_id INTEGER,
    ma_can_bo TEXT
);

CREATE TABLE chuong_trinh_dao_tao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ten TEXT NOT NULL,
    bac TEXT,
    khoa_id INTEGER
);

CREATE TABLE chuyen_nganh (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ctdt_id INTEGER,
    ten TEXT NOT NULL
);

CREATE TABLE hoc_phan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma TEXT,
    ten_viet TEXT NOT NULL,
    ten_anh TEXT,
    trinh_do TEXT,
    khoa_id INTEGER,
    so_tin_chi INTEGER,
    loai TEXT,
    tinh_chat TEXT,
    gio_lt REAL,
    gio_th REAL,
    gio_tl REAL,
    gio_tieu_luan REAL,
    gio_thuc_tap REAL,
    gio_tu_hoc REAL,
    tong_gio REAL,
    hp_tien_quyet TEXT,
    hp_thay_the TEXT,
    mo_ta TEXT,
    khoi_kien_thuc TEXT,
    trang_thai TEXT
);

CREATE TABLE ctdt_hoc_phan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ctdt_id INTEGER,
    hp_id INTEGER,
    khoi_kien_thuc TEXT,
    chuyen_nganh TEXT,
    thu_tu INTEGER
);

CREATE TABLE clo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER,
    ma TEXT,
    mo_ta TEXT,
    cdr_ma TEXT,
    level_irm TEXT
);

CREATE TABLE muc_tieu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER,
    so_thu_tu INTEGER,
    mo_ta TEXT,
    cdr_ma TEXT
);

CREATE TABLE hoc_lieu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hp_id INTEGER,
    loai TEXT,
    tac_gia TEXT,
    ten TEXT,
    thong_tin TEXT,
    noi_dung TEXT,
    tai_lieu_id INTEGER
);

CREATE TABLE Rubric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_hp TEXT,
    ma_rubric TEXT,
    ten TEXT
);
"""


class FakeDB:
    def __init__(self, conn):
        self.conn = conn

    def transaction(self):
        class Transaction:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                if not self.conn.in_transaction:
                    self.conn.execute("BEGIN")
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.conn.rollback()
                else:
                    self.conn.commit()

        return Transaction(self.conn)


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(LEGACY_SCHEMA_SQL)
    return FakeDB(conn)


class TestEnterpriseSchema(unittest.TestCase):
    def setUp(self):
        self.db = make_db()

    def tearDown(self):
        self.db.conn.close()

    def test_schema_upgrade_creates_all_domain_tables_and_metadata(self):
        apply_enterprise_schema_upgrade(self.db)
        tables = {
            row["name"].lower()
            for row in self.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        for table in ACADEMIC_SYSTEM_SCHEMA:
            self.assertIn(table, tables)

        clo_cols = {row["name"] for row in self.db.conn.execute("PRAGMA table_info(clo)").fetchall()}
        self.assertIn("clo_code", clo_cols)
        self.assertIn("assessment_methods", clo_cols)
        rubric_cols = {row["name"] for row in self.db.conn.execute("PRAGMA table_info(Rubric)").fetchall()}
        self.assertIn("rubric_code", rubric_cols)
        self.assertIn("syllabus_id", rubric_cols)

        meta_count = self.db.conn.execute("SELECT COUNT(*) FROM academic_field_meta").fetchone()[0]
        self.assertGreater(meta_count, 100)

    def test_enterprise_repository_uses_schema_metadata(self):
        apply_enterprise_schema_upgrade(self.db)
        repo = EnterpriseRepository(self.db)

        dept_id = repo.insert(
            "department",
            {"department_code": "K.CNTT", "department_name_vi": "CNTT", "unknown": "ignored"},
        )
        row = repo.get("department", dept_id)
        self.assertEqual(row["department_code"], "K.CNTT")

        form = repo.form_schema("syllabus")
        self.assertTrue(any(field["field_name"] == "content_type" for field in form))

    def test_bridge_legacy_data_is_idempotent(self):
        apply_enterprise_schema_upgrade(self.db)
        conn = self.db.conn
        khoa_id = conn.execute("INSERT INTO khoa(ma, ten) VALUES('K.CNTT', 'Cong nghe thong tin')").lastrowid
        gv_id = conn.execute(
            "INSERT INTO giang_vien(ho_ten, hoc_vi, email, khoa_id, ma_can_bo) VALUES('Nguyen A', 'TS', 'a@example.com', ?, 'GV001')",
            (khoa_id,),
        ).lastrowid
        ctdt_id = conn.execute("INSERT INTO chuong_trinh_dao_tao(ten, bac, khoa_id) VALUES('Ky thuat phan mem', 'Dai hoc', ?)", (khoa_id,)).lastrowid
        conn.execute("INSERT INTO chuyen_nganh(ctdt_id, ten) VALUES(?, 'Cong nghe phan mem')", (ctdt_id,))
        hp_id = conn.execute(
            """
            INSERT INTO hoc_phan(ma, ten_viet, ten_anh, trinh_do, khoa_id, so_tin_chi, loai, tinh_chat,
                                 gio_lt, gio_th, gio_tl, gio_tu_hoc, tong_gio, mo_ta, trang_thai)
            VALUES('IT101', 'Nhap mon lap trinh', 'Intro', 'Dai hoc', ?, 3, 'Bat buoc', 'Ly thuyet',
                   30, 0, 15, 90, 45, 'Mo ta', 'nhap')
            """,
            (khoa_id,),
        ).lastrowid
        conn.execute("INSERT INTO ctdt_hoc_phan(ctdt_id, hp_id, thu_tu) VALUES(?, ?, 1)", (ctdt_id, hp_id))
        conn.execute("INSERT INTO clo(hp_id, ma, mo_ta, cdr_ma, level_irm) VALUES(?, 'CLO1', 'Hieu', 'PLO1', 'I')", (hp_id,))
        conn.execute("INSERT INTO muc_tieu(hp_id, so_thu_tu, mo_ta, cdr_ma) VALUES(?, 1, 'Muc tieu', 'PLO1')", (hp_id,))
        conn.execute("INSERT INTO hoc_lieu(hp_id, loai, ten, tac_gia) VALUES(?, 'main', 'Sach A', 'Tac gia')", (hp_id,))
        self.assertIsNotNone(gv_id)

        svc = EnterpriseSchemaService(self.db)
        first = svc.bridge_legacy_data()
        second = svc.bridge_legacy_data()

        self.assertEqual(first["courses"], 1)
        self.assertEqual(second["courses"], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM course").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM syllabus").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT clo_code FROM clo").fetchone()[0], "CLO1")
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM syllabus_objective").fetchone()[0], 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM syllabus_material").fetchone()[0], 1)

        coverage = svc.validate_schema_coverage()
        self.assertTrue(coverage["complete"])


if __name__ == "__main__":
    unittest.main()
