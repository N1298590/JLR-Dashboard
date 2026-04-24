import tkinter as tk
from tkinter import ttk, font as tkfont
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
import seaborn as sns
import pandas as pd
import numpy as np
import os, sys

# ── Palette ─────────────────────────────────────────────────────────────────
BG = "#0D1117"
PANEL = "#161B22"
BORDER = "#21262D"
TEXT = "#E6EDF3"
TEXT_DIM = "#8B949E"
ACCENT = "#58A6FF"
GREEN = "#3FB950"
AMBER = "#D29922"
RED = "#F85149"
PURPLE = "#BC8CFF"

STATUS_COLORS = {"Approved": GREEN, "Pending": AMBER, "At Risk": RED}
PHASE_COLORS = {"Pre-Production": ACCENT, "Prototype": PURPLE, "Concept": "#FF7B72"}
ROLE_COLORS = {"Quality": "#58A6FF", "Engineering": "#3FB950",
               "Procurement": "#D29922", "Manufacturing": "#BC8CFF"}


# ── Data loading ─────────────────────────────────────────────────────────────
def load_data(path):
    raw = pd.read_excel(path, sheet_name="SUPPLIER READINESS_PSW", header=None)

    # Main PSW table: header on row 1, data rows 2-423
    psw = pd.read_excel(path, sheet_name="SUPPLIER READINESS_PSW", header=1).iloc[:422].copy()
    psw = psw[[c for c in psw.columns if not c.startswith("Unnamed")]].dropna(subset=["Programme_ID"])

    # ── FIX: coerce numeric column to float so matplotlib never sees mixed types
    psw["PSW_Variance_Days"] = pd.to_numeric(psw["PSW_Variance_Days"], errors="coerce")

    # ── FIX: ensure categorical columns are clean strings, not mixed-object series
    for col in ["PSW_Status", "Programme_Phase", "Programme_ID",
                "Approver_Role", "Approver_Name", "Vehicle_Code"]:
        if col in psw.columns:
            psw[col] = psw[col].astype(str).str.strip()
            psw.loc[psw[col] == "nan", col] = None

    psw = psw.dropna(subset=["PSW_Status", "Programme_ID"])

    # Weekly trend data (rows 434-487 in raw sheet)
    trend_raw = raw.iloc[434:488, [0, 1, 2]].copy()
    trend_raw.columns = ["Week", "Actual", "Forecast"]
    trend_raw = trend_raw.dropna(subset=["Week"])
    week_nums = trend_raw["Week"].astype(str).str.extract(r"(\d+)")[0]
    trend_raw = trend_raw.assign(Week_num=pd.to_numeric(week_nums, errors="coerce"))
    trend_raw = trend_raw.dropna(subset=["Week_num"])
    trend_raw["Week_num"] = trend_raw["Week_num"].astype(int)
    # ── FIX: ensure Actual and Forecast are float64
    trend_raw["Actual"] = pd.to_numeric(trend_raw["Actual"], errors="coerce")
    trend_raw["Forecast"] = pd.to_numeric(trend_raw["Forecast"], errors="coerce")
    trend_raw = trend_raw.sort_values("Week_num").reset_index(drop=True)

    return psw, trend_raw


# ── Chart helpers ─────────────────────────────────────────────────────────────
def apply_dark(ax, title="", xlabel="", ylabel="", grid_axis="y"):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    if grid_axis:
        ax.grid(axis=grid_axis, color=BORDER, linewidth=0.6, linestyle="--", alpha=0.7)
    if title:
        ax.set_title(title, color=TEXT, fontsize=9, fontweight="bold", pad=8)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT_DIM, fontsize=8)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_DIM, fontsize=8)


def kpi_bar(parent, label, value, colour, row, col):
    f = tk.Frame(parent, bg=PANEL, bd=0, highlightbackground=BORDER, highlightthickness=1)
    f.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
    tk.Label(f, text=label, bg=PANEL, fg=TEXT_DIM, font=("Courier New", 8)).pack(pady=(10, 2))
    tk.Label(f, text=str(value), bg=PANEL, fg=colour, font=("Courier New", 22, "bold")).pack()
    tk.Label(f, text=" ", bg=PANEL).pack(pady=4)
    return f


# ── Main Application ──────────────────────────────────────────────────────────
class Dashboard(tk.Frame):
    """PSW Supplier Readiness Dashboard.

    Inherits from tk.Frame so it can be safely embedded into any existing
    Tk application without conflicting with its event loop or root window.

    Standalone usage (run directly):
        root = tk.Tk()
        app = Dashboard(root, data_path="file.xlsx")
        app.pack(fill="both", expand=True)
        root.mainloop()

    Embedded usage (imported into another file):
        dash = Dashboard(master, data_path="file.xlsx")
        dash.pack(fill="both", expand=True)   # or .grid() etc.
    """

    def __init__(self, master, data_path):
        super().__init__(master, bg=BG)

        # Configure the top-level window that contains us
        win = self.winfo_toplevel()
        win.title("Supplier Readiness · PSW Dashboard")
        win.configure(bg=BG)
        win.geometry("1380x860")
        win.minsize(1100, 700)

        self.psw, self.trend = load_data(data_path)

        self._build_header()
        self._build_filters()
        self._build_kpis()
        self._build_charts()
        self._refresh()

    # ── Back button callback ──────────────────────────────────────────────────
    def on_button_click(self):
        self.master.destroy()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL, bd=0, highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", padx=12, pady=(10, 0))

        # Back button — top-left corner of the header
        tk.Button(hdr, text="◀  BACK", bg=BORDER, fg=ACCENT,
                  font=("Courier New", 8, "bold"), bd=0, padx=10, pady=6,
                  activebackground=PANEL, activeforeground=TEXT,
                  cursor="hand2",
                  command=self.on_button_click).pack(side="left", padx=(10, 4), pady=8)

        tk.Label(hdr, text="⬡ SUPPLIER READINESS", bg=PANEL, fg=ACCENT,
                 font=("Courier New", 18, "bold")).pack(side="left", padx=8, pady=10)
        tk.Label(hdr, text="PSW STATUS DASHBOARD", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 10)).pack(side="left", padx=4, pady=10)
        tk.Label(hdr, text="LIVE DATA  •  ALL PROGRAMMES", bg=PANEL, fg=TEXT_DIM,
                 font=("Courier New", 8)).pack(side="right", padx=16)

    # ── Filter bar ────────────────────────────────────────────────────────────
    def _build_filters(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=12, pady=6)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("PSW.TCombobox",
                        fieldbackground="#FFFFFF",
                        background="#FFFFFF",
                        foreground="#000000",
                        selectbackground="#FFFFFF",
                        selectforeground="#000000",
                        bordercolor=BORDER,
                        arrowcolor=ACCENT,
                        padding=3)
        style.map("PSW.TCombobox",
                  fieldbackground=[("readonly", "#FFFFFF"), ("disabled", PANEL)],
                  foreground=[("readonly", "#000000"), ("disabled", TEXT_DIM)],
                  selectbackground=[("readonly", "#FFFFFF")],
                  selectforeground=[("readonly", "#000000")])

        def lbl(text):
            tk.Label(bar, text=text, bg=BG, fg=TEXT_DIM,
                     font=("Courier New", 8)).pack(side="left", padx=(10, 2))

        programmes = ["All"] + sorted(self.psw["Programme_ID"].dropna().unique())
        phases = ["All"] + sorted(self.psw["Programme_Phase"].dropna().unique())
        statuses = ["All"] + sorted(self.psw["PSW_Status"].dropna().unique())
        roles = ["All"] + sorted(self.psw["Approver_Role"].dropna().unique())

        root = self.winfo_toplevel()
        self.prog_var = tk.StringVar(master=root, value="All")
        self.phase_var = tk.StringVar(master=root, value="All")
        self.status_var = tk.StringVar(master=root, value="All")
        self.role_var = tk.StringVar(master=root, value="All")

        for text, var, opts in [
            ("PROGRAMME", self.prog_var, programmes),
            ("PHASE", self.phase_var, phases),
            ("PSW STATUS", self.status_var, statuses),
            ("APPROVER ROLE", self.role_var, roles),
        ]:
            lbl(text)
            cb = ttk.Combobox(bar, textvariable=var, values=opts, width=16,
                              style="PSW.TCombobox", state="readonly")
            cb.pack(side="left", padx=2)
            cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Button(bar, text="RESET", bg=BORDER, fg=ACCENT,
                  font=("Courier New", 8, "bold"), bd=0, padx=10, pady=4,
                  activebackground=PANEL, activeforeground=TEXT,
                  command=self._reset_filters).pack(side="left", padx=(12, 4))

        tk.Button(bar, text="⬇  DOWNLOAD", bg=BORDER, fg=GREEN,
                  font=("Courier New", 8, "bold"), bd=0, padx=10, pady=4,
                  activebackground=PANEL, activeforeground=TEXT,
                  cursor="hand2",
                  command=self._download_excel).pack(side="left", padx=4)

    def _reset_filters(self):
        for v in (self.prog_var, self.phase_var, self.status_var, self.role_var):
            v.set("All")
        self._refresh()

    def _download_excel(self):
        """Export the currently-filtered rows (from the original PSW data) to Excel."""
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb

        # Build the same filtered dataframe that the dashboard is showing
        df = self.psw.copy()
        if self.prog_var.get() != "All":
            df = df[df["Programme_ID"] == self.prog_var.get()]
        if self.phase_var.get() != "All":
            df = df[df["Programme_Phase"] == self.phase_var.get()]
        if self.status_var.get() != "All":
            df = df[df["PSW_Status"] == self.status_var.get()]
        if self.role_var.get() != "All":
            df = df[df["Approver_Role"] == self.role_var.get()]

        if df.empty:
            mb.showwarning("No Data", "No rows match the current filters — nothing to download.")
            return

        save_path = fd.asksaveasfilename(
            title="Save filtered data as Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="PSW_Filtered_Export.xlsx",
        )
        if not save_path:
            return  # user cancelled

        try:
            df.to_excel(save_path, index=False, sheet_name="PSW Filtered Data")
            mb.showinfo("Download Complete",
                        f"Exported {len(df)} row(s) to:\n{save_path}")
        except Exception as exc:
            mb.showerror("Export Failed", str(exc))

    # ── KPI row ───────────────────────────────────────────────────────────────
    def _build_kpis(self):
        self.kpi_frame = tk.Frame(self, bg=BG)
        self.kpi_frame.pack(fill="x", padx=12, pady=(4, 0))
        for c in range(6):
            self.kpi_frame.columnconfigure(c, weight=1)

    def _update_kpis(self, df):
        for w in self.kpi_frame.winfo_children():
            w.destroy()
        total = len(df)
        approved = (df["PSW_Status"] == "Approved").sum()
        pending = (df["PSW_Status"] == "Pending").sum()
        at_risk = (df["PSW_Status"] == "At Risk").sum()
        pct_ok = f"{approved / total * 100:.1f}%" if total else "—"
        avg_var = f"{df['PSW_Variance_Days'].mean():.1f}d" if total else "—"
        kpi_bar(self.kpi_frame, "TOTAL PARTS", total, TEXT, 0, 0)
        kpi_bar(self.kpi_frame, "APPROVED", approved, GREEN, 0, 1)
        kpi_bar(self.kpi_frame, "PENDING", pending, AMBER, 0, 2)
        kpi_bar(self.kpi_frame, "AT RISK", at_risk, RED, 0, 3)
        kpi_bar(self.kpi_frame, "APPROVAL RATE", pct_ok, ACCENT, 0, 4)
        kpi_bar(self.kpi_frame, "AVG VARIANCE", avg_var, PURPLE, 0, 5)

    # ── Charts area ───────────────────────────────────────────────────────────
    def _build_charts(self):
        self.chart_frame = tk.Frame(self, bg=BG)
        self.chart_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.fig = plt.Figure(figsize=(17, 7), dpi=90, facecolor=BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_charts(self, df):
        self.fig.clf()
        gs = GridSpec(2, 4, figure=self.fig, hspace=0.45, wspace=0.38,
                      left=0.05, right=0.97, top=0.95, bottom=0.08)

        # 1 ── PSW Status donut
        ax1 = self.fig.add_subplot(gs[0, 0])
        status_counts = df["PSW_Status"].value_counts()
        colours = [STATUS_COLORS.get(s, TEXT_DIM) for s in status_counts.index]
        ax1.pie(status_counts, colors=colours, startangle=90,
                wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2))
        apply_dark(ax1, title="PSW STATUS SPLIT", grid_axis=None)
        legend_patches = [mpatches.Patch(color=STATUS_COLORS.get(s, TEXT_DIM),
                                         label=f"{s}  {v}")
                          for s, v in status_counts.items()]
        ax1.legend(handles=legend_patches, loc="lower center", ncol=1,
                   frameon=False, fontsize=7, labelcolor=TEXT,
                   bbox_to_anchor=(0.5, -0.18))

        # 2 ── Status by Programme (stacked bar)
        ax2 = self.fig.add_subplot(gs[0, 1:3])
        prog_status = (df.groupby(["Programme_ID", "PSW_Status"])
                       .size().unstack(fill_value=0))
        prog_status = prog_status.reindex(columns=["Approved", "Pending", "At Risk"],
                                          fill_value=0)
        # ── FIX: cast to plain Python int so numpy isfinite is never called on objects
        bottom = np.zeros(len(prog_status), dtype=float)
        for status, colour in zip(["Approved", "Pending", "At Risk"], [GREEN, AMBER, RED]):
            if status in prog_status.columns:
                vals = prog_status[status].values.astype(float)
                ax2.bar(prog_status.index, vals, bottom=bottom,
                        color=colour, label=status, width=0.65)
                bottom += vals
        apply_dark(ax2, title="PSW STATUS BY PROGRAMME", ylabel="Parts")
        ax2.set_xticklabels([p.replace("PRG_", "") for p in prog_status.index],
                            rotation=35, ha="right", fontsize=7, color=TEXT_DIM)
        ax2.legend(fontsize=7, frameon=False, labelcolor=TEXT,
                   loc="upper right", ncol=3)

        # 3 ── Programme Phase donut
        ax3 = self.fig.add_subplot(gs[0, 3])
        phase_counts = df["Programme_Phase"].value_counts()
        pcols = [PHASE_COLORS.get(p, TEXT_DIM) for p in phase_counts.index]
        ax3.pie(phase_counts, colors=pcols, startangle=90,
                wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2))
        apply_dark(ax3, title="PROGRAMME PHASE", grid_axis=None)
        leg2 = [mpatches.Patch(color=PHASE_COLORS.get(p, TEXT_DIM), label=f"{p}  {v}")
                for p, v in phase_counts.items()]
        ax3.legend(handles=leg2, loc="lower center", ncol=1, frameon=False,
                   fontsize=7, labelcolor=TEXT, bbox_to_anchor=(0.5, -0.22))

        # 4 ── Variance distribution (violin + strip)
        ax4 = self.fig.add_subplot(gs[1, 0])
        # ── FIX: explicitly cast to float64 before passing to seaborn
        var_data = df[["PSW_Status", "PSW_Variance_Days"]].copy()
        var_data["PSW_Variance_Days"] = var_data["PSW_Variance_Days"].astype(float)
        var_data = var_data.dropna()
        if not var_data.empty:
            statuses_present = var_data["PSW_Status"].unique()
            pal = {s: STATUS_COLORS.get(s, TEXT_DIM) for s in statuses_present}
            order = [s for s in ["Approved", "Pending", "At Risk"] if s in statuses_present]
            sns.violinplot(data=var_data, x="PSW_Status", y="PSW_Variance_Days",
                           hue="PSW_Status", palette=pal, inner=None, ax=ax4,
                           linewidth=0.8, order=order, legend=False)
            sns.stripplot(data=var_data, x="PSW_Status", y="PSW_Variance_Days",
                          hue="PSW_Status", palette=pal, ax=ax4, size=2.5,
                          alpha=0.5, jitter=True, order=order, legend=False)
        apply_dark(ax4, title="VARIANCE DISTRIBUTION", ylabel="Variance Days", xlabel="")
        ax4.set_xticklabels(ax4.get_xticklabels(), color=TEXT_DIM, fontsize=7)
        ax4.axhline(0, color=TEXT_DIM, linewidth=0.7, linestyle="--", alpha=0.5)

        # 5 ── Approver role horizontal bar
        ax5 = self.fig.add_subplot(gs[1, 1])
        role_counts = df["Approver_Role"].value_counts()
        rcols = [ROLE_COLORS.get(r, TEXT_DIM) for r in role_counts.index]
        # ── FIX: cast values to float
        role_vals = role_counts.values.astype(float)
        bars = ax5.barh(role_counts.index, role_vals, color=rcols, height=0.6)
        apply_dark(ax5, title="PARTS BY APPROVER ROLE", xlabel="Count", grid_axis="x")
        ax5.tick_params(axis="y", labelsize=7, colors=TEXT_DIM)
        for bar, val in zip(bars, role_vals):
            ax5.text(val + 1, bar.get_y() + bar.get_height() / 2,
                     str(int(val)), va="center", color=TEXT_DIM, fontsize=7)

        # 6 ── Weekly trend line chart
        ax6 = self.fig.add_subplot(gs[1, 2:])
        tr = self.trend.copy()
        # ── FIX: ensure both series are float64 numpy arrays
        weeks = tr["Week_num"].values.astype(float)
        actual = tr["Actual"].values.astype(float)
        forecast = tr["Forecast"].values.astype(float)

        ax6.fill_between(weeks, actual, alpha=0.15, color=GREEN)
        ax6.fill_between(weeks, forecast, alpha=0.10, color=ACCENT)
        ax6.plot(weeks, actual, color=GREEN, linewidth=1.8, label="Actual")
        ax6.plot(weeks, forecast, color=ACCENT, linewidth=1.4,
                 linestyle="--", label="Forecast")

        # Highlight last non-NaN actual point
        valid_mask = ~np.isnan(actual)
        if valid_mask.any():
            last_idx = np.where(valid_mask)[0][-1]
            ax6.scatter(weeks[last_idx], actual[last_idx], color=GREEN, s=50, zorder=5)
            ax6.annotate(f"{actual[last_idx]:.2f}",
                         xy=(weeks[last_idx], actual[last_idx]),
                         xytext=(5, 6), textcoords="offset points",
                         color=GREEN, fontsize=7)

        apply_dark(ax6, title="WEEKLY PSW COMPLETION RATE — ACTUAL vs FORECAST",
                   xlabel="Week", ylabel="Completion Rate")
        ax6.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=1, decimals=0))
        ax6.legend(fontsize=8, frameon=False, labelcolor=TEXT)

        self.canvas.draw()

    # ── Refresh ───────────────────────────────────────────────────────────────
    def _refresh(self):
        df = self.psw.copy()
        if self.prog_var.get() != "All": df = df[df["Programme_ID"] == self.prog_var.get()]
        if self.phase_var.get() != "All": df = df[df["Programme_Phase"] == self.phase_var.get()]
        if self.status_var.get() != "All": df = df[df["PSW_Status"] == self.status_var.get()]
        if self.role_var.get() != "All": df = df[df["Approver_Role"] == self.role_var.get()]
        self._update_kpis(df)
        self._draw_charts(df)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "Data set examples_Main.xlsx"),
            os.path.join(here, "data.xlsx"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path is None:
            import tkinter.filedialog as fd

            root = tk.Tk();
            root.withdraw()
            path = fd.askopenfilename(title="Select Excel file",
                                      filetypes=[("Excel files", "*.xlsx *.xls")])
            root.destroy()
        if not path:
            print("No data file selected. Exiting.")
            sys.exit(1)

    root = tk.Tk()
    app = Dashboard(master=root, data_path=path)
    app.pack(fill="both", expand=True)
    root.mainloop()