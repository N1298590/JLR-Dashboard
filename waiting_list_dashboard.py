"""
Customer Waiting List Dashboard
================================
Generates a multi-page dashboard (saved as a PNG) from the
customer waiting list sections of Data_set_examples_Main.csv.

Covers three years of data: 2023, 2024, and 2025.

Run:
    python waiting_list_dashboard.py

Output:
    waiting_list_dashboard.png  (saved alongside this script)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ── 1. DATA EXTRACTION ──────────────────────────────────────────────────────

def parse_num(val):
    """Convert comma-formatted string or number to int."""
    if pd.isna(val):
        return None
    try:
        return int(str(val).replace(",", "").strip())
    except ValueError:
        return None


def extract_waiting_list(df, header_row_idx):
    """
    Extract (week, customers_per_week, total_waiting_list) starting from the
    row after the header (which contains 'Week' in column 0).
    """
    rows = []
    for i in range(header_row_idx + 1, len(df)):
        row = df.iloc[i]
        week = parse_num(row.iloc[0])
        cpw  = parse_num(row.iloc[1])
        twl  = parse_num(row.iloc[2])
        if week is None:
            break
        rows.append({"week": week, "customers_per_week": cpw, "total_waiting_list": twl})
    return pd.DataFrame(rows)


raw = pd.read_csv("/mnt/user-data/uploads/Data_set_examples_Main.csv", header=None)

# Locate header rows that contain "Week" in column 0
header_rows = raw[raw.iloc[:, 0].astype(str).str.strip() == "Week"].index.tolist()
# Also locate the 2025 section (column 0 == "Weeks")
weeks_rows  = raw[raw.iloc[:, 0].astype(str).str.strip() == "Weeks"].index.tolist()
header_rows_all = sorted(header_rows + weeks_rows)

assert len(header_rows_all) == 3, f"Expected 3 header rows, found {header_rows_all}"

wl2023 = extract_waiting_list(raw, header_rows_all[0])
wl2024 = extract_waiting_list(raw, header_rows_all[1])
wl2025 = extract_waiting_list(raw, header_rows_all[2])

wl2023["year"] = 2023
wl2024["year"] = 2024
wl2025["year"] = 2025

all_years = pd.concat([wl2023, wl2024, wl2025], ignore_index=True)

# 2025 target
TARGET_2025 = 87_000

# ── 2. COMPUTED STATS ────────────────────────────────────────────────────────

def year_stats(df):
    cpw = df["customers_per_week"].dropna()
    twl = df["total_waiting_list"].dropna()
    return {
        "total_added":   int(cpw.sum()),
        "final_total":   int(twl.iloc[-1]),
        "peak_week":     int(df.loc[cpw.idxmax(), "week"]),
        "peak_cpw":      int(cpw.max()),
        "min_cpw":       int(cpw.min()),
        "avg_cpw":       round(cpw.mean(), 1),
        "median_cpw":    round(cpw.median(), 1),
        "std_cpw":       round(cpw.std(), 1),
        "weeks":         len(df),
    }

s23 = year_stats(wl2023)
s24 = year_stats(wl2024)
s25 = year_stats(wl2025)

# YoY growth
def yoy(v_new, v_old):
    return round(100 * (v_new - v_old) / v_old, 1) if v_old else None

growth_total_23_24 = yoy(s24["final_total"], s23["final_total"])
growth_total_24_25 = yoy(s25["final_total"], s24["final_total"])
growth_avg_23_24   = yoy(s24["avg_cpw"],     s23["avg_cpw"])
growth_avg_24_25   = yoy(s25["avg_cpw"],     s24["avg_cpw"])

# 2025 target progress
progress_pct = round(100 * s25["final_total"] / TARGET_2025, 1)
shortfall    = TARGET_2025 - s25["final_total"]

# ── 3. PALETTE & STYLE ───────────────────────────────────────────────────────

C23 = "#4A90D9"      # blue
C24 = "#F5A623"      # amber
C25 = "#7ED321"      # green
CTGT= "#E94B3C"      # red (target line)
BG  = "#1C1C2E"      # dark navy background
PANEL = "#2A2A42"    # slightly lighter panel
TEXT = "#E8E8F0"
GRID = "#3A3A55"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   PANEL,
    "axes.edgecolor":   GRID,
    "axes.labelcolor":  TEXT,
    "xtick.color":      TEXT,
    "ytick.color":      TEXT,
    "text.color":       TEXT,
    "grid.color":       GRID,
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "DejaVu Sans",
    "legend.facecolor": PANEL,
    "legend.edgecolor": GRID,
    "legend.labelcolor":TEXT,
})

def fmt_k(x, _=None):
    """Format large numbers with K/M suffix."""
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"{x/1_000:.0f}K"
    return str(int(x))

def arrow_badge(ax, x, y, text, color, fontsize=8):
    ax.annotate(text, xy=(x, y),
                xytext=(x, y * 1.07),
                fontsize=fontsize, color=color, ha="center", va="bottom",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8),
                bbox=dict(boxstyle="round,pad=0.2", fc=PANEL, ec=color, lw=0.8))

# ── 4. FIGURE LAYOUT ─────────────────────────────────────────────────────────

fig = plt.figure(figsize=(22, 28), facecolor=BG)
fig.suptitle("Customer Waiting List Dashboard  ·  2023 – 2025",
             fontsize=22, fontweight="bold", color=TEXT, y=0.995)

gs = fig.add_gridspec(
    5, 3,
    height_ratios=[0.18, 1, 1, 1, 1],
    hspace=0.55, wspace=0.35,
    left=0.06, right=0.97, top=0.97, bottom=0.03,
)

# ── ROW 0: KPI CARDS ─────────────────────────────────────────────────────────

kpi_data = [
    ("2023 Final Total",   f"{s23['final_total']:,}",  f"Avg {s23['avg_cpw']:,}/wk",  C23),
    ("2024 Final Total",   f"{s24['final_total']:,}",  f"+{growth_total_23_24}% vs 2023", C24),
    ("2025 Final Total",   f"{s25['final_total']:,}",  f"+{growth_total_24_25}% vs 2024", C25),
    ("2025 Target",        f"{TARGET_2025:,}",          f"{progress_pct}% achieved",   CTGT),
    ("2025 Shortfall",     f"{shortfall:,}",            "to reach target",              "#BB86FC"),
    ("Peak Week (2025)",   f"Wk {s25['peak_week']}",   f"{s25['peak_cpw']:,} added",   "#00BCD4"),
]

for col_idx in range(3):
    ax_kpi = fig.add_subplot(gs[0, col_idx])
    ax_kpi.set_xlim(0, 1); ax_kpi.set_ylim(0, 1)
    ax_kpi.axis("off")
    for card_i in range(2):
        d = kpi_data[col_idx * 2 + card_i]
        left = card_i * 0.52
        rect = mpatches.FancyBboxPatch(
            (left, 0.05), 0.46, 0.88,
            boxstyle="round,pad=0.02",
            facecolor=PANEL, edgecolor=d[3], linewidth=2,
            transform=ax_kpi.transAxes, figure=fig,
        )
        ax_kpi.add_patch(rect)
        ax_kpi.text(left + 0.23, 0.75, d[0], ha="center", va="center",
                    fontsize=7.5, color="#AAAACC", transform=ax_kpi.transAxes)
        ax_kpi.text(left + 0.23, 0.48, d[1], ha="center", va="center",
                    fontsize=13, fontweight="bold", color=d[3],
                    transform=ax_kpi.transAxes)
        ax_kpi.text(left + 0.23, 0.22, d[2], ha="center", va="center",
                    fontsize=7.5, color=TEXT, transform=ax_kpi.transAxes)

# ── ROW 1: CUMULATIVE TOTAL WAITING LIST (all 3 years) ───────────────────────

ax1 = fig.add_subplot(gs[1, :])
for df, color, year in [(wl2023, C23, 2023), (wl2024, C24, 2024), (wl2025, C25, 2025)]:
    ax1.plot(df["week"], df["total_waiting_list"], color=color,
             linewidth=2.2, label=str(year), zorder=3)
    ax1.fill_between(df["week"], df["total_waiting_list"], alpha=0.12, color=color)

ax1.axhline(TARGET_2025, color=CTGT, linewidth=1.8, linestyle="--",
            label=f"2025 Target ({TARGET_2025:,})", zorder=4)
ax1.set_title("Cumulative Total Waiting List – All Years", fontsize=13, fontweight="bold")
ax1.set_xlabel("Week of Year")
ax1.set_ylabel("Total Waiting List")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax1.legend(loc="upper left", fontsize=9)
ax1.grid(True, axis="y")
ax1.set_xlim(1, 52)

# Annotate final values
for df, color in [(wl2023, C23), (wl2024, C24), (wl2025, C25)]:
    last = df.iloc[-1]
    ax1.annotate(f"{int(last['total_waiting_list']):,}",
                 xy=(last["week"], last["total_waiting_list"]),
                 fontsize=8, color=color, fontweight="bold",
                 xytext=(last["week"] - 3.5, last["total_waiting_list"] * 0.97),
                 arrowprops=dict(arrowstyle="-", color=color, lw=0.6))

# ── ROW 2: CUSTOMERS PER WEEK bar chart (all 3 years) ───────────────────────

ax2 = fig.add_subplot(gs[2, :])
weeks = wl2025["week"].values
w = 0.28

# Align all three to the same week numbers (52 weeks each, but 2023 has partial)
def safe_cpw(df, wk):
    row = df[df["week"] == wk]
    return int(row["customers_per_week"].values[0]) if len(row) else 0

cpw23 = [safe_cpw(wl2023, w) for w in range(1, 53)]
cpw24 = [safe_cpw(wl2024, w) for w in range(1, 53)]
cpw25 = [safe_cpw(wl2025, w) for w in range(1, 53)]
wk_range = np.arange(1, 53)

ax2.bar(wk_range - w, cpw23, width=w, color=C23, alpha=0.85, label="2023")
ax2.bar(wk_range,     cpw24, width=w, color=C24, alpha=0.85, label="2024")
ax2.bar(wk_range + w, cpw25, width=w, color=C25, alpha=0.85, label="2025")

# Average lines
for avg, color in [(s23["avg_cpw"], C23), (s24["avg_cpw"], C24), (s25["avg_cpw"], C25)]:
    ax2.axhline(avg, color=color, linewidth=1.2, linestyle=":", alpha=0.8)

ax2.set_title("Customers Added Per Week – Year Comparison", fontsize=13, fontweight="bold")
ax2.set_xlabel("Week of Year")
ax2.set_ylabel("Customers per Week")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax2.legend(loc="upper right", fontsize=9)
ax2.grid(True, axis="y")
ax2.set_xlim(0.5, 52.5)

# ── ROW 3: LEFT – Rolling 4-week average │ MIDDLE – YoY comparison │ RIGHT – 2025 target gauge

# 3a Rolling average
ax3a = fig.add_subplot(gs[3, 0])
for df, color, yr in [(wl2023, C23, "2023"), (wl2024, C24, "2024"), (wl2025, C25, "2025")]:
    rolling = df["customers_per_week"].rolling(4, min_periods=1).mean()
    ax3a.plot(df["week"], rolling, color=color, linewidth=2, label=yr)
ax3a.set_title("4-Week Rolling Avg (Customers/Wk)", fontsize=10, fontweight="bold")
ax3a.set_xlabel("Week"); ax3a.set_ylabel("Avg Customers/Wk")
ax3a.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax3a.legend(fontsize=8); ax3a.grid(True, axis="y")

# 3b Year-over-year bar comparison of key stats
ax3b = fig.add_subplot(gs[3, 1])
categories = ["Total Added", "Final Total", "Avg/Wk", "Peak/Wk"]
vals23 = [s23["total_added"], s23["final_total"], s23["avg_cpw"], s23["peak_cpw"]]
vals24 = [s24["total_added"], s24["final_total"], s24["avg_cpw"], s24["peak_cpw"]]
vals25 = [s25["total_added"], s25["final_total"], s25["avg_cpw"], s25["peak_cpw"]]

x = np.arange(len(categories))
bw = 0.25
bars23 = ax3b.bar(x - bw, vals23, bw, color=C23, alpha=0.85, label="2023")
bars24 = ax3b.bar(x,      vals24, bw, color=C24, alpha=0.85, label="2024")
bars25 = ax3b.bar(x + bw, vals25, bw, color=C25, alpha=0.85, label="2025")
ax3b.set_title("Key Stats – Year-over-Year", fontsize=10, fontweight="bold")
ax3b.set_xticks(x); ax3b.set_xticklabels(categories, fontsize=8)
ax3b.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax3b.legend(fontsize=8); ax3b.grid(True, axis="y")

# 3c 2025 Target gauge (donut-style)
ax3c = fig.add_subplot(gs[3, 2])
ax3c.set_xlim(0, 1); ax3c.set_ylim(0, 1); ax3c.axis("off")
ax3c.set_title("2025 Target Progress", fontsize=10, fontweight="bold")

# Donut
theta_fill = 2 * np.pi * (s25["final_total"] / TARGET_2025)
theta_gap  = 2 * np.pi - theta_fill

angles_fill = np.linspace(np.pi / 2, np.pi / 2 - theta_fill, 300)
angles_gap  = np.linspace(np.pi / 2 - theta_fill, np.pi / 2 - 2 * np.pi, 100)

inner, outer = 0.28, 0.42
cx, cy = 0.5, 0.52

def donut_arc(ax, angles, color, inner, outer, cx, cy):
    x_outer = cx + outer * np.cos(angles)
    y_outer = cy + outer * np.sin(angles)
    x_inner = cx + inner * np.cos(angles[::-1])
    y_inner = cy + inner * np.sin(angles[::-1])
    xs = np.concatenate([x_outer, x_inner])
    ys = np.concatenate([y_outer, y_inner])
    ax.fill(xs, ys, color=color, zorder=3)

donut_arc(ax3c, angles_fill, C25,  inner, outer, cx, cy)
donut_arc(ax3c, angles_gap,  GRID, inner, outer, cx, cy)

ax3c.text(cx, cy + 0.03, f"{progress_pct}%", ha="center", va="center",
          fontsize=20, fontweight="bold", color=C25)
ax3c.text(cx, cy - 0.08, "of target reached", ha="center", va="center",
          fontsize=7.5, color=TEXT)
ax3c.text(cx, 0.10, f"Actual: {s25['final_total']:,}  |  Target: {TARGET_2025:,}",
          ha="center", va="center", fontsize=7.5, color=TEXT)
ax3c.text(cx, 0.04, f"Shortfall: {shortfall:,}", ha="center", va="center",
          fontsize=8, color=CTGT, fontweight="bold")

# ── ROW 4: LEFT – Boxplot distribution │ MIDDLE – weekly change (MoM delta) │ RIGHT – 2025 weekly growth rate

# 4a Boxplot distribution
ax4a = fig.add_subplot(gs[4, 0])
data_bp = [
    wl2023["customers_per_week"].dropna().values,
    wl2024["customers_per_week"].dropna().values,
    wl2025["customers_per_week"].dropna().values,
]
bp = ax4a.boxplot(data_bp, patch_artist=True, widths=0.5,
                  medianprops=dict(color="white", linewidth=2),
                  whiskerprops=dict(color=TEXT),
                  capprops=dict(color=TEXT),
                  flierprops=dict(marker="o", markersize=4, alpha=0.6))
for patch, color in zip(bp["boxes"], [C23, C24, C25]):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)
ax4a.set_xticklabels(["2023", "2024", "2025"])
ax4a.set_title("Distribution of Weekly Additions", fontsize=10, fontweight="bold")
ax4a.set_ylabel("Customers per Week")
ax4a.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax4a.grid(True, axis="y")

# 4b Week-on-week delta for 2025
ax4b = fig.add_subplot(gs[4, 1])
delta25 = wl2025["customers_per_week"].diff().dropna()
colors_delta = [C25 if v >= 0 else CTGT for v in delta25]
ax4b.bar(wl2025["week"].iloc[1:], delta25, color=colors_delta, alpha=0.85)
ax4b.axhline(0, color=TEXT, linewidth=0.8)
ax4b.set_title("2025 – Week-on-Week Change in New Customers", fontsize=10, fontweight="bold")
ax4b.set_xlabel("Week"); ax4b.set_ylabel("Δ Customers")
ax4b.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
ax4b.grid(True, axis="y")

# 4c Cumulative growth rate (%) within each year
ax4c = fig.add_subplot(gs[4, 2])
for df, color, yr in [(wl2023, C23, "2023"), (wl2024, C24, "2024"), (wl2025, C25, "2025")]:
    base = df["total_waiting_list"].iloc[0]
    growth_pct = ((df["total_waiting_list"] - base) / base * 100)
    ax4c.plot(df["week"], growth_pct, color=color, linewidth=2, label=yr)
ax4c.set_title("Cumulative Growth Rate (from Wk 1)", fontsize=10, fontweight="bold")
ax4c.set_xlabel("Week"); ax4c.set_ylabel("Growth (%)")
ax4c.legend(fontsize=8); ax4c.grid(True, axis="y")
ax4c.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))

# ── 5. FOOTER STATS TABLE ────────────────────────────────────────────────────

footer_text = (
    f"  2023 →  Total Added: {s23['total_added']:>7,}  |  Final Total: {s23['final_total']:>7,}  |  "
    f"Avg/Wk: {s23['avg_cpw']:>6,.1f}  |  Peak: Wk {s23['peak_week']} ({s23['peak_cpw']:,})  |  "
    f"Min/Wk: {s23['min_cpw']:,}  |  Std: {s23['std_cpw']:,.1f}   "
    f"\n  2024 →  Total Added: {s24['total_added']:>7,}  |  Final Total: {s24['final_total']:>7,}  |  "
    f"Avg/Wk: {s24['avg_cpw']:>6,.1f}  |  Peak: Wk {s24['peak_week']} ({s24['peak_cpw']:,})  |  "
    f"Min/Wk: {s24['min_cpw']:,}  |  Std: {s24['std_cpw']:,.1f}   "
    f"\n  2025 →  Total Added: {s25['total_added']:>7,}  |  Final Total: {s25['final_total']:>7,}  |  "
    f"Avg/Wk: {s25['avg_cpw']:>6,.1f}  |  Peak: Wk {s25['peak_week']} ({s25['peak_cpw']:,})  |  "
    f"Min/Wk: {s25['min_cpw']:,}  |  Std: {s25['std_cpw']:,.1f}  |  "
    f"Target Progress: {progress_pct}%  |  Shortfall: {shortfall:,}"
)

fig.text(0.03, 0.01, footer_text, fontsize=7.2, color="#AAAACC",
         va="bottom", ha="left",
         bbox=dict(boxstyle="round,pad=0.4", fc=PANEL, ec=GRID, alpha=0.8),
         family="monospace")

# ── 6. SAVE ──────────────────────────────────────────────────────────────────

out_path = "/mnt/user-data/outputs/waiting_list_dashboard.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"Dashboard saved → {out_path}")
plt.close(fig)
