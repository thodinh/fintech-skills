# Self-Contained Finance Market Skill Design

## Mục tiêu

Đóng gói skill theo kiểu self-contained và đồng thời đổi tên đầy đủ sang branding mới để AI agent có thể chạy ngay mà không cần cài `ccxt` hay cài package trước mỗi lần chạy trong môi trường sandbox tạm thời.

## Quyết định thiết kế

Chọn hai quyết định cùng lúc:

- bundle full `ccxt` vào repo thay vì phụ thuộc vào `pip install` lúc runtime
- đổi tên đầy đủ sang:
  - skill code: `finance-market-skills`
  - display name: `Finance Market`
  - Python package: `finance_market_skills`
  - console script: `finance-market-skills`

## Lý do chọn full bundle

- Agent runtime có thể không cài dependency trước khi chạy
- Sandbox có thể là ephemeral, làm mất môi trường đã cài ở lần chạy trước
- `ccxt` có nhiều module nội bộ liên quan nhau; bundle tối thiểu dễ gây thiếu module khi đổi sàn hoặc mở rộng tính năng
- Full bundle giúp runtime ổn định hơn và giảm phụ thuộc vào network

## Kiến trúc sau thay đổi

### Naming

Sau thay đổi, hệ thống dùng naming mới nhất quán:

- `SKILL.md`
  - `name: finance-market-skills`
- `agents/openai.yaml`
  - `display_name: Finance Market`
- package Python:
  - `/workspace/src/finance_market_skills/`
- CLI:
  - `finance-market-skills`
- module entrypoint:
  - `python -m finance_market_skills.cli`

Không giữ tên code cũ như nguồn sự thật chính.

### Vendor dependency

Thêm thư mục vendor trong repo, ví dụ:

- `/workspace/vendor/ccxt/`

Thư mục này chứa mã nguồn `ccxt` cần cho runtime.

### Python runtime

Code runtime sẽ được đổi tên package sang:

- `/workspace/src/finance_market_skills/`

API chính của toolkit được giữ nguyên về hành vi, nhưng đổi namespace/import sang package mới.

### Wrapper script

Wrapper root:

- `/workspace/scripts/run-tool.sh`

sẽ export `PYTHONPATH` theo thứ tự ưu tiên:

- `/workspace/vendor`
- `/workspace/src`

để Python import được cả `ccxt` vendor và package toolkit mới mà không cần cài đặt.

## Tài liệu skill

### SKILL.md

`/workspace/SKILL.md` cần được cập nhật để:

- bỏ yêu cầu cài dependency trước lần dùng đầu tiên
- mô tả skill là self-contained
- đổi `name` sang `finance-market-skills`
- hướng dẫn agent ưu tiên dùng wrapper root `/workspace/scripts/run-tool.sh`

### README

`/workspace/README.md` cần phản ánh runtime self-contained:

- không yêu cầu `pip install` như điều kiện bắt buộc để agent chạy skill
- có thể vẫn giữ phần cài package như lựa chọn cho developer local, nhưng tách rõ với agent runtime
- đổi tên hiển thị và ví dụ CLI sang `Finance Market` / `finance-market-skills`

## Phạm vi thay đổi

### Cần làm

- thêm vendor `ccxt` vào repo
- đổi tên package Python từ `finance_market_skills` sang `finance_market_skills`
- đổi console script sang `finance-market-skills`
- cập nhật wrapper root để dùng `vendor` + `src`
- cập nhật `SKILL.md`, `README.md`, metadata agent, import và test theo naming mới
- bổ sung kiểm tra để xác nhận wrapper chạy được khi không có package cài sẵn trong môi trường

### Không làm trong scope này

- không thêm trading/private API
- không thay đổi schema output hiện tại
- không thay đổi danh sách tool hay hành vi business logic của market data / indicators / scanners
- không giữ alias cũ như hướng vận hành chính, trừ khi bổ sung riêng ở bước triển khai

## Kiểm thử

Sau khi triển khai cần xác minh:

- wrapper chạy được từ `cwd` bất kỳ:
  - `/workspace/scripts/run-tool.sh --help`
- import `ccxt` thành công thông qua vendor path
- import package mới thành công:
  - `python -c "import finance_market_skills"`
- `pytest` tiếp tục pass
- `python -m compileall src tests` tiếp tục pass

## Tiêu chí hoàn thành

- agent không cần `pip install` để dùng skill
- runtime không phụ thuộc vào môi trường cài package bên ngoài
- wrapper root hoạt động ổn định trong sandbox ephemeral
- tài liệu không còn mô tả `pip install` là điều kiện bắt buộc cho agent runtime
- naming mới `finance-market-skills` / `Finance Market` / `finance_market_skills` được dùng nhất quán trong skill, package, CLI, docs và tests
