"""
Feature Readiness Dashboard
============================
A Tkinter GUI dashboard for visualising platform milestone readiness data.
 
Usage:
    python feature_readiness_dashboard.py
    python feature_readiness_dashboard.py path/to/your_data.xlsx
 
Requirements:
    pip install pandas openpyxl matplotlib
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
import numpy as np
import sys
import os

# ─────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────
PALETTE = {
    "bg": "#0d0f14",
    "surface": "#13161e",
    "surface2": "#1a1e2a",
    "border": "#252a38",
    "text": "#e2e8f0",
    "muted": "#64748b",
    "accent": "#6366f1",
    "ready": "#22c55e",
    "partial": "#f59e0b",
    "not_ready": "#ef4444",
    "ready_a": "#22c55e99",
    "partial_a": "#f59e0b99",
    "not_ready_a": "#ef444499",
}

STATUS_COLOURS = {
    "Ready": PALETTE["ready"],
    "Partial": PALETTE["partial"],
    "Not Ready": PALETTE["not_ready"],
}

VALID_PLATFORMS = [
    "PLATFORM_NEXUS", "PLATFORM_AXIS", "PLATFORM_VEGA", "PLATFORM_DELTA",
    "PLATFORM_PULSE", "PLATFORM_ARCTIC", "PLATFORM_SIERRA", "PLATFORM_SAHARA",
    "PLATFORM_POLAR", "PLATFORM_TERRA",
]
VALID_BASELINE_STATUSES = ["Ready", "Partial", "Not Ready", "On Track", "At Risk"]
VALID_MILESTONE_STATUSES = ["Achieved", "In Progress", "Not Achieved", "At Risk", "Delayed"]
TODAY = datetime(2026, 4, 23)


# ─────────────────────────────────────────────
# Data loader
# ─────────────────────────────────────────────
def _parse_date(val) -> datetime | None:
    if pd.isna(val):
        return None
    s = str(val).strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10] if len(s) > 10 else s, fmt)
        except ValueError:
            pass
    return None


EXCEL_FILENAME = "Data Set Examples_Main.xlsx"
SHEET_NAME = "Feature readiness"


def load_feature_data(path: str | None = None) -> pd.DataFrame:
    """Load and clean the Feature readiness sheet from the Excel workbook.

    If *path* is not supplied the file is looked for in the same directory
    as this script using EXCEL_FILENAME.
    """
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_FILENAME)
    df = pd.read_excel(path, sheet_name=SHEET_NAME)
    df = df[
        df["Platform_Name"].isin(VALID_PLATFORMS) &
        df["Milestone_Baseline_Status"].isin(VALID_BASELINE_STATUSES)
        ].copy()
    df["Target_Date"] = df["Target_Milestone_Date"].apply(_parse_date)
    df["Assessment_Date_Parsed"] = df["Assessment_Date"].apply(_parse_date)
    df["Days_Until_Target"] = df["Target_Date"].apply(
        lambda x: int((x - TODAY).days) if x else None
    )
    return df.reset_index(drop=True)


# ─────────────────────────────────────────────
# Matplotlib helper – dark axes preset
# ─────────────────────────────────────────────
def _dark_axes(ax):
    ax.set_facecolor(PALETTE["surface2"])
    ax.tick_params(colors=PALETTE["muted"], labelsize=8)
    ax.xaxis.label.set_color(PALETTE["muted"])
    ax.yaxis.label.set_color(PALETTE["muted"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["border"])
    ax.grid(axis="y", color=PALETTE["border"], linewidth=0.5, linestyle="--")
    ax.set_axisbelow(True)


# ─────────────────────────────────────────────
# Main Dashboard class
# ─────────────────────────────────────────────
class Dashboard:
    """
    Tkinter GUI dashboard for Feature Readiness data.

    Parameters
    ----------
    excel_path : str, optional
        Path to the Excel workbook.  If omitted a file-dialog is shown.
    """

    def __init__(self, master, excel_path: str | None = None):
        self._data_all: pd.DataFrame = pd.DataFrame()
        self._data: pd.DataFrame = pd.DataFrame()

        # ── root window ──────────────────────────────────────────────
        self.root = master
        self.root.title("Feature Readiness Dashboard")
        self.root.configure(bg=PALETTE["bg"])
        self.root.geometry("1440x900")
        self.root.minsize(1100, 750)

        # filter state
        self._filter_platform = tk.StringVar(value="All Platforms")
        self._filter_baseline_status = tk.StringVar(value="All Baseline Statuses")
        self._filter_milestone_status = tk.StringVar(value="All Milestone Statuses")
        self._filter_programme = tk.StringVar(value="All Programmes")

        self._build_ui()

        # load data – use supplied path, or default EXCEL_FILENAME next to this script
        self._load(excel_path)

        self.root.mainloop()

    # ─────────────────────────────────────────
    # File loading
    # ─────────────────────────────────────────
    def _ask_for_file(self) -> str | None:
        return filedialog.askopenfilename(
            title="Select Feature Readiness Excel file",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls")],
        )

    def _load(self, path: str | None = None):
        try:
            self._data_all = load_feature_data(path)
        except FileNotFoundError:
            # Fall back to file dialog if the default file isn't found
            path = self._ask_for_file()
            if not path:
                messagebox.showwarning("No file", "No Excel file selected. Exiting.")
                self.root.destroy()
                return
            try:
                self._data_all = load_feature_data(path)
            except Exception as exc:
                messagebox.showerror("Load error", str(exc))
                return
        except Exception as exc:
            messagebox.showerror("Load error", str(exc))
            return
        self._populate_filter_menus()
        self._apply_filters()

    # ─────────────────────────────────────────
    # UI build
    # ─────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_filter_bar()
        self._build_kpi_bar()
        self._build_body()

    # ── header ───────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=PALETTE["surface"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Button(
            hdr, text="← Back",
            bg=PALETTE["surface"], fg=PALETTE["accent"],
            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2",
            activebackground=PALETTE["surface2"], activeforeground=PALETTE["text"],
            command=self.root.destroy, padx=10, pady=4,
        ).pack(side="left", padx=(12, 0), pady=10)

        tk.Label(
            hdr, text="Feature Readiness Dashboard",
            bg=PALETTE["surface"], fg=PALETTE["text"],
            font=("Helvetica", 16, "bold"),
        ).pack(side="left", padx=24, pady=14)

        tk.Label(
            hdr, text="Platform Milestone Tracking · Baseline Status Analysis",
            bg=PALETTE["surface"], fg=PALETTE["muted"],
            font=("Courier", 10),
        ).pack(side="left", padx=0, pady=14)

        badge = tk.Label(
            hdr, text=f"● LIVE · {TODAY.strftime('%d %b %Y').upper()}",
            bg=PALETTE["surface"], fg=PALETTE["ready"],
            font=("Courier", 10),
        )
        badge.pack(side="right", padx=24)

        # open file button
        tk.Button(
            hdr, text="📂  Open File",
            bg=PALETTE["surface2"], fg=PALETTE["text"],
            font=("Helvetica", 10), relief="flat", cursor="hand2",
            activebackground=PALETTE["accent"], activeforeground="#fff",
            command=self._on_open_file, padx=10, pady=4,
        ).pack(side="right", padx=8)

        tk.Frame(self.root, bg=PALETTE["border"], height=1).pack(fill="x")

    # ── filter bar ───────────────────────────
    def _build_filter_bar(self):
        bar = tk.Frame(self.root, bg=PALETTE["surface"], pady=10)
        bar.pack(fill="x")

        def lbl(text):
            tk.Label(bar, text=text, bg=PALETTE["surface"], fg=PALETTE["muted"],
                     font=("Courier", 9)).pack(side="left", padx=(16, 4))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.TCombobox",
            fieldbackground=PALETTE["surface2"],
            background=PALETTE["surface2"],
            foreground=PALETTE["text"],
            selectbackground=PALETTE["accent"],
            selectforeground="#fff",
            arrowcolor=PALETTE["muted"],
            bordercolor=PALETTE["border"],
        )

        def combo(var, width=20):
            cb = ttk.Combobox(bar, textvariable=var, state="readonly",
                              width=width, style="Dark.TCombobox", font=("Helvetica", 10))
            cb.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())
            cb.pack(side="left", padx=4)
            return cb

        lbl("FILTERS")
        self._cb_platform = combo(self._filter_platform, 18)
        lbl("BASELINE STATUS")
        self._cb_baseline_status = combo(self._filter_baseline_status, 18)
        lbl("MILESTONE STATUS")
        self._cb_milestone_status = combo(self._filter_milestone_status, 18)
        lbl("PROGRAMME")
        self._cb_programme = combo(self._filter_programme, 14)

        tk.Button(
            bar, text="↺ Reset",
            bg=PALETTE["surface2"], fg=PALETTE["muted"],
            font=("Courier", 9), relief="flat", cursor="hand2",
            activebackground=PALETTE["border"], activeforeground=PALETTE["text"],
            command=self._reset_filters, padx=8, pady=3,
        ).pack(side="left", padx=12)

        tk.Frame(self.root, bg=PALETTE["border"], height=1).pack(fill="x")

    def _populate_filter_menus(self):
        platforms = ["All Platforms"] + sorted(self._data_all["Platform_Name"].unique())
        baseline_stats = ["All Baseline Statuses"] + VALID_BASELINE_STATUSES
        milestone_stats = ["All Milestone Statuses"] + VALID_MILESTONE_STATUSES
        programmes = ["All Programmes"] + sorted(self._data_all["Programme_Name"].unique())
        self._cb_platform["values"] = platforms
        self._cb_baseline_status["values"] = baseline_stats
        self._cb_milestone_status["values"] = milestone_stats
        self._cb_programme["values"] = programmes

    # ── KPI bar ──────────────────────────────
    def _build_kpi_bar(self):
        self._kpi_frame = tk.Frame(self.root, bg=PALETTE["border"])
        self._kpi_frame.pack(fill="x")
        self._kpi_labels: dict[str, tk.Label] = {}
        self._kpi_sub_labels: dict[str, tk.Label] = {}
        self._kpi_bars: dict[str, tk.Canvas] = {}

        kpis = [
            ("total", "Total Milestones", PALETTE["accent"]),
            ("ready", "Ready", PALETTE["ready"]),
            ("partial", "Partial", PALETTE["partial"]),
            ("notready", "Not Ready", PALETTE["not_ready"]),
            ("overdue", "Overdue Platforms", PALETTE["not_ready"]),
            ("rate", "Readiness Rate", PALETTE["accent"]),
        ]
        for i, (key, label, colour) in enumerate(kpis):
            card = tk.Frame(self._kpi_frame, bg=PALETTE["surface"], padx=18, pady=12)
            card.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            self._kpi_frame.columnconfigure(i, weight=1)

            tk.Label(card, text=label, bg=PALETTE["surface"], fg=PALETTE["muted"],
                     font=("Courier", 8)).pack(anchor="w")

            val_lbl = tk.Label(card, text="—", bg=PALETTE["surface"], fg=colour,
                               font=("Helvetica", 24, "bold"))
            val_lbl.pack(anchor="w")
            self._kpi_labels[key] = val_lbl

            sub_lbl = tk.Label(card, text="", bg=PALETTE["surface"], fg=PALETTE["muted"],
                               font=("Helvetica", 9))
            sub_lbl.pack(anchor="w")
            self._kpi_sub_labels[key] = sub_lbl

            bar_canvas = tk.Canvas(card, bg=PALETTE["surface"], height=3,
                                   highlightthickness=0, bd=0)
            bar_canvas.pack(fill="x", pady=(4, 0))
            self._kpi_bars[key] = (bar_canvas, colour)

        tk.Frame(self.root, bg=PALETTE["border"], height=1).pack(fill="x")

    def _update_kpis(self):
        df = self._data
        total = len(df)
        ready = (df["Milestone_Baseline_Status"] == "Ready").sum()
        partial = (df["Milestone_Baseline_Status"] == "Partial").sum()
        notready = (df["Milestone_Baseline_Status"] == "Not Ready").sum()
        overdue = df[
            df["Days_Until_Target"].notna() &
            (df["Days_Until_Target"] < 0) &
            (df["Milestone_Baseline_Status"] != "Ready")
            ]["Platform_Name"].nunique()
        rate = round(ready / total * 100) if total else 0

        def _pct(n): return f"{round(n / total * 100)}% of total" if total else "—"

        self._kpi_labels["total"].config(text=str(total))
        self._kpi_labels["ready"].config(text=str(ready))
        self._kpi_labels["partial"].config(text=str(partial))
        self._kpi_labels["notready"].config(text=str(notready))
        self._kpi_labels["overdue"].config(text=str(overdue))
        self._kpi_labels["rate"].config(text=f"{rate}%")

        self._kpi_sub_labels["total"].config(text="Across all platforms")
        self._kpi_sub_labels["ready"].config(text=_pct(ready))
        self._kpi_sub_labels["partial"].config(text=_pct(partial))
        self._kpi_sub_labels["notready"].config(text=_pct(notready))
        self._kpi_sub_labels["overdue"].config(text="Platforms past target")
        self._kpi_sub_labels["rate"].config(text="Ready / Total")

        fracs = {
            "total": 1.0, "ready": ready / total if total else 0,
            "partial": partial / total if total else 0,
            "notready": notready / total if total else 0,
            "overdue": min(overdue / 10, 1.0), "rate": rate / 100,
        }
        for key, (canvas, colour) in self._kpi_bars.items():
            canvas.update_idletasks()
            w = canvas.winfo_width() or 200
            canvas.delete("all")
            canvas.create_rectangle(0, 0, int(w * fracs[key]), 3,
                                    fill=colour, outline="")

    # ── body ─────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=PALETTE["bg"])
        body.pack(fill="both", expand=True)

        # left: charts notebook + table
        left = tk.Frame(body, bg=PALETTE["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=12)

        # right: insights
        right = tk.Frame(body, bg=PALETTE["surface"], width=300,
                         relief="flat", bd=0,
                         highlightbackground=PALETTE["border"], highlightthickness=1)
        right.pack(side="right", fill="y", padx=(0, 12), pady=12)
        right.pack_propagate(False)
        self._build_insights_panel(right)

        # charts 2×2 grid
        charts_frame = tk.Frame(left, bg=PALETTE["bg"])
        charts_frame.pack(fill="both", expand=True)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.rowconfigure(1, weight=1)

        self._fig = Figure(facecolor=PALETTE["bg"])
        self._fig.subplots_adjust(hspace=0.70, wspace=0.35,
                                  left=0.06, right=0.97,
                                  top=0.95, bottom=0.14)
        self._ax_domain = self._fig.add_subplot(2, 2, 1)
        self._ax_stacked = self._fig.add_subplot(2, 2, 2)
        self._ax_days = self._fig.add_subplot(2, 2, 3)
        self._ax_dist = self._fig.add_subplot(2, 2, 4)

        self._canvas = FigureCanvasTkAgg(self._fig, master=left)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # table
        self._build_table(left)

    # ── insights panel ───────────────────────
    def _build_insights_panel(self, parent):
        tk.Label(
            parent, text="⚡  Key Insights",
            bg=PALETTE["surface"], fg=PALETTE["text"],
            font=("Helvetica", 12, "bold"), anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 0))

        tk.Frame(parent, bg=PALETTE["border"], height=1).pack(fill="x", pady=8)

        self._insights_frame = tk.Frame(parent, bg=PALETTE["surface"])
        self._insights_frame.pack(fill="both", expand=True, padx=10, pady=0)

    def _update_insights(self):
        for w in self._insights_frame.winfo_children():
            w.destroy()

        df = self._data
        insights = []

        # overdue + not ready
        overdue_plats = df[
            df["Days_Until_Target"].notna() &
            (df["Days_Until_Target"] < 0) &
            (df["Milestone_Baseline_Status"] == "Not Ready")
            ]["Platform_Name"].apply(lambda x: x.replace("PLATFORM_", "")).unique()
        if len(overdue_plats):
            insights.append(("⚠ CRITICAL", PALETTE["not_ready"],
                             f"{', '.join(overdue_plats)} {'is' if len(overdue_plats) == 1 else 'are'} overdue with Not Ready status — immediate action required."))

        # partial
        partial_count = (df["Milestone_Baseline_Status"] == "Partial").sum()
        if partial_count:
            insights.append(("🔶 WATCH", PALETTE["partial"],
                             f"{partial_count} milestone{'s' if partial_count > 1 else ''} are Partial — review integration gaps before next gate."))

        # readiness rate
        total = len(df)
        ready = (df["Milestone_Baseline_Status"] == "Ready").sum()
        rate = round(ready / total * 100) if total else 0
        if rate >= 30:
            insights.append(("✅ POSITIVE", PALETTE["ready"],
                             f"{rate}% readiness rate achieved across selected scope."))

        # not-ready domains
        nr_domains = df[df["Milestone_Baseline_Status"] == "Not Ready"]["Domain"].unique()
        if len(nr_domains):
            shown = ", ".join(nr_domains[:4])
            extra = f" +{len(nr_domains) - 4} more" if len(nr_domains) > 4 else ""
            insights.append(("🔴 NOT READY DOMAINS", PALETTE["not_ready"],
                             f"{shown}{extra} have unresolved Not Ready status."))

        if not insights:
            insights.append(("✅ ALL CLEAR", PALETTE["ready"],
                             "No critical issues in current filter selection."))

        for badge, colour, text in insights:
            card = tk.Frame(self._insights_frame, bg=PALETTE["surface2"],
                            highlightbackground=colour, highlightthickness=2,
                            bd=0)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=badge, bg=PALETTE["surface2"], fg=colour,
                     font=("Courier", 8, "bold"), anchor="w").pack(fill="x", padx=8, pady=(6, 0))
            tk.Label(card, text=text, bg=PALETTE["surface2"], fg=PALETTE["text"],
                     font=("Helvetica", 9), wraplength=240, justify="left",
                     anchor="w").pack(fill="x", padx=8, pady=(2, 8))

    # ── table ────────────────────────────────
    def _build_table(self, parent):
        frame = tk.Frame(parent, bg=PALETTE["surface"],
                         highlightbackground=PALETTE["border"], highlightthickness=1)
        frame.pack(fill="x", pady=(8, 0))

        header_row = tk.Frame(frame, bg=PALETTE["surface2"])
        header_row.pack(fill="x")

        tk.Label(header_row, text="Milestone Detail", bg=PALETTE["surface2"],
                 fg=PALETTE["text"], font=("Helvetica", 11, "bold"),
                 anchor="w").pack(side="left", padx=14, pady=8)
        self._table_count_lbl = tk.Label(header_row, text="", bg=PALETTE["surface2"],
                                         fg=PALETTE["muted"], font=("Courier", 9))
        self._table_count_lbl.pack(side="right", padx=14)

        cols = ("Platform", "Programme", "Domain", "Status", "Target Date", "Days")
        style = ttk.Style()
        style.configure("Dark.Treeview",
                        background=PALETTE["surface"],
                        fieldbackground=PALETTE["surface"],
                        foreground=PALETTE["text"],
                        rowheight=24,
                        bordercolor=PALETTE["border"],
                        font=("Helvetica", 10))
        style.configure("Dark.Treeview.Heading",
                        background=PALETTE["surface2"],
                        foreground=PALETTE["muted"],
                        font=("Courier", 9, "bold"),
                        relief="flat")
        style.map("Dark.Treeview", background=[("selected", PALETTE["accent"])])

        tree_frame = tk.Frame(frame, bg=PALETTE["surface"])
        tree_frame.pack(fill="x")

        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  height=6, style="Dark.Treeview")
        widths = [120, 110, 140, 90, 100, 70]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")

        # row tags
        self._tree.tag_configure("ready", foreground=PALETTE["ready"])
        self._tree.tag_configure("partial", foreground=PALETTE["partial"])
        self._tree.tag_configure("notready", foreground=PALETTE["not_ready"])
        self._tree.tag_configure("overdue", foreground=PALETTE["not_ready"])

    def _update_table(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        df = self._data
        self._table_count_lbl.config(text=f"{len(df)} records")
        for _, r in df.iterrows():
            status = r["Milestone_Baseline_Status"]
            tag = {"Ready": "ready", "Partial": "partial", "Not Ready": "notready"}.get(status, "")
            days = r["Days_Until_Target"]
            days_str = f"{int(days):+d}d" if pd.notna(days) else "—"
            if pd.notna(days) and days < 0:
                tag = "overdue"
            date_str = r["Target_Date"].strftime("%d %b %Y") if r["Target_Date"] else "—"
            self._tree.insert("", "end", values=(
                r["Platform_Name"].replace("PLATFORM_", ""),
                r["Programme_Name"],
                r["Domain"],
                status,
                date_str,
                days_str,
            ), tags=(tag,))

    # ─────────────────────────────────────────
    # Filter logic
    # ─────────────────────────────────────────
    def _apply_filters(self):
        df = self._data_all.copy()
        pf = self._filter_platform.get()
        bf = self._filter_baseline_status.get()
        mf = self._filter_milestone_status.get()
        gf = self._filter_programme.get()
        if pf != "All Platforms":
            df = df[df["Platform_Name"] == pf]
        if bf != "All Baseline Statuses":
            df = df[df["Milestone_Baseline_Status"] == bf]
        if mf != "All Milestone Statuses":
            df = df[df["Milestone_Status"] == mf]
        if gf != "All Programmes":
            df = df[df["Programme_Name"] == gf]
        self._data = df.reset_index(drop=True)
        self._refresh()

    def _reset_filters(self):
        self._filter_platform.set("All Platforms")
        self._filter_baseline_status.set("All Baseline Statuses")
        self._filter_milestone_status.set("All Milestone Statuses")
        self._filter_programme.set("All Programmes")
        self._apply_filters()

    # ─────────────────────────────────────────
    # Refresh all widgets
    # ─────────────────────────────────────────
    def _refresh(self):
        self._update_kpis()
        self._draw_charts()
        self._update_table()
        self._update_insights()

    # ─────────────────────────────────────────
    # Chart drawing
    # ─────────────────────────────────────────
    def _draw_charts(self):
        for ax in (self._ax_domain, self._ax_stacked, self._ax_days, self._ax_dist):
            ax.clear()
        self._draw_domain_chart()
        self._draw_platform_stacked_chart()
        self._draw_days_chart()
        self._draw_distribution_chart()
        self._canvas.draw_idle()

    # Chart 1 – milestones per domain grouped by status
    def _draw_domain_chart(self):
        ax = self._ax_domain
        _dark_axes(ax)
        df = self._data
        domains = sorted(df["Domain"].unique())
        if not domains:
            ax.set_title("Milestones per Domain", color=PALETTE["text"], fontsize=9)
            return

        x = np.arange(len(domains))
        width = 0.25
        offsets = {"Not Ready": -width, "Partial": 0, "Ready": width}

        for status, offset in offsets.items():
            counts = [df[(df["Domain"] == d) & (df["Milestone_Baseline_Status"] == status)].shape[0]
                      for d in domains]
            bars = ax.bar(x + offset, counts, width, label=status,
                          color=STATUS_COLOURS[status] + "bb",
                          edgecolor=STATUS_COLOURS[status], linewidth=0.6)

        ax.set_xticks(x)
        ax.set_xticklabels(domains, rotation=40, ha="right", fontsize=7,
                           color=PALETTE["muted"])
        ax.set_yticks(range(int(ax.get_ylim()[1]) + 2))
        ax.set_title("Milestones per Domain – Grouped by Status",
                     color=PALETTE["text"], fontsize=9, pad=6)
        ax.legend(fontsize=7, facecolor=PALETTE["surface2"], labelcolor=PALETTE["text"],
                  edgecolor=PALETTE["border"])

    # Chart 2 – platform stacked proportional
    def _draw_platform_stacked_chart(self):
        ax = self._ax_stacked
        _dark_axes(ax)
        df = self._data
        platforms = sorted(df["Platform_Name"].unique())
        if not platforms:
            ax.set_title("Platform Status Dashboard", color=PALETTE["text"], fontsize=9)
            return

        short = [p.replace("PLATFORM_", "") for p in platforms]
        bottoms = np.zeros(len(platforms))

        for status in ["Not Ready", "Partial", "Ready"]:
            vals = np.array([
                df[(df["Platform_Name"] == p)].shape[0] and
                df[(df["Platform_Name"] == p) & (df["Milestone_Baseline_Status"] == status)].shape[0] /
                df[(df["Platform_Name"] == p)].shape[0]
                for p in platforms
            ])
            ax.bar(short, vals, bottom=bottoms, label=status,
                   color=STATUS_COLOURS[status] + "bb",
                   edgecolor=STATUS_COLOURS[status], linewidth=0.6)
            bottoms += vals

        ax.set_xticklabels(short, rotation=35, ha="right", fontsize=7,
                           color=PALETTE["muted"])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v * 100)}%"))
        ax.set_ylim(0, 1)
        ax.set_title("Platform Status Dashboard", color=PALETTE["text"], fontsize=9, pad=6)
        ax.legend(fontsize=7, facecolor=PALETTE["surface2"], labelcolor=PALETTE["text"],
                  edgecolor=PALETTE["border"])

    # Chart 3 – days until target per platform
    def _draw_days_chart(self):
        ax = self._ax_days
        _dark_axes(ax)
        df = self._data
        platforms = sorted(df["Platform_Name"].unique())
        if not platforms:
            ax.set_title("Days Until Target Milestone Date", color=PALETTE["text"], fontsize=9)
            return

        short = [p.replace("PLATFORM_", "") for p in platforms]
        avg_days = []
        bar_colours = []
        for p in platforms:
            rows = df[df["Platform_Name"] == p].dropna(subset=["Days_Until_Target"])
            avg = int(rows["Days_Until_Target"].mean()) if len(rows) else 0
            avg_days.append(avg)
            nr = (rows["Milestone_Baseline_Status"] == "Not Ready").sum()
            rd = (rows["Milestone_Baseline_Status"] == "Ready").sum()
            colour = STATUS_COLOURS["Not Ready"] if nr > rd else \
                STATUS_COLOURS["Ready"] if rd > 0 else STATUS_COLOURS["Partial"]
            bar_colours.append(colour + "bb")

        ax.bar(short, avg_days, color=bar_colours,
               edgecolor=[c[:7] for c in bar_colours], linewidth=0.6)
        ax.axhline(0, color=PALETTE["accent"], linewidth=0.8, linestyle="--")
        ax.set_xticklabels(short, rotation=35, ha="right", fontsize=7, color=PALETTE["muted"])
        ax.set_title("Days Until Target (avg, colour = readiness)",
                     color=PALETTE["text"], fontsize=9, pad=6)

        legend_handles = [mpatches.Patch(color=STATUS_COLOURS[s], label=s)
                          for s in ["Ready", "Partial", "Not Ready"]]
        ax.legend(handles=legend_handles, fontsize=7, facecolor=PALETTE["surface2"],
                  labelcolor=PALETTE["text"], edgecolor=PALETTE["border"])

    # Chart 4 – overall distribution bar
    def _draw_distribution_chart(self):
        ax = self._ax_dist
        _dark_axes(ax)
        df = self._data
        counts = {s: (df["Milestone_Baseline_Status"] == s).sum() for s in ["Not Ready", "Partial", "Ready"]}

        bars = ax.bar(
            list(counts.keys()), list(counts.values()),
            color=[STATUS_COLOURS[s] + "bb" for s in counts],
            edgecolor=[STATUS_COLOURS[s] for s in counts],
            linewidth=1.2, width=0.5
        )
        for bar, val in zip(bars, counts.values()):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                        str(val), ha="center", va="bottom",
                        color=PALETTE["text"], fontsize=10, fontweight="bold")

        ax.set_xticklabels(list(counts.keys()), fontsize=9, color=PALETTE["text"])
        ax.set_title("Milestone Status Distribution", color=PALETTE["text"], fontsize=9, pad=6)
        ax.set_ylim(0, max(counts.values(), default=1) * 1.25)

    # ─────────────────────────────────────────
    # File open handler
    # ─────────────────────────────────────────
    def _on_open_file(self):
        path = self._ask_for_file()
        if path:
            self._load(path)
