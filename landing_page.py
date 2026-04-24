import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import Quality_WCPA as qu
import supplier_readiness as sr
import timing as ti
import waiting_list as wl
import feature_readiness as fr
import manager as mo

# ── Colour palette ────────────────────────────────────────────────────────────
BG_DARK = "#0A0A0A"
BG_CARD = "#111111"
BG_PLOT = "#0D0D0D"
ACCENT = "#00BFFF"
ACCENT2 = "#FF4500"
ACCENT3 = "#32CD32"
ACCENT4 = "#FFD700"
TITLE_FG = "#FFFFFF"
GRID_COL = "#1E1E1E"

# ── Data path ─────────────────────────────────────────────────────────────────
DATA_PATH = 'Data set examples_Main.xlsx'


def _load(sheet, **kw):
    try:
        return pd.read_excel(DATA_PATH, sheet_name=sheet, **kw)
    except Exception:
        return pd.DataFrame()


# Load stable sheets at startup
df_supplier = _load('SUPPLIER READINESS_PSW')
df_waiting = _load('Customer waiting list', header=None)
df_feature = _load('Feature readiness')
df_quality = _load('QUALITY WCPA')


# ── Chart builders ────────────────────────────────────────────────────────────

def make_quality_chart(ax):
    """Bar: avg score per programme — PRG_ rows only, clean short labels."""
    try:
        # Filter to real programme rows only (removes junk rows like 'Build phase', 'OUTPUT:' etc.)
        clean = df_quality[df_quality['Programme_ID'].str.startswith('PRG_', na=False)]
        grp = clean.groupby('Programme_ID')['Score'].mean()
        # Shorten labels: PRG_ATLAS -> ATLAS
        labels = [p.replace('PRG_', '') for p in grp.index]
        colours = [ACCENT3 if v >= 3.5 else ACCENT2 for v in grp.values]
        x = np.arange(len(grp))
        ax.set_axisbelow(True)
        ax.bar(x, grp.values, color=colours, width=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=6, color=TITLE_FG,
                           rotation=35, ha='right', rotation_mode='anchor')
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_title("Avg Quality Score / Programme", fontsize=8,
                     fontweight="bold", color=TITLE_FG, pad=4)
        ax.set_ylabel("Score", fontsize=6, color=TITLE_FG)
        ax.tick_params(axis='y', labelsize=6, colors=TITLE_FG)
    except Exception as e:
        ax.text(0.5, 0.5, f"No data\n{e}", ha='center', va='center',
                color=TITLE_FG, transform=ax.transAxes, fontsize=6)


def make_supplier_chart(ax):
    """Donut: PSW status breakdown."""
    try:
        # Load fresh inside function - avoids stale empty df at import time
        raw = _load('SUPPLIER READINESS_PSW', header=None)
        if raw.empty:
            raise ValueError("Could not load Supplier sheet")
        # Row 0 is blank; row 1 is the real header; data starts at row 2
        header = raw.iloc[1]
        df = raw.iloc[2:].copy()
        df.columns = header
        valid = {'Approved', 'Pending', 'At Risk', 'Rejected'}
        counts = df[df['PSW_Status'].isin(valid)]['PSW_Status'].value_counts()
        colours_map = {'Approved': ACCENT3, 'Pending': ACCENT4,
                       'At Risk': ACCENT2, 'Rejected': '#FF0000'}
        cols = [colours_map.get(str(s), ACCENT) for s in counts.index]
        ax.pie(counts.values, colors=cols, startangle=90,
               wedgeprops=dict(width=0.55),
               autopct='%1.0f%%', pctdistance=0.75,
               textprops={'fontsize': 6, 'color': TITLE_FG})
        ax.legend(counts.index, fontsize=5, loc='lower center',
                  ncol=2, frameon=False, labelcolor=TITLE_FG,
                  bbox_to_anchor=(0.5, -0.18))
        ax.set_title("Supplier PSW Status", fontsize=8,
                     fontweight="bold", color=TITLE_FG, pad=4)
    except Exception as e:
        ax.text(0.5, 0.5, f"No data\n{e}", ha='center', va='center',
                color=TITLE_FG, transform=ax.transAxes, fontsize=6)


def make_timing_chart(ax):
    """Horizontal bar: project status counts.
    Loaded fresh inside the function to avoid a stale empty DataFrame
    if the working directory was not set correctly at import time."""
    try:
        df = _load('Timing')
        if df.empty or 'Project_Status' not in df.columns:
            raise ValueError("Could not load Timing sheet")
        counts = df['Project_Status'].value_counts()
        colour_map = {'On Track': ACCENT3, 'At Risk': ACCENT4, 'Delayed': ACCENT2}
        cols = [colour_map.get(str(s), ACCENT) for s in counts.index]
        y_pos = list(range(len(counts)))
        ax.set_axisbelow(True)
        ax.barh(y_pos, counts.values, color=cols, height=0.55)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(list(counts.index), fontsize=7, color=TITLE_FG)
        ax.tick_params(axis='x', labelsize=6, colors=TITLE_FG)
        ax.set_title("Programme Status Overview", fontsize=8,
                     fontweight="bold", color=TITLE_FG, pad=4)
        ax.set_xlabel("Count", fontsize=6, color=TITLE_FG)
        x_max = counts.values.max()
        ax.set_xlim(0, x_max * 1.15)
        for y, v in zip(y_pos, counts.values):
            ax.text(v + x_max * 0.02, y, str(v), va='center',
                    fontsize=6, color=TITLE_FG)
    except Exception as e:
        ax.text(0.5, 0.5, f"No data\n{e}", ha='center', va='center',
                color=TITLE_FG, transform=ax.transAxes, fontsize=6)


def make_waiting_chart(ax):
    """Line: monthly total waiting list (2023-2025)."""
    try:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        row_2023 = df_waiting.iloc[9, 1:13].astype(float).values
        row_2024 = df_waiting.iloc[78, 1:13].astype(float).values
        row_2025 = df_waiting.iloc[144, 1:13].astype(float).values
        x = np.arange(12)
        ax.plot(x, row_2023, color=ACCENT, linewidth=1.2,
                marker='o', markersize=2, label='2023')
        ax.plot(x, row_2024, color=ACCENT3, linewidth=1.2,
                marker='o', markersize=2, label='2024')
        ax.plot(x, row_2025, color=ACCENT4, linewidth=1.2,
                marker='o', markersize=2, label='2025')
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=5, color=TITLE_FG, rotation=30)
        ax.tick_params(axis='y', labelsize=6, colors=TITLE_FG)
        ax.legend(fontsize=5, frameon=False, labelcolor=TITLE_FG)
        ax.set_title("Monthly Waiting List Total", fontsize=8,
                     fontweight="bold", color=TITLE_FG, pad=4)
    except Exception as e:
        ax.text(0.5, 0.5, f"No data\n{e}", ha='center', va='center',
                color=TITLE_FG, transform=ax.transAxes, fontsize=6)


def make_feature_chart(ax):
    """Donut: overall milestone status counts with legend placed to the right."""
    try:
        valid = {'Achieved', 'In Progress', 'Not Achieved', 'At Risk', 'Delayed'}
        counts = df_feature[df_feature['Milestone_Status'].isin(valid)]['Milestone_Status'].value_counts()
        status_colours = {
            'Achieved':     ACCENT3,
            'In Progress':  ACCENT,
            'Not Achieved': ACCENT2,
            'At Risk':      ACCENT4,
            'Delayed':      '#FF8C00',
        }
        cols = [status_colours.get(str(s), '#888888') for s in counts.index]
        # Shrink the pie axes to the left so the right side is free for the legend
        ax.set_position([0.0, 0.05, 0.55, 0.85])
        ax.pie(counts.values, colors=cols, startangle=90,
               wedgeprops=dict(width=0.55),
               autopct='%1.0f%%', pctdistance=0.75,
               textprops={'fontsize': 6, 'color': TITLE_FG})
        ax.legend(counts.index, fontsize=5, frameon=False,
                  labelcolor=TITLE_FG,
                  loc='center left',
                  bbox_to_anchor=(1.05, 0.5),
                  bbox_transform=ax.transAxes)
        ax.set_title("Feature Milestone Status", fontsize=8,
                     fontweight="bold", color=TITLE_FG, pad=4)
    except Exception as e:
        ax.text(0.5, 0.5, f"No data\n{e}", ha='center', va='center',
                color=TITLE_FG, transform=ax.transAxes, fontsize=6)


# idx 0-4 active; idx 5 intentionally blank (button 6 removed)
CHART_FUNCS = [
    make_quality_chart,
    make_supplier_chart,
    make_timing_chart,
    make_waiting_chart,
    make_feature_chart,
    None,
]

BUTTON_NAMES = [
    'Quality WCPA',
    'Supplier Readiness',
    'Timing',
    'Customer Waiting List',
    'Feature Readiness',
    'manager'
]

# ── Main window ───────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("JLR Production Data Dashboards")
root.configure(bg=BG_DARK)
root.geometry("2048x1024")
root.resizable(True, True)

title_frame = tk.Frame(root, bg="#050505", pady=8)
title_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
tk.Label(title_frame, text="JLR  PRODUCTION  DATA  DASHBOARDS",
         font=("Helvetica", 14, "bold"), bg="#050505", fg=ACCENT,
         pady=4, padx=16).pack(side="left")
tk.Label(title_frame, text="HOME", font=("Helvetica", 9),
         bg="#050505", fg="#666666", pady=4, padx=16).pack(side="right")


def on_button_click(idx):
    if idx == 0:
        win = tk.Toplevel(root)
        qu.Dashboard(root=win)
    elif idx == 1:
        win = tk.Toplevel(root)
        dash = sr.Dashboard(master=win, data_path=DATA_PATH)
        dash.pack(fill="both", expand=True)
    elif idx == 2:
        win = tk.Toplevel(root)
        ti.Dashboard(master=win)
    elif idx == 3:
        win = tk.Toplevel(root)
        app = wl.WaitingListDashboard(master=win, data_path=DATA_PATH)
        app.pack(fill="both", expand=True)
    elif idx == 4:
        win = tk.Toplevel(root)
        fr.Dashboard(master=win)
    elif idx == 5:
        win = tk.Toplevel(root)
        mo.ManagerDashboard(master=win)


def _style_axes(ax, fig):
    ax.set_facecolor(BG_PLOT)
    fig.patch.set_facecolor(BG_CARD)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COL)
    ax.tick_params(colors=TITLE_FG)
    ax.yaxis.label.set_color(TITLE_FG)
    ax.xaxis.label.set_color(TITLE_FG)
    ax.grid(True, color=GRID_COL, linewidth=0.4, linestyle='--', alpha=0.6)


def start():
    for i in range(6):
        row, col = divmod(i, 3)

        card = tk.Frame(root, bg=BG_CARD, bd=0,
                        highlightbackground=ACCENT, highlightthickness=1)
        card.grid(row=row * 2 + 1, column=col,
                  padx=10, pady=(8, 0), sticky="nsew")

        if CHART_FUNCS[i] is not None:
            fig, ax = plt.subplots(figsize=(2.7, 1.95), dpi=85)
            _style_axes(ax, fig)
            CHART_FUNCS[i](ax)
            fig.tight_layout(pad=1.0)
            canvas = FigureCanvasTkAgg(fig, master=card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            # Blank slot - no chart, no button
            tk.Label(card, bg=BG_CARD, width=28, height=9).pack(
                fill="both", expand=True)

        if i < 6:
            btn = tk.Button(
                root, text=BUTTON_NAMES[i],
                font=("Helvetica", 9, "bold"),
                bg="#0D1B2A", fg=ACCENT,
                activebackground=ACCENT, activeforeground=BG_DARK,
                relief="flat", padx=14, pady=4, cursor="hand2",
                bd=0, highlightthickness=0,
                command=lambda idx=i: on_button_click(idx),
            )
            btn.grid(row=row * 2 + 2, column=col, pady=(4, 10))
        else:
            tk.Label(root, bg=BG_DARK, text="", height=2).grid(
                row=row * 2 + 2, column=col)

    for c in range(3):
        root.columnconfigure(c, weight=1)
    for r in range(5):
        root.rowconfigure(r, weight=1)

    root.mainloop()


start()