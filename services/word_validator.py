# services/word_validator.py
import re

class DCCTValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        message = "Validation Failed:\n" + "\n".join([f"[{e['code']}] {e['field']}: {e['message']}" for e in errors])
        super().__init__(message)

CONTACT_HOURS_PER_CREDIT = 15


def _as_number(value, default=0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _get_credits(data: dict) -> int:
    return _as_int(data.get('so_tc', data.get('Credits', data.get('so_tin_chi', 0))))


def _get_contact_hours(data: dict) -> float:
    pb = data.get('phan_bo_gio')
    if isinstance(pb, dict) and pb:
        return (
            _as_number(pb.get('ly_thuyet')) +
            _as_number(pb.get('thuc_hanh_tn')) +
            _as_number(pb.get('thao_luan')) +
            _as_number(pb.get('tieu_luan_do_an')) +
            _as_number(pb.get('thuc_tap'))
        )
    return (
        _as_number(data.get('HoursLT', data.get('gio_lt'))) +
        _as_number(data.get('HoursBT', data.get('gio_bt'))) +
        _as_number(data.get('HoursTH', data.get('gio_th_tn'))) +
        _as_number(data.get('HoursTL', data.get('gio_tl'))) +
        _as_number(data.get('HoursTieuLuan', data.get('gio_tieu_luan'))) +
        _as_number(data.get('HoursThucTap', data.get('gio_thuc_tap')))
    )


def _get_clos(data: dict) -> list:
    clos = data.get('clo')
    if clos is None:
        clos = data.get('CLOs', [])
    normalized = []
    for clo in clos or []:
        normalized.append({
            'ma': clo.get('ma', clo.get('Code', '')),
            'mo_ta': clo.get('mo_ta', clo.get('Desc', '')),
            'muc_do': clo.get('muc_do', clo.get('Level', '')),
        })
    return normalized


def _get_assessment(data: dict) -> list:
    rows = data.get('thanh_phan_dg')
    if rows is None:
        rows = data.get('AssessmentRows', [])
    normalized = []
    for row in rows or []:
        normalized.append({
            'thanh_phan': row.get('thanh_phan', row.get('nhom', row.get('Label', ''))),
            'trong_so': row.get('trong_so', row.get('ty_trong_nhom', row.get('Weight', 0))),
        })
    return normalized


def _get_rubrics(data: dict) -> list:
    rows = data.get('rubrics')
    if rows is None:
        rows = data.get('Rubrics', [])
    normalized = []
    for rb in rows or []:
        criteria = rb.get('tieu_chi')
        if criteria is None:
            criteria = rb.get('Criteria', rb.get('tieu_chi_list', []))
        normalized.append({
            'ma': rb.get('ma', rb.get('ky_hieu', rb.get('Code', ''))),
            'tieu_chi': criteria or [],
        })
    return normalized


def validate_data(data: dict) -> list:
    """
    Kiểm tra dữ liệu sinh ĐCCTHP theo 10 rules.
    Trả về list of error dicts. Trống nghĩa là hợp lệ.
    """
    errors = []
    
    # helper
    def add_error(field, code, message, severity="error"):
        errors.append({"field": field, "code": code, "message": message, "severity": severity})

    # [V1] so_tc > 0 và là số nguyên
    so_tc = _get_credits(data)
    if so_tc <= 0:
        add_error('so_tc', 'V1', 'Số tín chỉ phải là số nguyên > 0')

    # [V2] Giờ lên lớp tối thiểu theo quy tắc chung của app: 1 TC = 15 tiết lên lớp.
    contact_hours = _get_contact_hours(data)
    expected_contact = so_tc * CONTACT_HOURS_PER_CREDIT
    if contact_hours > 0 and contact_hours < expected_contact:
        add_error(
            'phan_bo_gio',
            'V2',
            f'Tổng giờ lên lớp ({contact_hours:g}) thấp hơn số tín chỉ x {CONTACT_HOURS_PER_CREDIT} ({expected_contact:g})',
            severity='warning'
        )

    # [V3] [V4] CLO
    clos = _get_clos(data)
    invalid_verbs = [r'^biết\b', r'^hiểu\b', r'^nắm vững\b']
    for clo in clos:
        mo_ta = (clo.get('mo_ta') or '').strip().lower()
        if any(re.match(pattern, mo_ta) for pattern in invalid_verbs):
            add_error(f"clo.{clo.get('ma')}", 'V3', f"Mô tả CLO không được bắt đầu bằng Biết/Hiểu/Nắm vững: '{mo_ta}'")
        
        muc_do = (clo.get('muc_do') or '').strip().upper()
        if muc_do and muc_do not in ('I', 'R', 'M'):
            add_error(f"clo.{clo.get('ma')}", 'V4', f"Mức độ CLO phải là I, R, hoặc M. Nhận được: '{muc_do}'")

    # [V5] Tổng trọng số đánh giá == 100
    thanh_phan_dg = _get_assessment(data)
    tong_trong_so = 0
    for dg in thanh_phan_dg:
        tp = (dg.get('thanh_phan') or '').lower()
        if 'chuyên cần' not in tp and 'chuyen can' not in tp:
            try:
                tong_trong_so += float(dg.get('trong_so', 0))
            except ValueError:
                pass
    if abs(tong_trong_so - 100) > 0.01 and thanh_phan_dg:
         add_error('thanh_phan_dg', 'V5', f'Tổng trọng số các bài đánh giá (trừ chuyên cần) phải = 100%. Hiện tại: {tong_trong_so}%')

    # [V6] Mỗi Rubric tổng trọng số == 100%
    rubrics = _get_rubrics(data)
    for rb in rubrics:
        tong_rb = 0
        for tc in rb.get('tieu_chi', []):
            try:
                # Xử lý chuỗi như "40%"
                ts_str = str(tc.get('trong_so', '0')).replace('%', '').strip()
                tong_rb += float(ts_str)
            except ValueError:
                pass
        if abs(tong_rb - 100) > 0.01:
            add_error(f"rubrics.{rb.get('ma')}", 'V6', f"Tổng trọng số tiêu chí của Rubric {rb.get('ma')} phải = 100%. Hiện tại: {tong_rb}%")

    # [V7] ai_policy_level
    ai_level = data.get('ai_policy_level', data.get('AiPolicyLevel', 1))
    if ai_level not in (1, 2, 3):
        add_error('ai_policy_level', 'V7', f"Mức độ AI policy phải thuộc {{1, 2, 3}}. Hiện tại: {ai_level}")

    # [V8] Tiến sĩ: bai_bao_quoc_te <= 10
    if data.get('trinh_do') == 'Tiến sĩ':
        bb = data.get('bai_bao_quoc_te', [])
        if len(bb) > 10:
             add_error('bai_bao_quoc_te', 'V8', f"Với bậc Tiến sĩ, bài báo quốc tế khai báo tối đa 10 mục. Hiện tại: {len(bb)}")

    # [V9] ten_tv và ten_ta không rỗng
    ten_tv = data.get('ten_tv', data.get('CourseName', data.get('ten_viet', '')))
    ten_ta = data.get('ten_ta', data.get('CourseNameEN', data.get('ten_anh', '')))
    if not ten_tv or not str(ten_tv).strip():
        add_error('ten_tv', 'V9', 'Tên tiếng Việt không được để trống')
    if not ten_ta or not str(ten_ta).strip():
        add_error('ten_ta', 'V9', 'Tên tiếng Anh không được để trống')

    # [V10] Số giảng viên chính >= 1
    gv_chinh = data.get('giang_vien_chinh', [])
    if len(gv_chinh) < 1:
        add_error('giang_vien_chinh', 'V10', 'Phải có ít nhất 1 giảng viên phụ trách chính')

    return errors
