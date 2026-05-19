# QLCTDT Anti V1.4.3

## Enterprise Academic QA Foundation

The app includes a non-destructive enterprise schema foundation for MOET/AUN-QA/ABET/CDIO/OBE/CQI workflows.
Migration v19 creates metadata-driven academic domain tables, preserves legacy V23 data, and exposes a schema
browser under `He thong -> Enterprise schema / QA foundation`.

See `docs/enterprise_schema_foundation.md` for the migration/bridge contract and validation command.

Hệ thống Quản lý Chuẩn đầu ra và Đề cương chi tiết (EPU APM System).

## Tính năng chính
- Quản lý ngân hàng câu hỏi.
- Trộn đề thi.
- Quản lý đề cương chi tiết học phần.
- Xuất/Nhập dữ liệu từ tệp Word.
- Quản lý Chuẩn đầu ra (CLO) và mục tiêu môn học (PO).

## Yêu cầu hệ thống
- Python 3.x
- Các thư viện phụ thuộc: `ttkbootstrap`, `python-docx`, `sqlite3`, v.v.

## Cách chạy ứng dụng
```bash
python main.py
```
