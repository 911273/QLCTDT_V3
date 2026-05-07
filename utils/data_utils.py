import re

def natural_sort_key(s):
    """
    Hàm tạo key để sắp xếp chuỗi theo thứ tự tự nhiên (Natural Sort).
    Ví dụ: 'PO1', 'PO2', 'PO10' thay vì 'PO1', 'PO10', 'PO2'.
    """
    if s is None:
        return []
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]


def extract_codes(raw_string: str) -> list:
    """
    Trích xuất danh sách các mã (PLO, PI, PO...) từ chuỗi thô.
    Hỗ trợ dấu phẩy, chấm phẩy, xuống dòng và khoảng trắng.
    Trả về list các mã đã viết hoa và strip khoảng trắng.
    """
    if not raw_string:
        return []
    # Thay thế các ký tự phân cách bằng dấu phẩy
    cleaned = raw_string.replace(';', ',').replace('\n', ',')
    # Tách chuỗi và làm sạch
    codes = [c.strip().upper() for c in cleaned.split(',') if c.strip()]
    return codes
