# Test Results

Nội dung dưới đây là console log được ghi lại từ các lần chạy test case bằng `agent.py`.

## Test 1: Direct Answer
**Console Log**
```text
Bạn: Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.

TravelBuddy đang suy nghĩ...
Trả lời trực tiếp

TravelBuddy: Xin chào! Rất vui được hỗ trợ bạn trong chuyến đi du lịch. Bạn có thể cho tôi biết thêm về sở thích của bạn không? Bạn thích biển, núi, hay khám phá văn hóa? Ngoài ra, bạn có ngân sách dự kiến cho chuyến đi này không?
```

## Test 2: Single Tool Call
**Console Log**
```text
Bạn: Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng

TravelBuddy đang suy nghĩ...
Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Đà Nẵng'})
Trả lời trực tiếp

TravelBuddy: Dưới đây là các chuyến bay từ Hà Nội đi Đà Nẵng:

1. **VietJet Air**: 08:30 - 09:50 | Phổ thông | **890.000đ**
2. **Bamboo Airways**: 11:00 - 12:20 | Phổ thông | **1.200.000đ**
3. **Vietnam Airlines**: 06:00 - 07:20 | Phổ thông | **1.450.000đ**
4. **Vietnam Airlines**: 14:00 - 15:20 | Thương gia | **2.800.000đ**

Lựa chọn tiết kiệm nhất là chuyến bay của VietJet Air với giá 890.000đ. Bạn có cần thêm thông tin gì khác không?
```

## Test 3: Multi-Step Tool Chaining
**Console Log**
```text
Bạn: Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!

TravelBuddy đang suy nghĩ...
Gọi tool: search_flights({'origin': 'Hà Nội', 'destination': 'Phú Quốc'})
Gọi tool: search_hotels({'city': 'Phú Quốc', 'max_price_per_night': 1500000})
Gọi tool: calculate_budget({'total_budget': 5000000, 'expenses': 'vé_máy_bay: 1100000, khách_sạn: 1600000'})
Trả lời trực tiếp

TravelBuddy: Dưới đây là thông tin chuyến đi của bạn từ Hà Nội đến Phú Quốc:

**Chuyến bay:**
- **Lựa chọn chính:** VietJet Air | 16:00 - 18:15 | Phổ thông | **Giá: 1.100.000đ**
- **Lựa chọn thay thế:** VietJet Air | 10:00 - 12:15 | Phổ thông | **Giá: 1.350.000đ**

**Khách sạn:**
- **Khách sạn phù hợp nhất:** Sol by Meliá | 4 sao | **Giá: 1.500.000đ/đêm** | Khu vực: Bãi Trường | Rating: 4.2
- **Lựa chọn thay thế:** Lahana Resort | 3 sao | **Giá: 800.000đ/đêm** | Khu vực: Dương Đông | Rating: 4.0

**Tổng chi phí ước tính:**
- **Tổng ngân sách ban đầu:** 5.000.000đ
- **Chi phí vé máy bay:** 1.100.000đ
- **Chi phí khách sạn (2 đêm):** 1.600.000đ
- **Tổng chi:** 2.700.000đ
- **Số tiền còn lại:** 2.300.000đ

**Gợi ý thêm:**
- Bạn có thể sử dụng số tiền còn lại để tham gia các hoạt động vui chơi, ăn uống hoặc mua sắm tại Phú Quốc.
- Nếu bạn cần thêm thông tin về các hoạt động tại Phú Quốc hoặc muốn đặt vé máy bay và khách sạn, hãy cho tôi biết nhé!
```

## Test 4: Missing Info / Clarification
**Console Log**
```text
Bạn: Tôi muốn đặt khách sạn

TravelBuddy đang suy nghĩ...
Trả lời trực tiếp

TravelBuddy: Bạn muốn đặt khách sạn ở thành phố nào? Bạn dự định ở bao nhiêu đêm và tổng ngân sách khoảng bao nhiêu để mình gợi ý phù hợp hơn?
```

## Test 5: Guardrail / Refusal
**Console Log**
```text
Bạn: Giải giúp tôi bài tập lập trình Python về linked list

TravelBuddy đang suy nghĩ...
Trả lời trực tiếp

TravelBuddy: Xin lỗi, nhưng tôi không thể giúp bạn với bài tập lập trình. Tuy nhiên, nếu bạn cần thông tin về du lịch, chuyến bay, khách sạn hoặc ngân sách cho chuyến đi, tôi rất sẵn lòng hỗ trợ! Bạn có kế hoạch đi đâu không?
```
