# Oreka Shipping Provider Simulator

GUI giả lập phản hồi của hãng vận chuyển (J&T Express, Shopee Express) để test cơ chế
đồng bộ trạng thái vận đơn của `shipping-api` mà không cần hãng gửi gì.

## Chạy

Chỉ dùng thư viện chuẩn của Python, không cần cài gì:

```bash
make dev
```

Các lệnh khác:

| Lệnh | Việc |
|---|---|
| `make` | liệt kê lệnh |
| `make dev` | chạy app |
| `make check` | kiểm tra python + tkinter |
| `make build-macos` | đóng gói `.app` + `.zip` vào `dist/` (tạo `.venv`, cài pyinstaller) |
| `make clean` | xoá `build/`, `dist/` |
| `make distclean` | xoá cả `.venv` |

Bản đóng gói để đưa cho QA không cài Python:

- macOS: `make build-macos` → `dist/OrekaShippingProviderSimulator-macos.zip`
- Windows: chạy `build_windows.bat` **trên máy Windows** → `dist\OrekaShippingProviderSimulator.exe`

PyInstaller không cross-compile, nên `.exe` phải build từ Windows. Không có máy Windows thì
dùng `.github/workflows/build.yml` (GitHub Actions dựng cả hai bản, tải về ở tab Artifacts).

macOS dùng python từ python.org hoặc homebrew đều có sẵn tkinter. Nếu báo thiếu tkinter:
`brew install python-tk`.

## Cấu hình

Gateway URL và secret nằm trong `config.py`, không còn nhập trên giao diện. Bản mặc định
trỏ vào môi trường test:

| Môi trường | `OREKA_SIM_ENV` | Gateway URL |
|---|---|---|
| Test (mặc định) | `test` | `https://dev.oreka.vn/` |
| Local | `local` | `http://localhost:8888` |

Đổi môi trường khi chạy từ source: `OREKA_SIM_ENV=local make dev`. Bản đóng gói luôn dùng
môi trường test; muốn bản khác thì sửa `DEFAULT_ENVIRONMENT` trong `config.py` rồi build lại.

Backend chỉ nhận lệnh khi `config.trackingSimulation.enabled = true`. Ở production luôn tắt.

## Cách dùng

1. Nhập mã đơn hàng — `Order.shortId`, 14 ký tự, ví dụ `NEV16PWGFN2GNF` → **Tải**.
   Không phải mã đơn vận (`SP-...`) cũng không phải mã vận đơn của hãng.
2. Chọn đơn vận trong bảng. Một đơn hàng có thể có nhiều đơn vận (đơn hoàn, đơn ship lại).

### Tab "Giả lập API hãng" — test cơ chế quét

Bên trái là những trạng thái hệ thống **đang có**. Bên phải là những gì hãng **sẽ trả về**,
mặc định copy từ bên trái.

Để giả lập một webhook bị mất: thêm trạng thái mới vào bên phải (cột ghi chú hiện `MỚI`),
bấm **Lưu kịch bản**. Xong việc của phần mềm này.

Hệ thống tự quét theo lịch của nó. Sau đó bấm **Tải** để xem kết quả:

- Trạng thái mới phải xuất hiện bên trái với nguồn `tracking_sync`.
- Tải lại lần nữa cũng chỉ có đúng một bản ghi cho trạng thái đó — không nhân đôi.
- Trạng thái có nhãn `SHIPPED` / `DELIVERED` sẽ chuyển trạng thái đơn hàng thật bên order-api.
- Trạng thái có nhãn `KẾT THÚC` làm đơn rớt khỏi hàng đợi quét vĩnh viễn.

Kịch bản nằm trong Redis, TTL 24 giờ. **Xoá kịch bản khỏi Redis** khi test xong — nếu quên,
đơn đó sẽ không gọi hãng thật cho tới khi hết hạn.

### Tab "Giả lập webhook"

Chọn trạng thái, bấm **Gửi webhook**. Payload và chữ ký do `shipping-api` dựng, GUI chỉ
chuyển tiếp tới đúng route webhook thật của gateway — nên tầng xác thực chữ ký cũng được test.

Gửi lại cùng trạng thái + thời điểm phải không tạo thêm bản ghi nào.

## Files

- `app.py` — giao diện
- `api.py` — gọi HTTP tới federation-gateway
- `config.py` — gateway URL + secret theo môi trường
- `providers.py` — bảng mã trạng thái của từng hãng
- `build_windows.bat` — script đóng gói `.exe`, chạy trên Windows
