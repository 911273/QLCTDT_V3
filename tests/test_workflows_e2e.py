import os
import shutil
import sys
import tempfile
import unittest

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import Database
from services.enterprise_schema_service import EnterpriseSchemaService
from services.excel_export_service import ExcelExportService
from services.excel_template_engine import ExcelTemplateEngine
from services.syllabus_workflow_validator import SyllabusWorkflowValidator


class EndToEndWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "workflow.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _create_default_excel_template(self) -> int:
        template_path = os.path.join(self.tmp, "syllabus_template.xlsx")
        ExcelTemplateEngine().create_default_template(template_path)
        with self.db.transaction():
            cur = self.db.conn.execute(
                """
                INSERT INTO excel_template(ten, mo_ta, file_path, placeholders, la_mac_dinh, created_at, updated_at)
                VALUES(?,?,?,?,1,datetime('now'),datetime('now'))
                """,
                ("Workflow default", "E2E default template", template_path, "[]"),
            )
        return cur.lastrowid

    def _create_complete_syllabus(self) -> int:
        khoa_id = self.db.conn.execute("INSERT INTO khoa(ma, ten) VALUES('K.CNTT', 'Khoa Công nghệ thông tin')").lastrowid
        gv_id = self.db.conn.execute(
            """
            INSERT INTO giang_vien(ho_ten, hoc_vi, sdt, email, khoa_id, ma_can_bo)
            VALUES('Nguyễn Văn Ánh', 'TS', '0900000000', 'anh@example.com', ?, 'GV001')
            """,
            (khoa_id,),
        ).lastrowid
        ctdt_id = self.db.conn.execute(
            "INSERT INTO chuong_trinh_dao_tao(ten, bac, khoa_id) VALUES('Kỹ thuật phần mềm', 'Đại học', ?)",
            (khoa_id,),
        ).lastrowid
        self.db.conn.execute("INSERT INTO chuyen_nganh(ctdt_id, ten) VALUES(?, 'Công nghệ phần mềm')", (ctdt_id,))

        hp_id = self.db.add_hoc_phan(
            {
                "ma": "IT2026",
                "ten_viet": "Nhập môn kiểm thử phần mềm",
                "ten_anh": "Introduction to Software Testing",
                "trinh_do": "Đại học",
                "khoa_id": khoa_id,
                "so_tin_chi": 3,
                "loai": "Bắt buộc",
                "tinh_chat": "Lý thuyết",
                "gio_lt": 30,
                "gio_bt": 15,
                "gio_tl": 0,
                "gio_th_tn": 0,
                "gio_th": 0,
                "gio_tu_hoc": 90,
                "tong_gio": 135,
                "hp_tien_quyet": "IT100 - Tin học cơ sở",
                "hp_thay_the": "Không có",
                "mo_ta": "Học phần kiểm thử với dữ liệu tiếng Việt có dấu.",
                "pp_day_hoc": "Thuyết trình, thảo luận, bài tập tình huống",
                "dia_diem_ky": "Hà Nội",
                "ngay_ky": "19/05/2026",
                "chuc_danh_ky_trai": "Giảng viên phụ trách",
                "ho_ten_ky_trai": "Nguyễn Văn Ánh",
                "chuc_danh_ky_phai": "Trưởng khoa",
                "ho_ten_ky_phai": "Trần Bình",
                "trang_thai": "nhap",
            }
        )
        self.db.update_hp_ctdt_links(hp_id, [{"ctdt_id": ctdt_id, "khoi_kien_thuc": "core", "chuyen_nganh": "Công nghệ phần mềm"}])
        self.db.conn.execute(
            """
            INSERT INTO hp_giang_vien(hp_id, gv_id, ho_ten, hoc_ham_vi, email, sdt, vai_tro, thu_tu, don_vi)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (hp_id, gv_id, "Nguyễn Văn Ánh", "TS", "anh@example.com", "0900000000", "phu_trach", 1, "Khoa CNTT"),
        )
        self.db.set_muc_tieu(
            hp_id,
            [
                {"mo_ta": "Hiểu quy trình kiểm thử", "cdr_ma": "PLO1"},
                {"mo_ta": "Thiết kế ca kiểm thử", "cdr_ma": "PLO2"},
            ],
        )
        self.db.set_clo(
            hp_id,
            [
                {"ma": "CLO1", "mo_ta": "Phân tích yêu cầu kiểm thử", "cdr_ma": "PLO1", "level_irm": "I", "cap_do_bloom": 3},
                {"ma": "CLO2", "mo_ta": "Thiết kế test case", "cdr_ma": "PLO2", "level_irm": "R", "cap_do_bloom": 4},
            ],
        )
        self.db.set_hoc_lieu(
            hp_id,
            [
                {"loai": "5.1", "tac_gia": "Ammann", "ten": "Introduction to Software Testing", "thong_tin": "Cambridge"},
                {"loai": "5.2", "tac_gia": "Myers", "ten": "The Art of Software Testing", "thong_tin": "Wiley"},
            ],
        )
        self.db.set_noi_dung(
            hp_id,
            "lt",
            [
                {
                    "ten": "Tổng quan kiểm thử",
                    "cap_do": 1,
                    "thu_tu": 1,
                    "gio_lt": 6,
                    "gio_bt": 3,
                    "cdr_ma": "CLO1",
                    "pp_day": "Thuyết trình",
                    "pp_hoc": "Đọc tài liệu",
                    "bai_danh_gia": "A1",
                },
                {
                    "ten": "Thiết kế test case",
                    "cap_do": 1,
                    "thu_tu": 2,
                    "gio_lt": 8,
                    "gio_bt": 4,
                    "cdr_ma": "CLO2",
                    "pp_day": "Bài tập",
                    "pp_hoc": "Thực hành nhóm",
                    "bai_danh_gia": "A2",
                },
            ],
        )
        self.db.set_ke_hoach_kt(
            hp_id,
            [
                {
                    "nhom": "thuong_xuyen",
                    "ty_trong_nhom": 40,
                    "noi_dung": "Bài tập kiểm thử",
                    "hinh_thuc": "Bài tập",
                    "thoi_gian": "Tuần 5",
                    "thang_diem": "10",
                    "clo_lien_quan": "CLO1,CLO2",
                },
                {
                    "nhom": "cuoi_ky",
                    "ty_trong_nhom": 60,
                    "noi_dung": "Đồ án cuối kỳ",
                    "hinh_thuc": "Báo cáo",
                    "thoi_gian": "Tuần 15",
                    "thang_diem": "10",
                    "clo_lien_quan": "CLO2",
                },
            ],
        )
        self.db.set_rubrics_full(
            hp_id,
            [
                {
                    "ten": "Rubric đánh giá test case",
                    "ky_hieu": "RB1",
                    "mo_ta": "Đánh giá phân tích và thiết kế",
                    "thu_tu": 1,
                    "tieu_chi_list": [
                        {
                            "tieu_chi": "Đầy đủ ca kiểm thử",
                            "trong_so": "50",
                            "muc_xuat_sac": "Bao phủ đầy đủ",
                            "muc_tot": "Bao phủ tốt",
                            "muc_dat": "Đạt cơ bản",
                            "muc_chua_dat": "Thiếu nhiều",
                            "thu_tu": 1,
                        }
                    ],
                }
            ],
        )
        self.db.set_lich_su(
            hp_id,
            [{"noi_dung": "Tạo đề cương workflow test", "ngay": "2026-05-19", "nguoi_cap_nhat": "QA"}],
        )
        self.db.conn.commit()
        return hp_id

    def test_workflow_create_reload_validate_bridge_export_excel(self):
        self._create_default_excel_template()
        hp_id = self._create_complete_syllabus()

        validator = SyllabusWorkflowValidator(self.db)
        result = validator.validate(hp_id)
        self.assertTrue(result["valid"], result["issues"])

        svc = EnterpriseSchemaService(self.db)
        bridge = svc.bridge_legacy_data()
        self.assertGreaterEqual(bridge["courses"], 1)
        self.assertTrue(svc.validate_schema_coverage()["complete"])

        self.db.close()
        reopened = Database(self.db_path)
        try:
            hp = reopened.get_hoc_phan(hp_id)
            self.assertEqual(hp["ten_viet"], "Nhập môn kiểm thử phần mềm")
            self.assertEqual(len(reopened.get_clo(hp_id)), 2)

            out_path = os.path.join(self.tmp, "workflow_export.xlsx")
            self.assertTrue(ExcelExportService(reopened).export_with_default(hp_id, out_path))
            self.assertTrue(os.path.exists(out_path))

            wb = openpyxl.load_workbook(out_path)
            self.assertEqual(wb["Overview"]["B3"].value, "Nhập môn kiểm thử phần mềm")
            self.assertEqual(wb["CLOs"]["A4"].value, "CLO1")
            self.assertEqual(wb["Assessment"]["G4"].value, 40)
            self.assertEqual(wb["Rubrics"]["A4"].value, "RB1")
            self.assertEqual(wb["RevisionHistory"]["B4"].value, "Tạo đề cương workflow test")
            self.assertEqual(wb["Approval"]["B3"].value, "Hà Nội")
        finally:
            reopened.close()

    def test_workflow_validator_detects_broken_clo_and_assessment_weight(self):
        hp_id = self._create_complete_syllabus()
        self.db.set_clo(
            hp_id,
            [
                {"ma": "CLO1", "mo_ta": "A", "cdr_ma": "PLO1", "level_irm": "X"},
                {"ma": "CLO1", "mo_ta": "B", "cdr_ma": "", "level_irm": "I"},
            ],
        )
        self.db.set_ke_hoach_kt(
            hp_id,
            [{"nhom": "cuoi_ky", "ty_trong_nhom": 80, "noi_dung": "Thi", "hinh_thuc": "Tự luận"}],
        )

        result = SyllabusWorkflowValidator(self.db).validate(hp_id)
        messages = "\n".join(issue["message"] for issue in result["issues"])
        self.assertFalse(result["valid"])
        self.assertIn("Duplicate CLO code", messages)
        self.assertIn("invalid I/R/M", messages)
        self.assertIn("expected 100", messages)


if __name__ == "__main__":
    unittest.main()
