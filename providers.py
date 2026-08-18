JT_EXPRESS = "JT_EXPRESS"
SHOPEE_EXPRESS = "SHOPEE_EXPRESS"

JT_EXPRESS_STATUSES = [
    ("103", "Đơn hàng đã được tạo"),
    ("104", "ĐVVC lấy hàng thất bại"),
    ("105", "Đơn hàng đã bị huỷ"),
    ("106", "ĐVVC lấy hàng thành công"),
    ("109", "Đơn hàng đã rời kho phân loại"),
    ("110", "Đơn hàng đã đến kho phân loại"),
    ("112", "Đơn hàng đang được giao đến người nhận"),
    ("113", "Giao hàng thành công"),
    ("116", "Đang hoàn hàng về Người Bán"),
    ("117", "Hoàn hàng thành công"),
    ("118", "Giao hàng thất bại"),
    ("120", "Hoàn hàng thất bại"),
    ("121", "Hoàn tất"),
]

SHOPEE_EXPRESS_STATUSES = [
    ("1001", "Chờ lấy hàng"),
    ("2001", "Đang vận chuyển"),
    ("2006", "Đang giao hàng"),
    ("3001", "Tạm giữ hàng"),
    ("4001", "Giao hàng thành công"),
    ("5001", "Lấy hàng thất bại"),
    ("5002", "Hàng bị hư hỏng"),
    ("5003", "Hàng bị thất lạc"),
    ("6001", "Đang hoàn hàng về người gửi"),
    ("6002", "Hoàn hàng thất bại"),
    ("6003", "Hoàn hàng thành công"),
    ("7001", "Mã vận đơn đã hết hạn"),
]

STATUSES_BY_PROVIDER = {
    JT_EXPRESS: JT_EXPRESS_STATUSES,
    SHOPEE_EXPRESS: SHOPEE_EXPRESS_STATUSES,
}

TERMINAL_BY_PROVIDER = {
    JT_EXPRESS: {"105", "113", "117", "121"},
    SHOPEE_EXPRESS: {"4001", "6003", "7001"},
}

ORDER_EFFECT_BY_PROVIDER = {
    JT_EXPRESS: {"106": "shipped", "113": "delivered"},
    SHOPEE_EXPRESS: {"2001": "shipped", "4001": "delivered"},
}


def statuses_for(provider):
    return STATUSES_BY_PROVIDER.get(provider, [])


def label_for(provider, status):
    for code, label in statuses_for(provider):
        if code == status:
            return label
    return ""


def annotate(provider, status):
    marks = []
    if status in TERMINAL_BY_PROVIDER.get(provider, set()):
        marks.append("KẾT THÚC")
    effect = ORDER_EFFECT_BY_PROVIDER.get(provider, {}).get(status)
    if effect:
        marks.append(effect.upper())
    return " ".join(marks)
