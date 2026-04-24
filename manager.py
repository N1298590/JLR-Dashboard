import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK = "#0A0A0A"
BG_CARD = "#111111"
BG_MID = "#1A1A2E"
BG_HEADER = "#0D1B2A"
FG_WHITE = "#FFFFFF"
FG_GREY = "#9CA3AF"
ACCENT = "#00BFFF"
GREEN = "#32CD32"
AMBER = "#FFD700"
RED = "#FF4500"
DARK_RED = "#8B0000"

DATA_PATH = 'Data set examples_Main.xlsx'

# ── Rating logic ──────────────────────────────────────────────────────────────
# Each source contributes an at-risk count. The combined weighted total drives the rating.
# Weights: Quality (x2 — score-based severity), Supplier (x1.5), Timing (x1)

QUALITY_WEIGHT = 2.0
SUPPLIER_WEIGHT = 1.5
TIMING_WEIGHT = 1.0


def get_rating(weighted_total):
    """Return (label, colour) based on weighted at-risk score."""
    if weighted_total == 0:
        return "✦ Excellent", GREEN
    elif weighted_total <= 20:
        return "✔ Good", "#90EE90"
    elif weighted_total <= 50:
        return "● Moderate", AMBER
    elif weighted_total <= 90:
        return "▲ High Risk", RED
    else:
        return "✖ Critical", DARK_RED


# ── Data loading ──────────────────────────────────────────────────────────────

def load_all():
    """Returns a DataFrame with one row per person and columns per data source."""

    # --- Quality WCPA: Assignee, at-risk = Score >= 4 ---
    df_q = pd.read_excel(DATA_PATH, sheet_name='QUALITY WCPA')
    df_q.columns = df_q.columns.str.strip()
    df_q = df_q[df_q['Programme_ID'].notna() & df_q['Score'].notna()]
    q_grp = df_q.groupby('Assignee').agg(
        q_total=('Score', 'count'),
        q_risk=('Score', lambda x: int((x >= 4).sum()))
    ).reset_index().rename(columns={'Assignee': 'Person'})

    # --- Supplier Readiness: Approver_Name, at-risk = PSW_Status == 'At Risk' ---
    df_s = pd.read_excel(DATA_PATH, sheet_name='SUPPLIER READINESS_PSW', header=None)
    df_s.columns = df_s.iloc[1]
    df_s = df_s.iloc[2:].copy()
    valid_psw = {'Approved', 'Pending', 'At Risk', 'Rejected'}
    df_s = df_s[df_s['PSW_Status'].isin(valid_psw)]
    s_grp = df_s.groupby('Approver_Name').agg(
        s_total=('PSW_Status', 'count'),
        s_risk=('PSW_Status', lambda x: int((x == 'At Risk').sum()))
    ).reset_index().rename(columns={'Approver_Name': 'Person'})

    # --- Timing: PM_Owner, at-risk = At Risk or Delayed ---
    df_t = pd.read_excel(DATA_PATH, sheet_name='Timing')
    t_grp = df_t.groupby('PM_Owner').agg(
        t_total=('Project_Status', 'count'),
        t_risk=('Project_Status', lambda x: int(x.isin(['At Risk', 'Delayed']).sum()))
    ).reset_index().rename(columns={'PM_Owner': 'Person'})

    # --- Merge all three on Person ---
    df = q_grp.merge(s_grp, on='Person', how='outer') \
        .merge(t_grp, on='Person', how='outer')
    df = df.fillna(0)
    for col in ['q_total', 'q_risk', 's_total', 's_risk', 't_total', 't_risk']:
        df[col] = df[col].astype(int)

    # Weighted at-risk score
    df['weighted'] = (
            df['q_risk'] * QUALITY_WEIGHT +
            df['s_risk'] * SUPPLIER_WEIGHT +
            df['t_risk'] * TIMING_WEIGHT
    )

    df['total_risk'] = df['q_risk'] + df['s_risk'] + df['t_risk']
    df['total_parts'] = df['q_total'] + df['s_total'] + df['t_total']
    df['rating_label'], df['rating_colour'] = zip(*df['weighted'].map(get_rating))
    df = df.sort_values('weighted', ascending=False).reset_index(drop=True)
    return df


# ── Dashboard ─────────────────────────────────────────────────────────────────

class ManagerDashboard:
    def __init__(self, master=None):
        if master is None:
            self.root = tk.Tk()
            self._standalone = True
        else:
            self.root = master
            self._standalone = False

        self.root.title("Manager Overview — At-Risk Summary")
        self.root.geometry("1300x820")
        self.root.configure(bg=BG_DARK)

        self.df = load_all()
        self._build_ui()

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────
        title_bar = tk.Frame(self.root, bg=BG_HEADER, pady=10)
        title_bar.pack(fill=tk.X)
        tk.Button(
            title_bar, text="← Back",
            bg=BG_HEADER, fg=ACCENT,
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            activebackground=BG_CARD, activeforeground=FG_WHITE,
            command=self.root.destroy, padx=10, pady=4,
        ).pack(side=tk.LEFT, padx=(8, 0), pady=6)

        tk.Label(title_bar, text="JLR  PRODUCTION  DATA  DASHBOARDS",
                 font=("Helvetica", 13, "bold"), bg=BG_HEADER,
                 fg=ACCENT, padx=20).pack(side=tk.LEFT)
        tk.Label(title_bar, text="MANAGER OVERVIEW",
                 font=("Helvetica", 10), bg=BG_HEADER,
                 fg=FG_GREY, padx=20).pack(side=tk.RIGHT)

        # ── KPI strip ──────────────────────────────────────────────────────
        kpi_frame = tk.Frame(self.root, bg=BG_DARK, pady=8)
        kpi_frame.pack(fill=tk.X, padx=15)

        total_risk = int(self.df['total_risk'].sum())
        total_parts = int(self.df['total_parts'].sum())
        critical = int((self.df['weighted'] > 90).sum())
        high = int(((self.df['weighted'] > 50) & (self.df['weighted'] <= 90)).sum())

        kpis = [
            ("Total At-Risk Items", str(total_risk), RED),
            ("Total Parts Tracked", str(total_parts), ACCENT),
            ("Critical Assignees", str(critical), DARK_RED),
            ("High-Risk Assignees", str(high), AMBER),
        ]
        for label, value, colour in kpis:
            card = tk.Frame(kpi_frame, bg=BG_CARD,
                            highlightbackground=colour,
                            highlightthickness=1, padx=18, pady=10)
            card.pack(side=tk.LEFT, padx=8)
            tk.Label(card, text=value, font=("Helvetica", 22, "bold"),
                     bg=BG_CARD, fg=colour).pack()
            tk.Label(card, text=label, font=("Helvetica", 8),
                     bg=BG_CARD, fg=FG_GREY).pack()

        # ── Main split: table left, charts right ───────────────────────────
        body = tk.Frame(self.root, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # ── Table ──────────────────────────────────────────────────────────
        table_frame = tk.Frame(body, bg=BG_CARD,
                               highlightbackground=ACCENT,
                               highlightthickness=1)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(table_frame, text="Assignee At-Risk Breakdown",
                 font=("Helvetica", 10, "bold"),
                 bg=BG_CARD, fg=ACCENT, pady=6).pack()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Manager.Treeview",
                        background=BG_MID,
                        foreground=FG_WHITE,
                        fieldbackground=BG_MID,
                        rowheight=28,
                        font=("Helvetica", 9))
        style.configure("Manager.Treeview.Heading",
                        background=BG_HEADER,
                        foreground=ACCENT,
                        font=("Helvetica", 9, "bold"),
                        relief="flat")
        style.map("Manager.Treeview",
                  background=[("selected", "#1E3A5F")])

        cols = ("Person",
                "Quality\nAt-Risk", "Supplier\nAt-Risk", "Timing\nAt-Risk",
                "Total\nAt-Risk", "Total\nParts", "Rating")
        col_keys = ("Person", "q_risk", "s_risk", "t_risk",
                    "total_risk", "total_parts", "rating_label")
        col_widths = (130, 90, 90, 90, 90, 90, 110)

        scroll_y = tk.Scrollbar(table_frame, orient=tk.VERTICAL,
                                bg=BG_CARD, troughcolor=BG_DARK)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                 style="Manager.Treeview",
                                 yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        for col, width in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center", minwidth=60)

        # Row tags per rating
        self.tree.tag_configure('critical', background='#3D0000', foreground=FG_WHITE)
        self.tree.tag_configure('high', background='#2D1500', foreground=FG_WHITE)
        self.tree.tag_configure('moderate', background='#2D2500', foreground=FG_WHITE)
        self.tree.tag_configure('good', background='#0D1F0D', foreground=FG_WHITE)
        self.tree.tag_configure('excellent', background=BG_MID, foreground=FG_WHITE)

        tag_map = {
            "✖ Critical": "critical",
            "▲ High Risk": "high",
            "● Moderate": "moderate",
            "✔ Good": "good",
            "✦ Excellent": "excellent",
        }

        for _, row in self.df.iterrows():
            values = tuple(row[k] for k in col_keys)
            tag = tag_map.get(row['rating_label'], '')
            self.tree.insert("", "end", values=values, tags=(tag,))

        self.tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # ── Charts panel ───────────────────────────────────────────────────
        chart_panel = tk.Frame(body, bg=BG_DARK)
        chart_panel.pack(side=tk.LEFT, fill=tk.BOTH)

        self._build_bar_chart(chart_panel)
        self._build_breakdown_chart(chart_panel)

    def _build_bar_chart(self, parent):
        """Horizontal bar — total at-risk per person, coloured by rating."""
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=ACCENT, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        fig = Figure(figsize=(4.8, 4.0), facecolor=BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_DARK)

        df = self.df.sort_values('total_risk')
        colours = [r for r in df['rating_colour']]

        bars = ax.barh(df['Person'], df['total_risk'],
                       color=colours, height=0.6, edgecolor='none')

        # Value labels
        for bar, val in zip(bars, df['total_risk']):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    str(val), va='center', ha='left',
                    fontsize=8, color=FG_WHITE)

        ax.set_xlabel("Total At-Risk Items", color=FG_GREY, fontsize=8)
        ax.set_title("At-Risk Count per Assignee", color=FG_WHITE,
                     fontsize=9, fontweight='bold', pad=8)
        ax.tick_params(colors=FG_WHITE, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#222222')
        ax.set_xlim(0, df['total_risk'].max() * 1.18)
        ax.xaxis.label.set_color(FG_GREY)
        ax.grid(axis='x', color='#222222', linewidth=0.5, linestyle='--')
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _build_breakdown_chart(self, parent):
        """Stacked bar — Quality / Supplier / Timing at-risk per person."""
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=ACCENT, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        fig = Figure(figsize=(4.8, 3.6), facecolor=BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_DARK)

        df = self.df.sort_values('weighted', ascending=False)
        x = np.arange(len(df))
        w = 0.55

        b1 = ax.bar(x, df['q_risk'], width=w, label='Quality', color='#00BFFF', edgecolor='none')
        b2 = ax.bar(x, df['s_risk'], width=w, bottom=df['q_risk'],
                    label='Supplier', color='#FFD700', edgecolor='none')
        b3 = ax.bar(x, df['t_risk'], width=w,
                    bottom=df['q_risk'] + df['s_risk'],
                    label='Timing', color='#FF4500', edgecolor='none')

        ax.set_xticks(x)
        ax.set_xticklabels(df['Person'], rotation=35, ha='right',
                           fontsize=7, color=FG_WHITE)
        ax.tick_params(axis='y', colors=FG_WHITE, labelsize=7)
        ax.set_ylabel("At-Risk Count", color=FG_GREY, fontsize=8)
        ax.set_title("At-Risk Breakdown by Source", color=FG_WHITE,
                     fontsize=9, fontweight='bold', pad=8)
        ax.legend(fontsize=7, frameon=False, labelcolor=FG_WHITE,
                  loc='upper right')
        for spine in ax.spines.values():
            spine.set_edgecolor('#222222')
        ax.grid(axis='y', color='#222222', linewidth=0.5, linestyle='--')
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run(self):
        if self._standalone:
            self.root.mainloop()


if __name__ == "__main__":
    app = ManagerDashboard()
    app.run()