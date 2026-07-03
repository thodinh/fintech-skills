# Finance Market (ccxt) — Design Spec

## 1) Mục tiêu

Xây dựng Skill Python cung cấp bộ công cụ tài chính mạnh cho AI Agent dựa trên market data công khai từ CEX qua thư viện `ccxt`, tập trung vào:

- Lấy giá/ticker chuẩn hoá
- Lấy OHLCV (nến) đa timeframe
- Lấy order book và trades gần nhất
- Tính các chỉ báo kỹ thuật phổ biến từ OHLCV
- Quét thị trường (top movers, volume spikes, volatility rank, breakout rules)

Thiết kế ưu tiên AI-agent friendly: output tự mô tả, có `summary`/`highlights` dùng ngay, đồng thời vẫn cung cấp dữ liệu đủ sâu để lập luận và kiểm chứng.

## 2) Non-goals (ngoài phạm vi)

- Không hỗ trợ trading (đặt/hủy lệnh), không dùng API key/secret
- Không hỗ trợ dữ liệu on-chain, DEX, hoặc price oracle
- Không tối ưu cho HFT; chỉ nhắm tới phân tích/giám sát theo phút–giờ–ngày

## 3) Phạm vi sàn và thị trường

### 3.1 Sàn mặc định

- Binance
- Bybit
- OKX

### 3.2 Loại thị trường

- `market_type`: `"spot"` mặc định
- Cho phép `"swap"`/`"future"` khi ccxt exchange hỗ trợ, nhưng vẫn chỉ market data

## 4) Kiến trúc tổng thể

### 4.1 Các module chính (Python)

- `exchanges/registry.py`: map tên sàn → factory tạo instance ccxt + cấu hình chuẩn
- `exchanges/client.py`: wrapper thống nhất:
  - load markets
  - normalize symbol
  - call ccxt với retry/timeout/rate limit
- `cache/memory_cache.py`: cache TTL in-memory theo key (exchange, method, params)
- `schemas/response.py`: chuẩn response + helper tạo `summary`/`highlights`
- `market_data/*`:
  - `ticker.py`
  - `ohlcv.py`
  - `orderbook.py`
  - `trades.py`
- `indicators/*`:
  - `moving_averages.py` (SMA/EMA)
  - `rsi.py`
  - `macd.py`
  - `bbands.py`
  - `atr.py`
  - `vwap.py`
  - `compute.py` (orchestrator)
- `scanners/*`:
  - `top_movers.py`
  - `volume_spikes.py`
  - `volatility_rank.py`
  - `breakouts.py`

### 4.2 Data flow

1. Tool nhận `exchange`, `symbol`, `market_type`, và params
2. Tạo ccxt client (hoặc reuse) + load markets (cache)
3. Gọi method ccxt phù hợp (có timeout + retry)
4. Normalize data → chuẩn schema
5. Tính `stats` (tuỳ tool)
6. Tạo `summary` + `highlights`
7. Trả response `ok=true`

Nếu lỗi:

- Classify lỗi (invalid exchange/symbol, unsupported, rate limit, network timeout)
- Trả `ok=false` + `error` (không quăng raw exception ra ngoài)

## 5) Chuẩn response (AI-agent friendly)

### 5.1 Envelope chung

Mọi tool trả object với các field sau:

- `ok`: boolean
- `summary`: string (1–3 câu, giàu số liệu, không mơ hồ)
- `highlights`: string[] (3–6 item, dạng `key=value`, dễ trích dẫn)
- `query`: object
  - `exchange`: string
  - `symbol`: string | null
  - `market_type`: `"spot" | "swap" | "future"`
  - `timeframe`: string | null
  - `since_ms`: number | null
  - `limit`: number | null
  - `params`: object
- `ts_ms`: number (UTC, milliseconds)
- `iso_time`: string (UTC ISO-8601)
- `data`: object (payload chính, tuỳ tool)
- `stats`: object (thống kê bổ trợ, tuỳ tool)
- `meta`: object
  - `source`: `"ccxt"`
  - `exchange_id`: string (id trong ccxt)
  - `rate_limit_enabled`: boolean
  - `timeout_ms`: number
  - `cache`: `{ hit: boolean, ttl_s: number | null }`
  - `units`: `{ price: "quote", volume: "base", ts: "ms" }`
  - `precision`: `{ price_decimals: number | null, amount_decimals: number | null }`
  - `warnings`: string[]
- `error`: object | null
  - `code`: string
  - `message`: string
  - `context`: object
    - `method`: string | null
    - `retryable`: boolean

### 5.2 Rút gọn series để tối ưu agent

Với dữ liệu dạng chuỗi thời gian:

- Mặc định trả `series_tail` (ví dụ 120 điểm gần nhất)
- Nếu user/agent yêu cầu, có thể bật `full_series=true` để trả full trong giới hạn `limit`

Quy ước:

- `data.series_tail`: array
- `data.series_full_truncated`: boolean
- `data.series_tail_size`: number

## 6) Danh sách tool (API cấp Skill)

### 6.1 Price & Ticker

#### `get_price(exchange, symbol, market_type="spot")`

- `data`: `{ last: number, ts_ms: number }`
- `stats`: `{ bid: number | null, ask: number | null, spread_abs: number | null, spread_pct: number | null }`

#### `get_ticker(exchange, symbol, market_type="spot")`

- `data`:
  - `last`, `bid`, `ask`
  - `open`, `high`, `low`
  - `base_volume`, `quote_volume`
  - `change`, `percentage`
  - `ts_ms`
- `stats`:
  - `spread_abs`, `spread_pct`
  - `range_pct` (high-low / mid)

### 6.2 OHLCV

#### `get_ohlcv(exchange, symbol, timeframe="1m", limit=500, since_ms=null, market_type="spot", full_series=false, series_tail_size=120)`

- `data`:
  - `ohlcv`: array (full hoặc tail tuỳ cấu hình)
  - `ohlcv_tail`: array (luôn có)
  - `last_candle`: `[ts_ms, o, h, l, c, v] | null`
- `stats`:
  - `return_pct`: theo cửa sổ trả về
  - `volatility`: std log-return (tail)
  - `avg_range_pct`, `avg_volume`

### 6.3 Order Book & Trades

#### `get_orderbook(exchange, symbol, limit=100, market_type="spot")`

- `data`:
  - `bids`: `[[price, amount], ...]`
  - `asks`: `[[price, amount], ...]`
  - `ts_ms`
- `stats`:
  - `best_bid`, `best_ask`, `spread_abs`, `spread_pct`
  - `depth_bid_notional`, `depth_ask_notional` (tổng quote notional theo top levels)

#### `get_trades(exchange, symbol, limit=200, since_ms=null, market_type="spot")`

- `data`:
  - `trades`: array normalized `{ ts_ms, price, amount, side }`
  - `ts_ms`
- `stats`:
  - `buy_volume`, `sell_volume` (base)
  - `buy_sell_ratio`

### 6.4 Indicators

#### `compute_indicators(exchange, symbol, timeframe="1h", limit=500, since_ms=null, market_type="spot", indicators=[...], indicator_params={}, full_series=false, series_tail_size=120)`

- Orchestrator:
  - lấy OHLCV
  - tính indicator
  - trả series tail + `last` + `signal`

Supported indicators (MVP):

- `sma(period)`
- `ema(period)`
- `rsi(period=14)`
- `macd(fast=12, slow=26, signal=9)`
- `bbands(period=20, stddev=2)`
- `atr(period=14)`
- `vwap(window=null | number)` (mặc định dùng toàn tail nếu window null)

`data`:

- `ohlcv_tail`
- `indicators`: map
  - `params`
  - `series_tail`
  - `last`
  - `signal` (khi phù hợp)

`stats`:

- `close_last`
- `return_pct_tail`
- `trend_slope` (slope đơn giản của close tail)

### 6.5 Scanners

#### `scan_top_movers(exchange, quote="USDT", market_type="spot", top_n=20, min_quote_volume=null)`

- Universe: load markets, lọc symbol có quote đúng (mặc định USDT)
- Dùng ticker để xếp hạng theo `percentage` (24h)
- `data.results`: `{ symbol, metrics, reason }[]`

#### `scan_volume_spikes(exchange, quote="USDT", timeframe="1h", lookback=48, spike_factor=3.0, top_n=20)`

- Lấy OHLCV tail cho mỗi symbol
- Tính volume hiện tại / volume trung bình lookback

#### `scan_volatility_rank(exchange, quote="USDT", timeframe="1h", lookback=120, top_n=20)`

- Dùng std log-return để xếp hạng biến động

#### `scan_breakouts(exchange, quote="USDT", timeframe="1h", rule="close>bb_upper", top_n=20, indicator_params={...})`

- Lấy OHLCV + tính indicator cần thiết
- Rule engine tối thiểu hỗ trợ:
  - `close>bb_upper`
  - `close<bb_lower`
  - `rsi>70` / `rsi<30`
  - `macd_cross_up` / `macd_cross_down`

## 7) Cache, rate limit, retry

### 7.1 Rate limit

- Bật `enableRateLimit` trong ccxt client
- Không tự song song hoá theo symbol ở MVP; scan theo batch tuần tự hoặc giới hạn concurrency thấp có kiểm soát

### 7.2 Cache TTL đề xuất (in-memory)

- `load_markets`: 30 phút
- `fetch_ticker`: 2–5 giây
- `fetch_ohlcv`:
  - timeframe <= 5m: 10–20 giây
  - timeframe >= 15m: 30–60 giây
- `fetch_order_book`: 1–2 giây
- `fetch_trades`: 2–5 giây

### 7.3 Retry/timeout

- Timeout mặc định: 10–15 giây (config)
- Retry 2 lần với exponential backoff cho lỗi network/timeout
- Không retry với lỗi “unsupported” hoặc “bad symbol”

## 8) Normalization & symbol handling

- `exchange` nhận dạng tên thân thiện (`"binance"`, `"bybit"`, `"okx"`)
- `symbol` theo format ccxt (`"BTC/USDT"`) sau khi normalize
- Nếu user đưa `"BTCUSDT"`, áp dụng mapping heuristics:
  - detect quote theo whitelist (`USDT`, `USDC`, `BTC`, `ETH`)
  - chuyển về `"BTC/USDT"`
- Trả warning nếu heuristic được dùng

## 9) Error model

`error.code` (ví dụ):

- `INVALID_EXCHANGE`
- `INVALID_SYMBOL`
- `UNSUPPORTED_MARKET_TYPE`
- `UNSUPPORTED_OPERATION`
- `RATE_LIMIT`
- `NETWORK_ERROR`
- `TIMEOUT`
- `UPSTREAM_ERROR`

`error.context` chứa các field giúp agent xử lý: exchange, symbol, method, retryable boolean.

## 10) Kiểm thử và xác minh

### 10.1 Unit tests (offline)

- Indicator calculations:
  - RSI, EMA/SMA, MACD, BBands, ATR, VWAP trên OHLCV fixtures
- Response schema:
  - đảm bảo có `summary/highlights/meta.units` và kiểu dữ liệu JSON-friendly

### 10.2 Integration tests (online, tuỳ chọn)

- Smoke test gọi `fetch_ticker` và `fetch_ohlcv` cho 1–2 symbol phổ biến trên Binance spot
- Cho phép tắt bằng env flag để CI không phụ thuộc mạng

## 11) Tiêu chí “AI-agent friendly”

- Mọi tool đều có `summary` và `highlights` để trả lời ngay
- `query` + `meta` giúp agent trích nguồn và tránh “bịa”
- Series mặc định rút gọn (`series_tail`) để tránh bloat ngữ cảnh
- Lỗi trả chuẩn hoá, có `retryable` trong context để agent quyết định thử lại hay đổi tham số
