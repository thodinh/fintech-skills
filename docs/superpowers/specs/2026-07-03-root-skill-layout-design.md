# Root Skill Layout Design

## Mục tiêu

Điều chỉnh cấu trúc project để agent chỉ cần đọc `SKILL.md` ở root project là có thể nhận diện và sử dụng skill `crypto-market-toolkit`.

## Quyết định thiết kế

Chọn phương án A:

- Đưa `SKILL.md` chính lên root project: `/workspace/SKILL.md`
- Đưa metadata agent lên root-level assets:
  - `/workspace/agents/openai.yaml`
  - `/workspace/scripts/run-tool.sh`
- Giữ nguyên package Python hiện tại trong `src/crypto_market_toolkit/`
- Cập nhật toàn bộ tài liệu và đường dẫn wrapper sang layout mới ở root

## Kiến trúc sau thay đổi

### Root-level skill entrypoint

Root project sẽ có:

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/run-tool.sh`

`SKILL.md` là nguồn sự thật duy nhất cho agent discovery.

### Python runtime

Phần thực thi vẫn giữ nguyên:

- console script `crypto-market-toolkit`
- module entrypoint `python -m crypto_market_toolkit.cli`

Wrapper `scripts/run-tool.sh` chỉ có vai trò export `PYTHONPATH` và gọi CLI.

## Di chuyển và chuẩn hoá

### File cần tạo/cập nhật

- Tạo `/workspace/SKILL.md` từ nội dung skill hiện có
- Tạo `/workspace/agents/openai.yaml`
- Tạo `/workspace/scripts/run-tool.sh`
- Cập nhật `README.md` để trỏ tới root layout mới

### File cũ cần ngừng dùng

Các file dưới `skills/crypto-market-toolkit/` không còn là entrypoint chính sau thay đổi này.

Để tránh hai nguồn sự thật, triển khai nên chọn một trong hai:

- xóa thư mục `skills/crypto-market-toolkit/`
- hoặc giữ tạm nhưng ghi rõ deprecated và không còn được tham chiếu ở README

Khuyến nghị: xóa sau khi root layout đã chạy ổn.

## Error handling

- Nếu user chạy wrapper cũ trong `skills/crypto-market-toolkit/scripts/run-tool.sh`, tài liệu không còn tham chiếu tới path này
- Wrapper mới ở root phải tiếp tục hoạt động trong môi trường local repo mà không cần thay đổi code package

## Kiểm thử

Sau khi đổi cấu trúc cần xác minh:

- `pytest`
- `python -m compileall src tests`
- `crypto-market-toolkit --help`
- `./scripts/run-tool.sh --help`

## Tiêu chí hoàn thành

- Agent discovery dựa trên `/workspace/SKILL.md`
- Không còn tài liệu chính nào trỏ về `skills/crypto-market-toolkit/`
- Root wrapper và CLI đều chạy được
- Không tạo thêm logic runtime mới ngoài việc đổi layout và path
