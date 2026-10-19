# binance-futures-flex-bot

Bot auto-trading Binance Futures dengan **filter sinyal yang lebih longgar** dibanding
[`binance-futures-strict-bot`](https://github.com/aziz-sudrajat/binance-futures-strict-bot).
Basis kode: strict-bot commit `01cf28d`, dengan hanya perubahan konfigurasi + 2 bugfix.

## Kenapa ada bot ini?

Strict-bot adalah *trending-market-only machine*: dalam scan 491 simbol, 0 sinyal lolos
(V21 displacement ≥ 1,5 %/24 jam, MTF 5 timeframe unanimous, pola candle wajib, Q ≥ 70).
Di market sideways, engine-nya diam total berhari-hari.

Insight: dengan margin $1 × leverage 10x, target profit +20 % margin ($0,20) **cuma butuh
gerakan harga ~2 %** (fee PP ~$0,01). Engine tidak perlu menunggu trend sempurna —
cukup probabilitas gerakan 2 %. Metrik sukses bot ini: **win rate > 50–60 % dan
ekspektasi per trade positif**, bukan jumlah sinyal.

## Perbedaan vs strict-bot

| Aspek | strict-bot | flex-bot |
|---|---|---|
| Arah | long + short (live) | long + short |
| Quality threshold | 70 | **60** (adaptif 50/70) |
| MTF cascade | 5 TF unanimous | **LEAN** |
| MTF require 1d | hard gate | **off** |
| Freshness | ketat | **1,0 %** |
| V21 displacement | ≥ 1,5 %/24 jam | **≥ 0,8 %/24 jam** |
| SR zone ATR mult | 2,0 | **1,5** |
| News/liq/whale review (preset ketat) | on | **off** |
| Preset sedang quality | 60 | **55** |
| Confidence gate | tidak dipakai eksekusi | **≥ 65 ditolak** (K1 fix) |

Bugfix yang ikut masuk (dari audit independen):
- **C1**: `apply_dashboard_overrides` sekarang meng-int-kan knob integer
  (`sr_zone_lookback_4h` float sebelumnya bikin slice TypeError → veto jatuh ke "hold").
- **K1**: `CONFIDENCE_THRESHOLD_MODERATE` (65) kini benar-benar dipakai sebagai gate
  eksekusi, bukan cuma tiebreaker ranking.

## Status

- Test: **700 passed, 1 skipped** (`pytest`, ~59 dtk).
- **Paper-test WAJIB minimal 1 minggu sebelum live.** Jangan jalankan `--live`
  sebelum paper-test selesai dan dievaluasi.

## Menjalankan

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Paper (default aman)
python run_executor.py --paper --loop

# Live — HANYA setelah paper-test 1 minggu, keys dari env:
# BINANCE_LIVE_KEY / BINANCE_LIVE_SECRET
python run_executor.py --live --loop
```

Setting live yang dipakai: ISOLATED, $1/entry, leverage 10x fixed, profit-take +20 %
dari margin, SL ATR 1,5–3,0x. Jangan ubah risk tanpa paham konsekuensinya.

Dashboard (opsional): `python dashboard.py` → http://localhost:8080
(toggle auto-trade, knob hanya bisa *mengetatkan*, tidak melonggarkan).

## Struktur

- `config.py` — semua knob (preset biasa/sedang/ketat + adaptif)
- `signal_engine.py` — pipeline sinyal 11 tahap + confidence gate
- `executor.py` — eksekusi order, write-ahead + tri-state anti double-entry
- `vetoes.py`, `quality_deltas.py` — 6 veto + delta kualitas adaptif
- `dashboard.py` — web UI monitoring & kill switch
- `tests/` — 700 test

## Peringatan

Trading futures berisiko tinggi. Bot ini eksperimental: filter longgar = lebih banyak
sinyal = lebih banyak eksposur ke false signal. Mulai dari paper, evaluasi win rate
dan ekspektasi per trade, baru pertimbangkan live dengan modal yang siap hilang.
Bukan saran finansial.
