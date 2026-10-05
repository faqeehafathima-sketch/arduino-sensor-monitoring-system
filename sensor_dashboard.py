"""
╔══════════════════════════════════════════════════════════════╗
║     🌡️  ARDUINO SENSOR MONITORING SYSTEM  v2.0              ║
║     Real-Time Sensor Data Acquisition & Analytics Dashboard   ║
║     Built with Python | Seaborn | Matplotlib | Serial        ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
  1. Connect Arduino (with DHT11 code uploaded)
  2. Install dependencies:
       pip install pyserial matplotlib seaborn pandas numpy scipy
  3. Run: python sensor_dashboard.py
  4. Select your COM port when prompted

DEMO MODE:
  Run without Arduino for expo simulation:
       python sensor_dashboard.py --demo

The source is organized for readability and reliability while preserving the
existing dashboard layout, styling, labels, and calculations.
"""

import sys
import os
import time
import threading
import argparse
import math
import random
from datetime import datetime
from collections import deque

import numpy as np

# Fix emoji/glyph warnings on Windows
import matplotlib as mpl
mpl.rcParams['axes.unicode_minus'] = False
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
import seaborn as sns
from scipy.ndimage import gaussian_filter1d
from scipy.stats import linregress
from sklearn.ensemble import IsolationForest

# ─────────────────────────────────────────────
#  GLOBAL CONFIGURATION
# ─────────────────────────────────────────────
BAUD_RATE       = 9600
MAX_POINTS      = 120          # keep last 120 readings on chart
UPDATE_INTERVAL = 2000         # ms between plot refreshes
DATA_LOG_FILE   = "sensor_log.csv"

# ── DARK THEME PALETTE ──────────────────────
BG_COLOR        = "#0D1117"    # GitHub dark background
PANEL_COLOR     = "#161B22"    # panel background
BORDER_COLOR    = "#30363D"    # subtle borders
TEXT_COLOR      = "#E6EDF3"    # primary text
MUTED_COLOR     = "#8B949E"    # muted / secondary text

TEMP_COLOR      = "#FF6B6B"    # coral red  – temperature
HUM_COLOR       = "#4ECDC4"    # teal       – humidity
FEEL_COLOR      = "#FFE66D"    # gold       – heat index
AVG_COLOR       = "#A78BFA"    # violet     – moving average
ALERT_COLOR     = "#FF4444"    # bright red – alert

GRADIENT_TEMP   = ["#FF6B6B", "#FF8E53"]
GRADIENT_HUM    = ["#4ECDC4", "#44A3AA"]

# ── THRESHOLDS (customize as needed) ────────
TEMP_HIGH       = 35.0   # °C
TEMP_LOW        = 15.0   # °C
HUM_HIGH        = 80.0   # %
HUM_LOW         = 20.0   # %

# ─────────────────────────────────────────────
#  DATA STORE
# ─────────────────────────────────────────────
timestamps   = deque(maxlen=MAX_POINTS)
temperatures = deque(maxlen=MAX_POINTS)
humidities   = deque(maxlen=MAX_POINTS)
heat_indices = deque(maxlen=MAX_POINTS)
reading_count = 0
start_time    = time.time()
alerts        = deque(maxlen=30)

lock = threading.Lock()


# ─────────────────────────────────────────────
#  HEAT INDEX FORMULA  (feels-like temperature)
# ─────────────────────────────────────────────
def calc_heat_index(T, RH):
    """Steadman's heat index (°C)."""
    if T < 27 or RH < 40:
        return T
    hi = (-8.78469475556
          + 1.61139411   * T
          + 2.33854883889 * RH
          - 0.14611605   * T  * RH
          - 0.012308094  * T  * T
          - 0.0164248277778 * RH * RH
          + 0.002211732  * T  * T  * RH
          + 0.00072546   * T  * RH * RH
          - 0.000003582  * T  * T  * RH * RH)
    return round(hi, 2)


# ─────────────────────────────────────────────
#  COMFORT INDEX  (0–100)
# ─────────────────────────────────────────────
def comfort_score(T, RH):
    temp_score = max(0, 100 - abs(T - 22) * 5)
    hum_score  = max(0, 100 - abs(RH - 50) * 1.5)
    return round((temp_score + hum_score) / 2, 1)


# ─────────────────────────────────────────────
#  ALERT CHECKER
# ─────────────────────────────────────────────
def check_alerts(T, RH):
    msgs = []
    if T > TEMP_HIGH:  msgs.append(f"🔴 HIGH TEMP: {T:.1f}°C")
    if T < TEMP_LOW:   msgs.append(f"🔵 LOW TEMP: {T:.1f}°C")
    if RH > HUM_HIGH:  msgs.append(f"💧 HIGH HUMIDITY: {RH:.1f}%")
    if RH < HUM_LOW:   msgs.append(f"🌵 LOW HUMIDITY: {RH:.1f}%")
    return msgs

def detect_anomaly(temps, hums):
    """Use recent sensor history to flag an unusual latest reading."""
    if len(temps) < 40:
        return "WARMING UP", None

    history = np.column_stack((
        np.asarray(temps[:-1], dtype=float),
        np.asarray(hums[:-1], dtype=float),
    ))
    latest = np.asarray([[float(temps[-1]), float(hums[-1])]])

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
    )
    model.fit(history)

    score = float(model.decision_function(latest)[0])
    prediction = int(model.predict(latest)[0])

    # Use the model label plus a conservative score threshold so normal
    # edge-of-range readings are not over-reported as anomalies.
    status = "ANOMALY" if prediction == -1 and score < -0.09 else "NORMAL"
    return status, score


# ─────────────────────────────────────────────
#  CSV LOGGER
# ─────────────────────────────────────────────
def log_to_csv(ts, T, RH, HI, comfort):
    header = not os.path.exists(DATA_LOG_FILE)
    with open(DATA_LOG_FILE, "a", encoding="utf-8", newline="") as f:
        if header:
            f.write("timestamp,temperature,humidity,heat_index,comfort\n")
        f.write(f"{ts},{T},{RH},{HI},{comfort}\n")


# ─────────────────────────────────────────────
#  SERIAL READER  (runs in background thread)
# ─────────────────────────────────────────────
def serial_reader(port):
    import serial
    global reading_count
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
        print(f"✅ Connected to {port}")
        time.sleep(2)
        while True:
            line = ser.readline().decode("utf-8").strip()
            if "," in line:
                parts = line.split(",")
                if len(parts) == 2:
                    try:
                        T = float(parts[0].strip())
                        RH = float(parts[1].strip())
                        if not (math.isfinite(T) and math.isfinite(RH)):
                            continue
                        HI = calc_heat_index(T, RH)
                        cs = comfort_score(T, RH)
                        ts = datetime.now().strftime("%H:%M:%S")
                        with lock:
                            timestamps.append(ts)
                            temperatures.append(T)
                            humidities.append(RH)
                            heat_indices.append(HI)
                            reading_count += 1
                            al = check_alerts(T, RH)
                            if al:
                                alerts.extend(al)
                        log_to_csv(ts, T, RH, HI, cs)
                    except ValueError:
                        pass
    except Exception as e:
        print(f"❌ Serial error: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
#  DEMO DATA GENERATOR  (no Arduino needed)
# ─────────────────────────────────────────────
def demo_generator():
    global reading_count
    t_base = 28.0
    h_base = 60.0
    step   = 0
    while True:
        noise_t = math.sin(step * 0.15) * 3 + random.uniform(-0.5, 0.5)
        noise_h = math.cos(step * 0.12) * 8 + random.uniform(-1, 1)
        T  = round(t_base + noise_t, 1)
        RH = round(max(20, min(95, h_base + noise_h)), 1)
        HI = calc_heat_index(T, RH)
        cs = comfort_score(T, RH)
        ts = datetime.now().strftime("%H:%M:%S")
        with lock:
            timestamps.append(ts)
            temperatures.append(T)
            humidities.append(RH)
            heat_indices.append(HI)
            reading_count += 1
            al = check_alerts(T, RH)
            if al:
                alerts.extend(al)
        log_to_csv(ts, T, RH, HI, cs)
        step  += 1
        time.sleep(2)


# ─────────────────────────────────────────────
#  MATPLOTLIB DARK THEME SETUP
# ─────────────────────────────────────────────
def apply_dark_theme():
    plt.rcParams.update({
        "figure.facecolor":  BG_COLOR,
        "axes.facecolor":    PANEL_COLOR,
        "axes.edgecolor":    BORDER_COLOR,
        "axes.labelcolor":   TEXT_COLOR,
        "axes.grid":         True,
        "grid.color":        BORDER_COLOR,
        "grid.linestyle":    "--",
        "grid.alpha":        0.5,
        "xtick.color":       MUTED_COLOR,
        "ytick.color":       MUTED_COLOR,
        "text.color":        TEXT_COLOR,
        "legend.facecolor":  PANEL_COLOR,
        "legend.edgecolor":  BORDER_COLOR,
        "font.family":       "DejaVu Sans",
        "font.size":         9,
    })


# ─────────────────────────────────────────────
#  FIGURE & AXES LAYOUT
# ─────────────────────────────────────────────
def build_figure():
    fig = plt.figure(figsize=(22, 14), facecolor=BG_COLOR)
    fig.canvas.manager.set_window_title("Sensor Dashboard  |  Real-Time Monitor")

    # Row 0: Temperature | Humidity          (2 panels)
    # Row 1: Heat Index  | Distribution      (2 panels)
    # Row 2: Prediction  (full width)        (1 panel)
    # Row 3: Bar Chart   | Scatter           (2 panels)
    # Row 4: Gauge       | Stats             (2 panels)

    gs = gridspec.GridSpec(
        5, 2,
        figure=fig,
        hspace=0.70,
        wspace=0.30,
        top=0.90, bottom=0.05,
        left=0.06, right=0.97,
        height_ratios=[1, 1, 0.9, 1, 1]
    )

    ax_temp   = fig.add_subplot(gs[0, 0])   # Temperature
    ax_hum    = fig.add_subplot(gs[0, 1])   # Humidity
    ax_hi     = fig.add_subplot(gs[1, 0])   # Heat Index
    ax_dist   = fig.add_subplot(gs[1, 1])   # Distribution KDE
    ax_dist_hum = ax_dist.twinx()            # persistent humidity density axis
    ax_pred   = fig.add_subplot(gs[2, :])   # Prediction (full width)
    ax_bar    = fig.add_subplot(gs[3, 0])   # Bar Chart
    ax_scatter= fig.add_subplot(gs[3, 1])   # Scatter
    ax_gauge  = fig.add_subplot(gs[4, 0])   # Comfort Gauge
    ax_stats  = fig.add_subplot(gs[4, 1])   # Stats Table

    axes = dict(
        temp=ax_temp,
        hum=ax_hum,
        hi=ax_hi,
        dist=ax_dist,
        dist_hum=ax_dist_hum,
        scatter=ax_scatter,
        pred=ax_pred,
        bar=ax_bar,
        gauge=ax_gauge,
        stats=ax_stats,
    )
    return fig, axes


# ─────────────────────────────────────────────
#  HEADER  (title bar drawn on figure)
# ─────────────────────────────────────────────
def draw_header(fig, reading_count, uptime_s):
    for artist in getattr(fig, '_header_artists', []):
        try: artist.remove()
        except: pass
    fig._header_artists = []

    uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_s))
    now_str    = datetime.now().strftime("%d %b %Y  |  %H:%M:%S")

    title = fig.text(0.5, 0.955,
                     "*** REAL-TIME ENVIRONMENTAL SENSOR DASHBOARD ***",
                     ha="center", va="center", fontsize=16, fontweight="bold",
                     color=TEXT_COLOR, transform=fig.transFigure)

    sub = fig.text(0.5, 0.927,
                   f"Arduino DHT11  ·  {now_str}  ·  Readings: {reading_count}  ·  Uptime: {uptime_str}",
                   ha="center", va="center", fontsize=9, color=MUTED_COLOR,
                   transform=fig.transFigure)

    fig._header_artists = [title, sub]


# ─────────────────────────────────────────────
#  SMOOTH  helper
# ─────────────────────────────────────────────
def smooth(data, sigma=2):
    arr = np.array(data)
    if len(arr) < 4:
        return arr
    return gaussian_filter1d(arr, sigma=sigma)


# ─────────────────────────────────────────────
#  PLOT: Temperature / Humidity time series
# ─────────────────────────────────────────────
def plot_time_series(ax, data, label, color, unit, high_thresh, low_thresh):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    if len(data) < 2:
        ax.set_title(f"{label} — waiting for data…", color=TEXT_COLOR, pad=8)
        return

    x   = np.arange(len(data))
    raw = np.array(data)
    smo = smooth(raw)

    # Gradient fill under curve
    ax.fill_between(x, raw, alpha=0.15, color=color)
    ax.plot(x, raw, color=color, alpha=0.35, linewidth=1, linestyle="--")
    ax.plot(x, smo, color=color, linewidth=2.5, label=f"{label} (smoothed)")

    # Current value marker
    ax.scatter([x[-1]], [raw[-1]], color=color, s=60, zorder=5)
    ax.annotate(f"  {raw[-1]:.1f}{unit}", xy=(x[-1], raw[-1]),
                color=color, fontsize=10, fontweight="bold",
                va="center")

    # Threshold lines
    ax.axhline(high_thresh, color=ALERT_COLOR, linestyle=":", linewidth=1.2, alpha=0.7,
               label=f"High ({high_thresh}{unit})")
    ax.axhline(low_thresh, color=HUM_COLOR, linestyle=":", linewidth=1.2, alpha=0.7,
               label=f"Low ({low_thresh}{unit})")

    # Trend arrow via linear regression
    if len(x) > 5:
        slope, intercept, *_ = linregress(x, raw)
        trend_y = slope * x + intercept
        ax.plot(x, trend_y, color=AVG_COLOR, linewidth=1,
                linestyle="-.", alpha=0.6, label="Trend")
        direction = "↑" if slope > 0 else "↓"
        ax.set_title(f"{label}  {direction}  |  Now: {raw[-1]:.1f}{unit}",
                     color=TEXT_COLOR, pad=8, fontsize=10, fontweight="bold")
    else:
        ax.set_title(f"{label}  |  Now: {raw[-1]:.1f}{unit}",
                     color=TEXT_COLOR, pad=8, fontsize=10, fontweight="bold")

    ax.set_ylabel(f"{label} ({unit})", color=MUTED_COLOR, fontsize=8)
    ax.set_xlabel("Reading #", color=MUTED_COLOR, fontsize=8)
    ax.legend(fontsize=7, loc="upper left",
              facecolor=PANEL_COLOR, edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR)
    ax.tick_params(colors=MUTED_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)


# ─────────────────────────────────────────────
#  PLOT: Heat Index
# ─────────────────────────────────────────────
def plot_heat_index(ax, temps, hums, his):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    if len(his) < 2:
        ax.set_title("Heat Index — waiting…", color=TEXT_COLOR); return

    x   = np.arange(len(his))
    raw = np.array(his)
    smo = smooth(raw)

    ax.fill_between(x, raw, alpha=0.12, color=FEEL_COLOR)
    ax.plot(x, smo, color=FEEL_COLOR, linewidth=2.5, label="Heat Index")

    # Moving average (window=10)
    if len(raw) >= 10:
        ma = pd.Series(raw).rolling(10).mean().values
        ax.plot(x, ma, color=AVG_COLOR, linewidth=1.5,
                linestyle="--", label="MA-10")

    ax.scatter([x[-1]], [raw[-1]], color=FEEL_COLOR, s=60, zorder=5)
    ax.annotate(f"  {raw[-1]:.1f}°C", xy=(x[-1], raw[-1]),
                color=FEEL_COLOR, fontsize=10, fontweight="bold", va="center")

    ax.set_title(f"🌤 Feels-Like (Heat Index)  |  {raw[-1]:.1f}°C",
                 color=TEXT_COLOR, pad=8, fontsize=10, fontweight="bold")
    ax.set_ylabel("Heat Index (°C)", color=MUTED_COLOR, fontsize=8)
    ax.set_xlabel("Reading #", color=MUTED_COLOR, fontsize=8)
    ax.legend(fontsize=7, loc="upper left",
              facecolor=PANEL_COLOR, edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR)
    ax.tick_params(colors=MUTED_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)


# ─────────────────────────────────────────────
#  PLOT: KDE / Distribution
# ─────────────────────────────────────────────
def plot_distribution(ax, hum_ax, temps, hums):
    """Draw the temperature and humidity KDEs without stacking axes."""
    ax.cla()
    hum_ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    hum_ax.set_facecolor(PANEL_COLOR)

    if len(temps) < 5:
        ax.set_title("Distribution — collecting…", color=TEXT_COLOR)
        return

    t_arr = np.asarray(temps, dtype=float)
    h_arr = np.asarray(hums, dtype=float)

    sns.kdeplot(
        t_arr, ax=ax, color=TEMP_COLOR, fill=True,
        alpha=0.35, linewidth=2, label="Temp (°C)"
    )
    sns.kdeplot(
        h_arr, ax=hum_ax, color=HUM_COLOR, fill=True,
        alpha=0.25, linewidth=2, label="Humidity (%)"
    )

    ax.axvline(t_arr.mean(), color=TEMP_COLOR, linestyle="--", linewidth=1.2)
    hum_ax.axvline(h_arr.mean(), color=HUM_COLOR, linestyle="--", linewidth=1.2)

    ax.set_title("📊 Distribution (KDE)", color=TEXT_COLOR, pad=8,
                 fontsize=10, fontweight="bold")
    ax.set_xlabel("Value", color=MUTED_COLOR, fontsize=8)
    ax.set_ylabel("Density (Temp)", color=TEMP_COLOR, fontsize=8)
    hum_ax.set_ylabel("Density (Hum)", color=HUM_COLOR, fontsize=8)
    ax.tick_params(colors=MUTED_COLOR)
    hum_ax.tick_params(colors=MUTED_COLOR)

    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)
    for sp in hum_ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = hum_ax.get_legend_handles_labels()
    ax.legend(
        lines1 + lines2, labels1 + labels2,
        fontsize=7, loc="upper right",
        facecolor=PANEL_COLOR, edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR
    )


# ─────────────────────────────────────────────
#  PLOT: Scatter  Temp vs Humidity
# ─────────────────────────────────────────────
def plot_scatter(ax, temps, hums):
    """Draw the scatter plot without accumulating colorbars."""
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)

    if len(temps) < 5:
        ax.set_title("Scatter — collecting…", color=TEXT_COLOR)
        return

    t_arr = np.asarray(temps, dtype=float)
    h_arr = np.asarray(hums, dtype=float)
    ages = np.linspace(0, 1, len(t_arr))  # colour by recency

    scatter = ax.scatter(
        t_arr, h_arr, c=ages, cmap="plasma",
        s=30, alpha=0.7, edgecolors=BORDER_COLOR, linewidths=0.3
    )

    if len(t_arr) > 5:
        slope, intercept, r_value, *_ = linregress(t_arr, h_arr)
        x_line = np.linspace(t_arr.min(), t_arr.max(), 50)
        ax.plot(
            x_line, slope * x_line + intercept,
            color=AVG_COLOR, linewidth=1.5, linestyle="--",
            label=f"R²={r_value ** 2:.2f}"
        )
        ax.legend(
            fontsize=7, facecolor=PANEL_COLOR,
            edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR
        )

    ax.set_title("🔵 Temp vs Humidity (Scatter)", color=TEXT_COLOR,
                 pad=8, fontsize=10, fontweight="bold")
    ax.set_xlabel("Temperature (°C)", color=MUTED_COLOR, fontsize=8)
    ax.set_ylabel("Humidity (%)", color=MUTED_COLOR, fontsize=8)
    ax.tick_params(colors=MUTED_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)


# ─────────────────────────────────────────────
#  PLOT: Seaborn bar – recent readings
# ─────────────────────────────────────────────
def plot_bar(ax, temps, hums, ts_list):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    if len(temps) < 2:
        ax.set_title("Bar – collecting…", color=TEXT_COLOR); return

    N   = min(20, len(temps))
    t_s = list(temps)[-N:]
    h_s = list(hums)[-N:]
    tsl = list(ts_list)[-N:]
    x   = np.arange(N)
    w   = 0.38

    ax.bar(x - w/2, t_s, w, color=TEMP_COLOR, alpha=0.85,
           label="Temp (°C)", edgecolor=PANEL_COLOR, linewidth=0.5)
    ax.bar(x + w/2, h_s, w, color=HUM_COLOR, alpha=0.85,
           label="Humidity (%)", edgecolor=PANEL_COLOR, linewidth=0.5)

    ax.set_xticks(x[::max(1, N//6)])
    ax.set_xticklabels([tsl[i] for i in range(0, N, max(1, N//6))],
                       rotation=30, fontsize=7, color=MUTED_COLOR)
    ax.set_title(f"📈 Last {N} Readings (Bar Chart)", color=TEXT_COLOR,
                 pad=8, fontsize=10, fontweight="bold")
    ax.set_ylabel("Value", color=MUTED_COLOR, fontsize=8)
    ax.legend(fontsize=7, loc="upper right",
              facecolor=PANEL_COLOR, edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR)
    ax.tick_params(colors=MUTED_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)


# ─────────────────────────────────────────────
#  PLOT: Comfort Gauge (arc)
# ─────────────────────────────────────────────
def plot_gauge(ax, temps, hums):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    ax.set_aspect("equal")
    ax.axis("off")

    if not temps:
        ax.text(0.5, 0.5, "Waiting…", ha="center", va="center",
                color=MUTED_COLOR, transform=ax.transAxes)
        return

    score = comfort_score(list(temps)[-1], list(hums)[-1])
    angle = 180 - (score / 100) * 180   # 180=0% → 0=100%

    # Background arc
    theta = np.linspace(0, np.pi, 300)
    ax.plot(np.cos(theta), np.sin(theta), color=BORDER_COLOR, linewidth=12, solid_capstyle="round")

    # Coloured arc
    end_theta = np.pi - (score / 100) * np.pi
    theta2    = np.linspace(np.pi, end_theta, 300)
    if score < 40:    arc_col = ALERT_COLOR
    elif score < 65:  arc_col = FEEL_COLOR
    else:             arc_col = HUM_COLOR
    ax.plot(np.cos(theta2), np.sin(theta2), color=arc_col,
            linewidth=12, solid_capstyle="round")

    # Needle
    needle_x = 0.75 * math.cos(math.radians(angle))
    needle_y = 0.75 * math.sin(math.radians(angle))
    ax.annotate("", xy=(needle_x, needle_y), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=TEXT_COLOR,
                                lw=2.5, mutation_scale=12))
    ax.scatter([0], [0], color=TEXT_COLOR, s=50, zorder=5)

    ax.text(0, -0.2, f"{score:.0f}", ha="center", va="center",
            fontsize=26, fontweight="bold", color=arc_col)
    ax.text(0, -0.42, "Comfort Score", ha="center", va="center",
            fontsize=9, color=MUTED_COLOR)
    ax.text(-1.05, -0.12, "0", fontsize=8, color=MUTED_COLOR)
    ax.text(0.92, -0.12, "100", fontsize=8, color=MUTED_COLOR)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.6, 1.1)
    ax.set_title("😊 Comfort Gauge", color=TEXT_COLOR, pad=6,
                 fontsize=10, fontweight="bold")


# ─────────────────────────────────────────────
#  PLOT: Stats table
# ─────────────────────────────────────────────
def plot_stats(ax, temps, hums, his, reading_count, anomaly_status, anomaly_score):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    ax.axis("off")

    if not temps:
        ax.text(0.5, 0.5, "No data yet…", ha="center", va="center",
                color=MUTED_COLOR, transform=ax.transAxes)
        return

    t_arr = np.array(temps)
    h_arr = np.array(hums)
    hi_arr = np.array(his)

    rows = [
        ["Metric", "Temp (°C)", "Hum (%)", "HeatIdx"],
        ["Current", f"{t_arr[-1]:.1f}", f"{h_arr[-1]:.1f}", f"{hi_arr[-1]:.1f}"],
        ["Mean",    f"{t_arr.mean():.1f}", f"{h_arr.mean():.1f}", f"{hi_arr.mean():.1f}"],
        ["Max",     f"{t_arr.max():.1f}", f"{h_arr.max():.1f}", f"{hi_arr.max():.1f}"],
        ["Min",     f"{t_arr.min():.1f}", f"{h_arr.min():.1f}", f"{hi_arr.min():.1f}"],
        ["Std Dev", f"{t_arr.std():.2f}", f"{h_arr.std():.2f}", f"{hi_arr.std():.2f}"],
    ]

    tbl = ax.table(
        cellText  = rows[1:],
        colLabels = rows[0],
        cellLoc   = "center",
        loc       = "upper center",
        bbox      = [0, 0.32, 1, 0.65],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)

    for (r, c), cell in tbl.get_celld().items():
        cell.set_facecolor(PANEL_COLOR if r > 0 else "#21262D")
        cell.set_edgecolor(BORDER_COLOR)
        cell.set_text_props(color=TEXT_COLOR if r > 0 else MUTED_COLOR,
                            fontweight="bold" if r == 0 else "normal")

    # Alert messages
    latest_alerts = alerts[-3:] if alerts else ["✅ All values nominal"]
    ax.text(0.5, 0.26, "⚠ Alerts", ha="center", color=MUTED_COLOR,
            fontsize=9, transform=ax.transAxes)
    for i, msg in enumerate(latest_alerts):
        col = ALERT_COLOR if "🔴" in msg or "🔵" in msg or "💧" in msg or "🌵" in msg else HUM_COLOR
        ax.text(0.5, 0.18 - i * 0.10, msg, ha="center", color=col,
                fontsize=8, transform=ax.transAxes)

    anomaly_text = f"ML anomaly check: {anomaly_status}"
    if anomaly_score is not None:
        anomaly_text += f"  |  score: {anomaly_score:+.3f}"
    anomaly_color = ALERT_COLOR if anomaly_status == "ANOMALY" else HUM_COLOR
    ax.text(0.5, -0.04, anomaly_text, ha="center", color=anomaly_color,
            fontsize=7.5, transform=ax.transAxes)
    ax.text(0.5, -0.11, f"📡 Total Readings: {reading_count}  |  Log: {DATA_LOG_FILE}",
            ha="center", color=MUTED_COLOR, fontsize=7.0, transform=ax.transAxes)

    ax.set_title("📋 Live Statistics", color=TEXT_COLOR, pad=8,
                 fontsize=10, fontweight="bold")


# ─────────────────────────────────────────────
#  PLOT: Prediction (Next 10 readings forecast)
# ─────────────────────────────────────────────
def plot_prediction(ax, temps, hums):
    ax.cla()
    ax.set_facecolor(PANEL_COLOR)
    ax.set_title("Next 10 Readings Forecast", color=TEXT_COLOR,
                 pad=8, fontsize=10, fontweight="bold")

    if len(temps) < 10:
        ax.text(0.5, 0.5, f"Collecting data... ({len(temps)}/10)",
                ha="center", va="center", color=MUTED_COLOR,
                fontsize=11, transform=ax.transAxes)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER_COLOR)
        return

    t_arr = np.array(temps)
    h_arr = np.array(hums)

    # Linear regression on last 20 points
    window = min(20, len(t_arr))
    x_win  = np.arange(window)
    t_win  = t_arr[-window:]
    h_win  = h_arr[-window:]

    t_slope, t_intercept, *_ = linregress(x_win, t_win)
    h_slope, h_intercept, *_ = linregress(x_win, h_win)

    # Predict next 10 readings
    future_x   = np.arange(window, window + 10)
    t_pred     = t_slope * future_x + t_intercept
    h_pred     = h_slope * future_x + h_intercept

    # Clamp humidity between 0-100
    h_pred = np.clip(h_pred, 0, 100)

    # Plot past data
    ax.plot(x_win, t_win, color=TEMP_COLOR, linewidth=2,
            label="Temp - Actual", alpha=0.8)
    ax.plot(x_win, h_win, color=HUM_COLOR, linewidth=2,
            label="Humidity - Actual", alpha=0.8)

    # Plot predictions (dashed)
    pred_x_full = np.arange(window - 1, window + 10)
    ax.plot(pred_x_full,
            np.concatenate([[t_win[-1]], t_pred]),
            color=TEMP_COLOR, linewidth=2, linestyle="--",
            alpha=0.6, label="Temp - Predicted")
    ax.plot(pred_x_full,
            np.concatenate([[h_win[-1]], h_pred]),
            color=HUM_COLOR, linewidth=2, linestyle="--",
            alpha=0.6, label="Hum - Predicted")

    # Shaded prediction zone
    ax.axvspan(window - 0.5, window + 9.5, alpha=0.08,
               color=AVG_COLOR, label="Forecast Zone")

    # Confidence band (±1 std dev of recent data)
    t_std = t_win.std()
    h_std = h_win.std()
    ax.fill_between(pred_x_full,
                    np.concatenate([[t_win[-1]], t_pred]) - t_std,
                    np.concatenate([[t_win[-1]], t_pred]) + t_std,
                    alpha=0.10, color=TEMP_COLOR)
    ax.fill_between(pred_x_full,
                    np.concatenate([[h_win[-1]], h_pred]) - h_std,
                    np.concatenate([[h_win[-1]], h_pred]) + h_std,
                    alpha=0.08, color=HUM_COLOR)

    # Divider line between actual and predicted
    ax.axvline(window - 0.5, color=AVG_COLOR, linewidth=1.2,
               linestyle=":", alpha=0.8)
    ax.text(window, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else min(t_arr.min(), h_arr.min()),
            "  FORECAST -->", color=AVG_COLOR, fontsize=7, va="bottom")

    # Annotation: predicted next value
    ax.annotate(f"T: {t_pred[0]:.1f}°C",
                xy=(window, t_pred[0]),
                xytext=(window + 1, t_pred[0] + 1),
                color=TEMP_COLOR, fontsize=8, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=TEMP_COLOR, lw=1))
    ax.annotate(f"H: {h_pred[0]:.1f}%",
                xy=(window, h_pred[0]),
                xytext=(window + 1, h_pred[0] - 2),
                color=HUM_COLOR, fontsize=8, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=HUM_COLOR, lw=1))

    ax.set_xlabel("Reading #", color=MUTED_COLOR, fontsize=8)
    ax.set_ylabel("Value", color=MUTED_COLOR, fontsize=8)
    ax.legend(fontsize=7, loc="upper left", ncol=2,
              facecolor=PANEL_COLOR, edgecolor=BORDER_COLOR, labelcolor=TEXT_COLOR)
    ax.tick_params(colors=MUTED_COLOR)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER_COLOR)


# ─────────────────────────────────────────────
#  MAIN UPDATE FUNCTION  (called every frame)
# ─────────────────────────────────────────────
def update(frame, fig, axes):
    with lock:
        t_snap  = list(temperatures)
        h_snap  = list(humidities)
        hi_snap = list(heat_indices)
        ts_snap = list(timestamps)
        rc      = reading_count

    anomaly_status, anomaly_score = detect_anomaly(t_snap, h_snap)
    uptime = time.time() - start_time

    draw_header(fig, rc, uptime)
    plot_time_series(axes["temp"],    t_snap, "Temperature", TEMP_COLOR, "°C", TEMP_HIGH, TEMP_LOW)
    plot_time_series(axes["hum"],     h_snap, "Humidity",    HUM_COLOR,  "%",  HUM_HIGH,  HUM_LOW)
    plot_heat_index (axes["hi"],      t_snap, h_snap, hi_snap)
    plot_distribution(axes["dist"], axes["dist_hum"], t_snap, h_snap)
    plot_scatter    (axes["scatter"], t_snap, h_snap)
    plot_prediction (axes["pred"],    t_snap, h_snap)
    plot_bar        (axes["bar"],     t_snap, h_snap, ts_snap)
    plot_gauge      (axes["gauge"],   t_snap, h_snap)
    plot_stats      (axes["stats"],   t_snap, h_snap, hi_snap, rc, anomaly_status, anomaly_score)


# ─────────────────────────────────────────────
#  PORT SELECTION
# ─────────────────────────────────────────────
def choose_port():
    """Show available serial ports and return a validated selection."""
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No serial ports found. Use --demo mode.")
        sys.exit(1)

    print("\n📡 Available COM Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i}]  {port.device}  —  {port.description}")

    while True:
        choice = input("\nEnter port number (or press Enter for [0]): ").strip()

        if choice == "":
            return ports[0].device

        if choice.isdigit():
            index = int(choice)
            if 0 <= index < len(ports):
                return ports[index].device

        print(f"Invalid selection. Enter a number from 0 to {len(ports) - 1}.")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Arduino Sensor Dashboard")
    parser.add_argument("--demo", action="store_true",
                        help="Run in demo mode (no Arduino required)")
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════╗
║   🌡️  Arduino Sensor Dashboard  v2.1       ║
║   Real-Time Environmental Monitoring         ║
╚══════════════════════════════════════════════╝
    """)

    apply_dark_theme()
    fig, axes = build_figure()

    if args.demo:
        print("🎮 DEMO MODE — Simulating sensor data…")
        t = threading.Thread(target=demo_generator, daemon=True)
    else:
        port = choose_port()
        t = threading.Thread(target=serial_reader, args=(port,), daemon=True)

    t.start()
    print("🚀 Dashboard launching… Close the window to exit.\n")

    animation = FuncAnimation(
        fig, update,
        fargs=(fig, axes),
        interval=UPDATE_INTERVAL,
        cache_frame_data=False
    )

    plt.show()
    print(f"\n✅ Session ended. Data saved to: {DATA_LOG_FILE}")


if __name__ == "__main__":
    main()