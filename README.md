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
| Confidence gate | tidak dipakai eksekusi | **confidence < 65 ditolak** (K1 fix) |

Bugfix yang ikut masuk (dari audit independen):
- **C1**: `apply_dashboard_overrides` sekarang meng-int-kan knob integer
  (`sr_zone_lookback_4h` float sebelumnya bikin slice TypeError → veto jatuh ke "hold").
- **K1**: `CONFIDENCE_THRESHOLD_MODERATE` (65) kini benar-benar dipakai sebagai gate
  eksekusi, bukan cuma tiebreaker ranking.

## Status

- Test: **729 passed** (`pytest`, ~52 dtk).
- **Paper-test SEDANG BERJALAN** sejak 2026-10-19 16:28 WIB (dijalankan manual user). Evaluasi setelah ≥1 minggu (~2026-10-26).
  **Jangan jalankan `--live` sebelum paper-test selesai dan dievaluasi.**

## Menjalankan

### Cara cepat: `binance-flex` (workflow launcher)

Satu perintah untuk satu workflow lengkap:

```bash
./binance-flex -m 100 -l 10 isolated paper -a 20
```

Artinya: paper trading, margin $100/entry, leverage 10x, ISOLATED,
auto-TP saat profit +20% dari margin, loop jalan terus.

```
=== BINANCE-FLEX [PAPER] ===
  margin   : $100.00/entry
  leverage : 10x
  mode     : ISOLATED
  auto TP  : +20% dari margin
  jalan    : loop terus
```

| Argumen | Arti | Default |
|---|---|---|
| `-m, --margin` | margin USDT per entry | `1.0` |
| `-l, --leverage` | leverage | `10` |
| `-a, --auto-tp` | auto-TP saat profit +% dari margin (`0` = mati) | `20.0` |
| `isolated` / `cross` | margin mode | `isolated` |
| `paper` / `testnet` / `live` | mode jalan | `paper` |
| `--once` | sekali scan lalu berhenti | (loop) |
| `--dry-run` | tampilkan konfigurasi tanpa menjalankan | - |
| `--yes` | lewati konfirmasi mode live | - |

Contoh lain:

```bash
./binance-flex paper                              # default: $1, 10x, isolated, TP 20%
./binance-flex -m 5 -l 5 cross testnet --once     # testnet sekali scan
./binance-flex -m 100 -l 10 isolated paper -a 20 --dry-run  # cek dulu
./binance-flex live --yes                         # LIVE (butuh BINANCE_LIVE_KEY/SECRET)
```

Yang dilakukan launcher:
1. Menulis `profit_take_pct` (-a) dan `margin_mode` ke `dashboard_settings.json`
   section mode yang dipilih — jalur resmi, executor membaca tiap cycle dan
   dashboard ikut menampilkan. Validasi via `dashboard.validate_settings`.
2. Membangun perintah `run_executor.py` yang sesuai lalu exec ke sana.

Keamanan:
- `-m`/`-l` adalah flag TEST ONLY milik engine: **ditolak untuk live**
  (engine pun menolaknya). Risk live hanya via dashboard (knob tighten-only).
- Mode live menampilkan banner merah dan wajib konfirmasi
  (ketik `LIVE`, atau `--yes`).

### Cara manual


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

Monitor trading kit (gaya azzx-fast-scalping, read-only):
```bash
.venv/bin/python kit.py              # ringkasan paper: saldo, posisi terbuka,
                                     # trade yang ditutup hari ini + win rate
.venv/bin/python kit.py --mode live  # baca state live
```
Contoh baris posisi:
```
tgl                 | symbol    | side | entry     | margin | lev | TP        | SL
2026-10-19 16:35:01 | BTCUSDT   | LONG | 82,800.50 | $1.00  | 10x | 84,456.50 | 81,500.00
```
Setiap posisi dibuka/ditutup, executor juga mencetak satu baris kit berwarna
di terminal (hijau = LONG/profit, merah = SHORT/loss), contoh:
```
2026-10-19 16:35:01 | OPEN LONG BTCUSDT @ 82,800.50 | margin $1.00 | lev 10x | TP 84,456.50 | SL 81,500.00
2026-10-19 17:02:44 | CLOSE LONG BTCUSDT | entry 82,800.50 | exit 84,460.00 | PnL +$0.21 [TP]
```

## Struktur

- `config.py` — semua knob (preset biasa/sedang/ketat + adaptif)
- `signal_engine.py` — pipeline sinyal 11 tahap + confidence gate
- `executor.py` — eksekusi order, write-ahead + tri-state anti double-entry
- `vetoes.py`, `quality_deltas.py` — 6 veto + delta kualitas adaptif
- `dashboard.py` — web UI monitoring & kill switch
- `trade_kit.py` — formatter baris kit gaya scalping (dipakai executor)
- `kit.py` — monitor terminal read-only (saldo, posisi, trade hari ini)
- `binance-flex` — workflow launcher satu perintah (+ `tests/test_binance_flex.py`: 19 test)
- `tests/` — 710 test

## Peringatan

Trading futures berisiko tinggi. Bot ini eksperimental: filter longgar = lebih banyak
sinyal = lebih banyak eksposur ke false signal. Mulai dari paper, evaluasi win rate
dan ekspektasi per trade, baru pertimbangkan live dengan modal yang siap hilang.
Bukan saran finansial.
