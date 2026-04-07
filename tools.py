from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from langchain_core.tools import tool

#
# MOCK DATA - Dữ liệu giả lập hệ thống du lịch
#
# Lưu ý: Giá cả có logic (VD: cuối tuần đắt hơn, hạng cao hơn đắt hơn)
# Sinh viên cần đọc hiểu data để debug test cases.
#

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1_200_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1_350_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1_100_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1_600_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1_300_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3_200_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650_000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3_500_000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1_500_000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800_000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200_000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
}

_CITY_ALIASES = {
    "ha noi": "Hà Nội",
    "hanoi": "Hà Nội",
    "hn": "Hà Nội",
    "da nang": "Đà Nẵng",
    "danang": "Đà Nẵng",
    "dn": "Đà Nẵng",
    "phu quoc": "Phú Quốc",
    "pq": "Phú Quốc",
    "ho chi minh": "Hồ Chí Minh",
    "thanh pho ho chi minh": "Hồ Chí Minh",
    "tp ho chi minh": "Hồ Chí Minh",
    "tphcm": "Hồ Chí Minh",
    "tp hcm": "Hồ Chí Minh",
    "hcm": "Hồ Chí Minh",
    "hcmc": "Hồ Chí Minh",
    "sai gon": "Hồ Chí Minh",
    "saigon": "Hồ Chí Minh",
}

_EXPENSE_PATTERN = re.compile(
    r"\s*([^:,\n]+?)\s*:\s*([\d.,_\s]+(?:\s*(?:vnđ|vnd|đ))?)\s*(?:,|;|\n|$)",
    re.IGNORECASE,
)


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def _normalize_city(text: str) -> str:
    cleaned = " ".join(text.strip().lower().split())
    cleaned = cleaned.replace("tp.", "tp ").replace("tp ", "tp ")
    cleaned = cleaned.replace("thành phố", "thanh pho")
    cleaned = _strip_accents(cleaned)
    return _CITY_ALIASES.get(cleaned, text.strip().title())


def _format_currency(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def _parse_amount(value: int | str) -> int:
    if isinstance(value, int):
        return value

    digits = re.sub(r"[^\d]", "", value)
    if not digits:
        raise ValueError("Không đọc được số tiền hợp lệ.")
    return int(digits)


def _sorted_flights(flights: Iterable[dict]) -> list[dict]:
    return sorted(flights, key=lambda item: (item["price"], item["departure"], item["airline"]))


def _sorted_hotels(hotels: Iterable[dict]) -> list[dict]:
    return sorted(hotels, key=lambda item: (-item["rating"], item["price_per_night"], -item["stars"]))


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.

    Tham số:
    - origin: thành phố khởi hành (VD: 'Hà Nội', 'Hồ Chí Minh')
    - destination: thành phố đến (VD: 'Đà Nẵng', 'Phú Quốc')

    Trả về danh sách chuyến bay với hãng, giờ bay, giá vé.
    Nếu không tìm thấy tuyến bay, trả về thông báo không có chuyến.
    """
    try:
        origin_city = _normalize_city(origin)
        destination_city = _normalize_city(destination)

        if not origin_city or not destination_city:
            return "Thiếu thông tin điểm đi hoặc điểm đến. Vui lòng cung cấp đầy đủ hai thành phố."

        if origin_city == destination_city:
            return "Điểm đi và điểm đến đang trùng nhau, nên chưa thể tìm chuyến bay phù hợp."

        flights = FLIGHTS_DB.get((origin_city, destination_city))
        used_reverse_route = False

        if not flights:
            flights = FLIGHTS_DB.get((destination_city, origin_city))
            used_reverse_route = flights is not None

        if not flights:
            return (
                f"Hiện chưa có dữ liệu chuyến bay cho tuyến {origin_city} -> {destination_city}. "
                "Bạn có thể thử đổi điểm đi hoặc điểm đến khác."
            )

        lines = [f"Kết quả chuyến bay cho tuyến {origin_city} -> {destination_city}:"]
        if used_reverse_route:
            lines.append(
                f"Lưu ý: hệ thống không có dữ liệu chiều đi trực tiếp, nên đang dùng dữ liệu chiều ngược "
                f"{destination_city} -> {origin_city} để tham khảo."
            )

        for index, flight in enumerate(_sorted_flights(flights), start=1):
            flight_class = "Phổ thông" if flight["class"] == "economy" else "Thương gia"
            lines.append(
                f"{index}. {flight['airline']} | {flight['departure']} - {flight['arrival']} | "
                f"{flight_class} | {_format_currency(flight['price'])}"
            )

        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tìm chuyến bay: {exc}"


@tool
def search_hotels(city: str, max_price_per_night: int = 99_999_999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.

    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ), mặc định không giới hạn

    Trả về danh sách khách sạn phù hợp với tên, số sao, giá, khu vực, rating.
    """
    try:
        city_name = _normalize_city(city)
        budget_cap = _parse_amount(max_price_per_night)

        hotels = HOTELS_DB.get(city_name)
        if not hotels:
            return f"Hiện chưa có dữ liệu khách sạn tại {city_name}."

        matched_hotels = [hotel for hotel in hotels if hotel["price_per_night"] <= budget_cap]
        matched_hotels = _sorted_hotels(matched_hotels)

        if not matched_hotels:
            cheapest = min(hotel["price_per_night"] for hotel in hotels)
            return (
                f"Không tìm thấy khách sạn nào ở {city_name} với giá tối đa "
                f"{_format_currency(budget_cap)}/đêm. Mức thấp nhất hiện có là {_format_currency(cheapest)}/đêm."
            )

        lines = [
            f"Tìm thấy {len(matched_hotels)} khách sạn phù hợp tại {city_name} "
            f"(tối đa {_format_currency(budget_cap)}/đêm):"
        ]
        for index, hotel in enumerate(matched_hotels, start=1):
            lines.append(
                f"{index}. {hotel['name']} | {hotel['stars']} sao | {_format_currency(hotel['price_per_night'])}/đêm | "
                f"Khu vực: {hotel['area']} | Rating: {hotel['rating']}"
            )

        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tìm khách sạn: {exc}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.

    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ)
    - expenses: chuỗi mô tả các khoản chi, mỗi khoản cách nhau bởi dấu phẩy,
      định dạng 'tên_khoản: số_tiền'
      Ví dụ: 'vé_máy_bay: 890000, khách_sạn: 650000'

    Trả về bảng chi tiết các khoản chi và số tiền còn lại.
    Nếu vượt ngân sách, cảnh báo rõ ràng số tiền thiếu.
    """
    try:
        budget = _parse_amount(total_budget)
        if budget <= 0:
            return "Tổng ngân sách phải lớn hơn 0."

        raw_expenses = expenses.strip()
        if not raw_expenses:
            return "Danh sách chi phí đang trống. Hãy cung cấp theo dạng 'vé_bay: 1100000, khách_sạn: 1600000'."

        matches = list(_EXPENSE_PATTERN.finditer(raw_expenses))
        if not matches:
            return (
                "Không đọc được danh sách chi phí. Vui lòng dùng đúng định dạng "
                "'tên_khoản: số_tiền, tên_khoản_khác: số_tiền'."
            )

        remainder = _EXPENSE_PATTERN.sub("", raw_expenses).strip(" ,;\n\t")
        if remainder:
            return (
                "Một phần dữ liệu chi phí có định dạng không hợp lệ. "
                "Vui lòng dùng đúng mẫu 'tên_khoản: số_tiền, tên_khoản_khác: số_tiền'."
            )

        parsed_items: list[tuple[str, int]] = []
        for match in matches:
            label = match.group(1).strip()
            amount = _parse_amount(match.group(2))
            if not label:
                return "Tên khoản chi không được để trống."
            parsed_items.append((label.replace("_", " "), amount))

        total_expense = sum(amount for _, amount in parsed_items)
        remaining = budget - total_expense

        lines = [
            f"Tổng ngân sách: {_format_currency(budget)}",
            "Chi tiết chi phí:",
        ]
        for label, amount in parsed_items:
            lines.append(f"- {label}: {_format_currency(amount)}")

        lines.append(f"Tổng chi: {_format_currency(total_expense)}")
        if remaining >= 0:
            lines.append(f"Còn lại: {_format_currency(remaining)}")
        else:
            lines.append(f"Vượt ngân sách: {_format_currency(abs(remaining))}")

        return "\n".join(lines)
    except Exception as exc:
        return f"Lỗi khi tính ngân sách: {exc}"
