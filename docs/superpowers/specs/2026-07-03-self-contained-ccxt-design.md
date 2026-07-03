# Self-Contained CCXT Skill Design

## Mục tiêu

Đóng gói skill `crypto-market-toolkit` theo kiểu self-contained để AI agent có thể chạy ngay mà không cần cài `ccxt` hay cài package trước mỗi lần chạy trong môi trường sandbox tạm thời.

## Quyết định thiết kế

Chọn bundle full `ccxt` vào repo thay vì phụ thuộc vào `pip install` lúc runtime.

## Lý do chọn full bundle

- Agent runtime có thể không cài dependency trước khi chạy
- Sandbox có thể là ephemeral, làm mất môi trường đã cài ở lần chạy trước
- `ccxt` có nhiều module nội bộ liên quan nhau; bundle tối thiểu dễ gây thiếu module khi đổi sàn hoặc mở rộng tính năng
- Full bundle giúp runtime ổn định hơn và giảm phụ thuộc vào network

## Kiến trúc sau thay đổi

### Vendor dependency

Thêm thư mục vendor trong repo, ví dụ:

- `/workspace/vendor/ccxt/`

Thư mục này chứa mã nguồn `ccxt` cần cho runtime.

### Python runtime

Giữ nguyên code trong:

- `/workspace/src/crypto_market_toolkit/`

Không thay đổi API chính của toolkit.

### Wrapper script

Wrapper root:

- `/workspace/scripts/run-tool.sh`

sẽ export `PYTHONPATH` theo thứ tự ưu tiên:

- `/workspace/vendor`
- `/workspace/src`

để Python import được cả `ccxt` vendor và package toolkit mà không cần cài đặt.

## Tài liệu skill

### SKILL.md

`/workspace/SKILL.md` cần được cập nhật để:

- bỏ yêu cầu cài dependency trước lần dùng đầu tiên
- mô tả skill là self-contained
- hướng dẫn agent ưu tiên dùng wrapper root `/workspace/scripts/run-tool.sh`

### README

`/workspace/README.md` cần phản ánh runtime self-contained:

- không yêu cầu `pip install` như điều kiện bắt buộc để agent chạy skill
- có thể vẫn giữ phần cài package như lựa chọn cho developer local, nhưng tách rõ với agent runtime

## Phạm vi thay đổi

### Cần làm

- thêm vendor `ccxt` vào repo
- cập nhật wrapper root để dùng `vendor` + `src`
- cập nhật tài liệu skill và README
- bổ sung kiểm tra để xác nhận wrapper chạy được khi không có package cài sẵn trong môi trường

### Không làm trong scope này

- không thêm trading/private API
- không thay đổi schema output hiện tại
- không thay đổi danh sách tool hay hành vi business logic của market data / indicators / scanners

## Kiểm thử

Sau khi triển khai cần xác minh:

- wrapper chạy được từ `cwd` bất kỳ:
  - `/workspace/scripts/run-tool.sh --help`
- import `ccxt` thành công thông qua vendor path
- `pytest` tiếp tục pass
- `python -m compileall src tests` tiếp tục pass

## Tiêu chí hoàn thành

- agent không cần `pip install` để dùng skill
- runtime không phụ thuộc vào môi trường cài package bên ngoài
- wrapper root hoạt động ổn định trong sandbox ephemeral
- tài liệu không còn mô tả `pip install` là điều kiện bắt buộc cho agent runtime
