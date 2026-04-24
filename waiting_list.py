"""
Customer Waiting List Dashboard  —  Split Historical / Live View
================================================================
Top half  : Historical data (2023 & 2024) — complete full-year insights
Bottom half: Current year (2025) — live progress, pace tracking, projections

Both halves have independent filter bars that redraw their charts live.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
import pandas as pd
import numpy as np
import os, sys
import warnings
warnings.filterwarnings("ignore")

# ── Palette ───────────────────────────────────────────────────────────────────
C23      = "#4A90D9"
C24      = "#F5A623"
C25      = "#7ED321"
CTGT     = "#E94B3C"
BG       = "#1C1C2E"
PANEL    = "#2A2A42"
TEXT     = "#E8E8F0"
TEXT_DIM = "#8899AA"
GRID     = "#3A3A55"
ACCENT   = "#BB86FC"
TEAL     = "#00BCD4"
HIST_DIV = "#2A3A2A"
LIVE_DIV = "#1A2A3A"

TARGET_2025 = 87_000

MONTHS  = ["Jan","Feb","Mar","Apr","May","Jun",
           "Jul","Aug","Sep","Oct","Nov","Dec"]
REGIONS     = ["UK","North America","ASIA","Europe","Overseas"]
NA_AFTER    = {"UK"}
REG_COLORS  = {"UK":C23,"North America":TEAL,"ASIA":C24,"Europe":C25,"Overseas":ACCENT}

# ── Data helpers ──────────────────────────────────────────────────────────────

def parse_num(val):
    if pd.isna(val): return None
    try: return int(str(val).replace(",","").strip())
    except: return None


def load_data(path):
    raw = pd.read_excel(path, sheet_name="Customer waiting list", header=None)

    def get_weekly_std(hdr):
        rows = []
        for i in range(hdr+1, len(raw)):
            wk = parse_num(raw.iloc[i,0]); cpw = parse_num(raw.iloc[i,1]); twl = parse_num(raw.iloc[i,2])
            if wk is None: break
            rows.append({"week":wk,"cpw":cpw,"twl":twl})
        return pd.DataFrame(rows)

    def get_weekly_2025(hdr):
        rows = []
        for i in range(hdr+1, len(raw)):
            wk = parse_num(raw.iloc[i,0]); twl = parse_num(raw.iloc[i,1]); cpw = parse_num(raw.iloc[i,2])
            if wk is None: break
            rows.append({"week":wk,"cpw":cpw,"twl":twl})
        return pd.DataFrame(rows)

    wl23 = get_weekly_std(11);   wl23["year"] = 2023
    wl24 = get_weekly_std(81);   wl24["year"] = 2024
    wl25 = get_weekly_2025(148); wl25["year"] = 2025

    def extract_regional(hdr_idx):
        result = {}; last = None; empty_streak = 0
        for i in range(hdr_idx+1, len(raw)):
            row  = raw.iloc[i]
            cell = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
            norm = cell.lower()
            if norm in ("","nan"):
                mvals = [parse_num(row.iloc[c]) if c < len(row) else None for c in range(1,13)]
                has   = any(v is not None for v in mvals)
                if has and last in NA_AFTER and "North America" not in result:
                    result["North America"] = [(v or 0) for v in mvals]; last = "North America"; empty_streak = 0
                elif has and last:
                    for j,v in enumerate(mvals): result[last][j] += (v or 0)
                    empty_streak = 0
                else:
                    empty_streak += 1
                    if empty_streak >= 2 and result: break
                continue
            empty_streak = 0
            if norm == "total": break
            match = next((r for r in REGIONS if r.lower() == norm), None)
            if match is None: continue
            result[match] = [(parse_num(row.iloc[c]) or 0) if c < len(row) else 0 for c in range(1,13)]
            last = match
        return result

    reg_hdrs = raw[raw.iloc[:,0].astype(str).str.strip() == "Region"].index.tolist()
    regional = {2023: extract_regional(reg_hdrs[0]),
                2024: extract_regional(reg_hdrs[1]),
                2025: extract_regional(reg_hdrs[2])}
    return wl23, wl24, wl25, regional


def calc_stats(df):
    cpw = df["cpw"].dropna(); twl = df["twl"].dropna()
    if cpw.empty: return {k:0 for k in ["total_added","final","avg","peak_cpw","peak_wk",
                                         "min_cpw","min_wk","std","weeks",
                                         "q1_avg","q2_avg","q3_avg","q4_avg","late_avg","early_avg"]}
    return {
        "total_added": int(cpw.sum()), "final": int(twl.iloc[-1]),
        "avg": round(cpw.mean(),1),   "peak_cpw": int(cpw.max()),
        "peak_wk": int(df.loc[cpw.idxmax(),"week"]),
        "min_cpw": int(cpw.min()),    "min_wk": int(df.loc[cpw.idxmin(),"week"]),
        "std": round(cpw.std(),1),    "weeks": len(df),
        "q1_avg": round(df[df["week"].between(1,13)]["cpw"].mean(),1),
        "q2_avg": round(df[df["week"].between(14,26)]["cpw"].mean(),1),
        "q3_avg": round(df[df["week"].between(27,39)]["cpw"].mean(),1),
        "q4_avg": round(df[df["week"].between(40,52)]["cpw"].mean(),1),
        "late_avg":  round(df[df["week"]>=48]["cpw"].mean(),1),
        "early_avg": round(df[df["week"]<=47]["cpw"].mean(),1),
    }


def fmt_k(x, _=None):
    if abs(x) >= 1_000_000: return f"{x/1_000_000:.1f}M"
    if abs(x) >= 1_000:     return f"{x/1_000:.0f}K"
    return str(int(x))


def apply_dark_ax(ax):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(GRID)


def apply_mpl_style():
    plt.rcParams.update({
        "figure.facecolor":BG,"axes.facecolor":PANEL,"axes.edgecolor":GRID,
        "axes.labelcolor":TEXT,"xtick.color":TEXT,"ytick.color":TEXT,"text.color":TEXT,
        "grid.color":GRID,"grid.linestyle":"--","grid.alpha":0.45,
        "font.family":"DejaVu Sans",
        "legend.facecolor":PANEL,"legend.edgecolor":GRID,"legend.labelcolor":TEXT,
    })


def donut_arc(ax, angles, color, inner, outer, cx, cy):
    xo = cx+outer*np.cos(angles); yo = cy+outer*np.sin(angles)
    xi = cx+inner*np.cos(angles[::-1]); yi = cy+inner*np.sin(angles[::-1])
    ax.fill(np.concatenate([xo,xi]), np.concatenate([yo,yi]), color=color, zorder=3)


# ── Tk widget helpers ─────────────────────────────────────────────────────────

def section_label(parent, text, fg, bg):
    bar = tk.Frame(parent, bg=bg, highlightbackground=fg, highlightthickness=1)
    bar.pack(fill="x", padx=10, pady=(8,0))
    tk.Label(bar, text=text, bg=bg, fg=fg,
             font=("Courier New",10,"bold")).pack(side="left", padx=14, pady=5)
    return bar


def kpi_card(parent, title, value, subtitle, colour, col):
    card = tk.Frame(parent, bg=PANEL, highlightbackground=colour, highlightthickness=1)
    card.grid(row=0, column=col, padx=4, pady=5, sticky="nsew")
    tk.Label(card, text=title,    bg=PANEL, fg=TEXT_DIM, font=("Courier New",7,"bold")).pack(pady=(6,0))
    tk.Label(card, text=value,    bg=PANEL, fg=colour,   font=("Courier New",13,"bold")).pack(pady=(1,0))
    tk.Label(card, text=subtitle, bg=PANEL, fg=TEXT,     font=("Courier New",7)).pack(pady=(1,6))


def insight_bar(parent, insights, bg=BG):
    bar = tk.Frame(parent, bg=bg)
    bar.pack(fill="x", padx=10, pady=(0,3))
    for icon, text, colour in insights:
        chip = tk.Frame(bar, bg=bg); chip.pack(side="left", padx=6, pady=2)
        tk.Label(chip, text=icon, bg=bg, fg=colour, font=("Courier New",9)).pack(side="left")
        tk.Label(chip, text=text, bg=bg, fg=TEXT,   font=("Courier New",7)).pack(side="left", padx=(2,0))


def combo_style():
    s = ttk.Style()
    try: s.theme_use("clam")
    except: pass
    s.configure("WL.TCombobox", fieldbackground="#fff", background="#fff",
                foreground="#000", selectbackground="#fff", selectforeground="#000",
                bordercolor=GRID, arrowcolor=ACCENT, padding=3)
    s.map("WL.TCombobox",
          fieldbackground=[("readonly","#fff")], foreground=[("readonly","#000")],
          selectbackground=[("readonly","#fff")], selectforeground=[("readonly","#000")])


def lbl(parent, text, bg=BG):
    tk.Label(parent, text=text, bg=bg, fg=TEXT_DIM,
             font=("Courier New",8,"bold")).pack(side="left", padx=(10,3))


def sep(parent):
    tk.Label(parent, text="|", bg=BG, fg=GRID,
             font=("Courier New",12)).pack(side="left", padx=4)


def reset_btn(parent, cmd):
    tk.Button(parent, text="RESET", bg=GRID, fg=ACCENT,
              font=("Courier New",8,"bold"), bd=0, padx=8, pady=4,
              activebackground=PANEL, activeforeground=TEXT,
              cursor="hand2", command=cmd).pack(side="left", padx=10, pady=4)


# ══════════════════════════════════════════════════════════════════════════════
class WaitingListDashboard(tk.Frame):

    def __init__(self, master, data_path):
        super().__init__(master, bg=BG)
        win = self.winfo_toplevel()
        win.title("Customer Waiting List Dashboard  ·  Historical & Live 2025")
        win.configure(bg=BG)
        win.geometry("1440x1040")
        win.minsize(1200, 820)
        apply_mpl_style()
        combo_style()

        self.wl23, self.wl24, self.wl25, self.regional = load_data(data_path)
        self.s23 = calc_stats(self.wl23)
        self.s24 = calc_stats(self.wl24)
        self.s25 = calc_stats(self.wl25)
        self.yoy        = round(100*(self.s24["final"]-self.s23["final"])/self.s23["final"],1)
        self.prog_pct   = round(100*self.s25["final"]/TARGET_2025,1)
        self.shortfall  = max(0, TARGET_2025 - self.s25["final"])

        # ── Back button on the toplevel window ──────────────────────────────
        top = self.winfo_toplevel()
        back_bar = tk.Frame(top, bg=BG, pady=4)
        back_bar.pack(fill="x")
        tk.Button(
            back_bar, text="← Back",
            bg=PANEL, fg=ACCENT,
            font=("Courier New", 9, "bold"),
            relief="flat", padx=12, pady=4, cursor="hand2",
            activebackground=GRID, activeforeground=TEXT,
            command=top.destroy,
        ).pack(side="left", padx=10)
        tk.Frame(top, bg=GRID, height=1).pack(fill="x")

        self._build_scroll()
        self._build_historical_section()
        self._build_live_section()

    # ── scrollable outer container ────────────────────────────────────────────
    def _build_scroll(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)
        vscroll = tk.Scrollbar(outer, orient="vertical", bg=PANEL)
        vscroll.pack(side="right", fill="y")
        self._sc = tk.Canvas(outer, bg=BG, yscrollcommand=vscroll.set, highlightthickness=0)
        self._sc.pack(side="left", fill="both", expand=True)
        vscroll.config(command=self._sc.yview)
        self.inner = tk.Frame(self._sc, bg=BG)
        win_id = self._sc.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self._sc.configure(scrollregion=self._sc.bbox("all")))
        self._sc.bind("<Configure>", lambda e: self._sc.itemconfig(win_id, width=e.width))
        self._sc.bind_all("<MouseWheel>", lambda e: self._sc.yview_scroll(-1*(e.delta//120),"units"))

    # ══════════════════════════════════════════════════════════════════════════
    #  HISTORICAL SECTION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_historical_section(self):
        s23, s24 = self.s23, self.s24
        inner = self.inner
        win   = self.winfo_toplevel()

        section_label(inner,
            "▸  HISTORICAL DATA  ·  2023 – 2024  ·  COMPLETE FULL-YEAR RECORDS",
            C24, HIST_DIV)

        # ── KPI row ───────────────────────────────────────────────────────────
        hist_kpi = tk.Frame(inner, bg=BG)
        hist_kpi.pack(fill="x", padx=10, pady=(2,0))
        for c in range(8): hist_kpi.columnconfigure(c, weight=1)

        kpi_card(hist_kpi,"2023 FINAL TOTAL",    f"{s23['final']:,}",       f"Avg {s23['avg']:,.0f}/wk",                                           C23, 0)
        kpi_card(hist_kpi,"2023 PEAK WEEK",       f"Wk {s23['peak_wk']}",   f"{s23['peak_cpw']:,} customers",                                      C23, 1)
        kpi_card(hist_kpi,"2023 Q4 DROP-OFF",     f"{((s23['late_avg']-s23['early_avg'])/s23['early_avg']*100):.0f}%", f"Wk1-47 avg {s23['early_avg']:,.0f} → Wk48-52 avg {s23['late_avg']:,.0f}", C23, 2)
        kpi_card(hist_kpi,"2024 FINAL TOTAL",     f"{s24['final']:,}",       f"Avg {s24['avg']:,.0f}/wk",                                           C24, 3)
        kpi_card(hist_kpi,"2024 PEAK WEEK",       f"Wk {s24['peak_wk']}",   f"{s24['peak_cpw']:,} customers",                                      C24, 4)
        kpi_card(hist_kpi,"2024 Q4 DROP-OFF",     f"{((s24['late_avg']-s24['early_avg'])/s24['early_avg']*100):.0f}%", f"Wk1-47 avg {s24['early_avg']:,.0f} → Wk48-52 avg {s24['late_avg']:,.0f}", C24, 5)
        kpi_card(hist_kpi,"YoY GROWTH",           f"+{self.yoy}%",           "2023 → 2024 final total",                                             TEAL, 6)
        kpi_card(hist_kpi,"AVG WEEKLY UPLIFT",    f"+{s24['avg']-s23['avg']:,.0f}", "extra customers/wk in 2024 vs 2023",                           TEAL, 7)

        insight_bar(inner, [
            ("▲", f"10.1% YoY growth 2023→2024 ({s23['final']:,} → {s24['final']:,})", C24),
            ("⚠", f"Severe Q4 drop: −61% in 2023, −84% in 2024 (Wks 48–52)",           CTGT),
            ("◆", f"2024 peak {s24['peak_cpw']:,}/wk — 13.4% higher than 2023 peak {s23['peak_cpw']:,}/wk", C24),
            ("●", f"2024 avg {s24['avg']:,.0f}/wk vs 2023 avg {s23['avg']:,.0f}/wk (+{s24['avg']-s23['avg']:,.0f})", C23),
        ])

        # ── Historical filter bar ─────────────────────────────────────────────
        hfbar = tk.Frame(inner, bg=BG, highlightbackground=GRID, highlightthickness=1)
        hfbar.pack(fill="x", padx=10, pady=(2,0))

        # Year checkboxes
        lbl(hfbar, "YEARS")
        self.h_year_vars = {}
        yf = tk.Frame(hfbar, bg=BG); yf.pack(side="left", padx=(0,4))
        for yr, col in [(2023,C23),(2024,C24)]:
            v = tk.BooleanVar(master=win, value=True)
            self.h_year_vars[yr] = v
            tk.Checkbutton(yf, text=str(yr), variable=v, bg=BG, fg=col,
                           selectcolor=PANEL, activebackground=BG, activeforeground=col,
                           font=("Courier New",8,"bold"),
                           command=self._refresh_historical).pack(side="left", padx=4)
        sep(hfbar)

        # Region dropdown
        lbl(hfbar, "REGION")
        self.h_region_var = tk.StringVar(master=win, value="All")
        ttk.Combobox(hfbar, textvariable=self.h_region_var,
                     values=["All"]+REGIONS, width=13, style="WL.TCombobox",
                     state="readonly").pack(side="left", padx=2)
        self.h_region_var.trace_add("write", lambda *_: self._refresh_historical())
        sep(hfbar)

        # Quarter selector
        lbl(hfbar, "QUARTER")
        self.h_quarter_var = tk.StringVar(master=win, value="Full Year")
        ttk.Combobox(hfbar, textvariable=self.h_quarter_var,
                     values=["Full Year","Q1 (Wk 1–13)","Q2 (Wk 14–26)",
                             "Q3 (Wk 27–39)","Q4 (Wk 40–52)"],
                     width=14, style="WL.TCombobox", state="readonly").pack(side="left", padx=2)
        self.h_quarter_var.trace_add("write", lambda *_: self._refresh_historical())
        sep(hfbar)

        # Chart type
        lbl(hfbar, "CHART FOCUS")
        self.h_chart_var = tk.StringVar(master=win, value="Overview")
        ttk.Combobox(hfbar, textvariable=self.h_chart_var,
                     values=["Overview","Cumulative Growth","Weekly Volume",
                             "Regional Breakdown","Quarterly Analysis","Rolling Average"],
                     width=18, style="WL.TCombobox", state="readonly").pack(side="left", padx=2)
        self.h_chart_var.trace_add("write", lambda *_: self._refresh_historical())
        sep(hfbar)

        reset_btn(hfbar, self._reset_historical)

        # ── Historical chart canvas ───────────────────────────────────────────
        self.hist_fig = plt.Figure(figsize=(18,8), dpi=90, facecolor=BG)
        hc_frame = tk.Frame(inner, bg=BG)
        hc_frame.pack(fill="x", padx=10, pady=(3,8))
        self.hist_canvas = FigureCanvasTkAgg(self.hist_fig, master=hc_frame)
        self.hist_canvas.get_tk_widget().configure(bg=BG)
        self.hist_canvas.get_tk_widget().pack(fill="x")
        self._refresh_historical()

    def _reset_historical(self):
        for v in self.h_year_vars.values(): v.set(True)
        self.h_region_var.set("All")
        self.h_quarter_var.set("Full Year")
        self.h_chart_var.set("Overview")

    def _get_hist_filtered(self):
        """Return filtered weekly dfs for the active historical years."""
        q_map = {"Full Year":(1,52),"Q1 (Wk 1–13)":(1,13),
                 "Q2 (Wk 14–26)":(14,26),"Q3 (Wk 27–39)":(27,39),"Q4 (Wk 40–52)":(40,52)}
        wk_lo, wk_hi = q_map.get(self.h_quarter_var.get(),(1,52))
        active = [yr for yr,v in self.h_year_vars.items() if v.get()]
        result = {}
        for yr, raw_df in [(2023,self.wl23),(2024,self.wl24)]:
            df = raw_df[raw_df["week"].between(wk_lo,wk_hi)].copy() if yr in active else pd.DataFrame(columns=raw_df.columns)
            result[yr] = df
        return result, active, wk_lo, wk_hi

    def _get_hist_regional(self, year):
        region = self.h_region_var.get()
        rd = self.regional.get(year,{})
        if region == "All":
            totals = [0]*12
            for vals in rd.values():
                for i,v in enumerate(vals): totals[i] += v
            return totals
        return rd.get(region,[0]*12)

    def _refresh_historical(self):
        filtered, active, wk_lo, wk_hi = self._get_hist_filtered()
        focus = self.h_chart_var.get()
        fig   = self.hist_fig
        fig.clf()

        w23 = filtered[2023]; w24 = filtered[2024]
        s23f = calc_stats(w23) if not w23.empty else self.s23
        s24f = calc_stats(w24) if not w24.empty else self.s24

        def safe(df, wk_):
            r = df[df["week"]==wk_]
            return int(r["cpw"].values[0]) if len(r) else 0

        YEAR_META = [(yr, filtered[yr],
                      s23f if yr==2023 else s24f,
                      C23  if yr==2023 else C24)
                     for yr in [2023,2024] if yr in active and not filtered[yr].empty]

        region_lbl = self.h_region_var.get()

        # ── OVERVIEW (default 2×4 grid) ───────────────────────────────────────
        if focus == "Overview":
            gs = GridSpec(2,4,figure=fig,hspace=0.52,wspace=0.35,
                          left=0.05,right=0.97,top=0.93,bottom=0.1)

            # (0,0:2) Cumulative
            ax1 = fig.add_subplot(gs[0,0:2])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    ax1.plot(df["week"],df["twl"],color=col,lw=2.2,label=str(yr))
                    ax1.fill_between(df["week"],df["twl"],alpha=0.12,color=col)
                    last=df.iloc[-1]
                    ax1.annotate(f"{int(last['twl']):,}",xy=(last["week"],last["twl"]),
                                 fontsize=8,color=col,fontweight="bold",xytext=(-28,6),textcoords="offset points")
            ax1.set_title("Cumulative Waiting List Growth",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Total Waiting List")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=8); ax1.grid(True,axis="y"); ax1.set_xlim(wk_lo,wk_hi)

            # (0,2:4) Weekly volume
            ax2 = fig.add_subplot(gs[0,2:4])
            wk_range = np.arange(wk_lo,wk_hi+1)
            n = max(len(YEAR_META),1); bw = 0.7/n
            offs = np.linspace(-(n-1)/2*bw,(n-1)/2*bw,n)
            for (yr,df,s,col),off in zip(YEAR_META,offs):
                cpw = [safe(df,k) for k in wk_range]
                ax2.bar(wk_range+off,cpw,width=bw,color=col,alpha=0.8,label=str(yr))
                if s["avg"]: ax2.axhline(s["avg"],color=col,lw=1,ls=":",alpha=0.7)
            ax2.axvspan(47.5,52.5,color=CTGT,alpha=0.07,label="Q4 drop zone")
            ax2.set_title("Weekly Volume (dotted = annual avg)",fontsize=10,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Customers / Week")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y"); ax2.set_xlim(wk_lo-0.5,wk_hi+0.5)

            # (1,0) Quarterly avg
            ax3 = fig.add_subplot(gs[1,0])
            qlabels = ["Q1\nWk1-13","Q2\nWk14-26","Q3\nWk27-39","Q4\nWk40-52"]
            x = np.arange(4); n2 = max(len(YEAR_META),1); bw2 = 0.7/n2
            offs2 = np.linspace(-(n2-1)/2*bw2,(n2-1)/2*bw2,n2)
            for (yr,df,s,col),off in zip(YEAR_META,offs2):
                qvals = [s["q1_avg"],s["q2_avg"],s["q3_avg"],s["q4_avg"]]
                ax3.bar(x+off,qvals,bw2,color=col,alpha=0.85,label=str(yr))
                for i,v in enumerate(qvals):
                    ax3.text(i+off,v+10,f"{v:.0f}",ha="center",fontsize=6.5,color=col)
            ax3.set_title("Quarterly Avg Customers/Wk",fontsize=10,fontweight="bold")
            ax3.set_xticks(x); ax3.set_xticklabels(qlabels,fontsize=8)
            ax3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax3.legend(fontsize=8); ax3.grid(True,axis="y")

            # (1,1) Regional stacked
            ax4 = fig.add_subplot(gs[1,1])
            x2 = np.arange(len([yr for yr in [2023,2024] if yr in active]))
            xlbls = [str(yr) for yr in [2023,2024] if yr in active]
            bottoms = np.zeros(len(x2))
            for reg in REGIONS:
                vals = []
                for yr in [2023,2024]:
                    if yr not in active: continue
                    rd = self.regional[yr] if region_lbl=="All" else {region_lbl: self.regional[yr].get(region_lbl,[0]*12)}
                    vals.append(sum(rd.get(reg,[0]*12)) if region_lbl=="All" else sum(self.regional[yr].get(reg,[0]*12)) if reg==region_lbl else 0)
                vals = np.array(vals,dtype=float)
                if vals.sum() == 0: continue
                ax4.bar(x2,vals,0.5,bottom=bottoms,color=REG_COLORS.get(reg,"#888"),label=reg,alpha=0.9)
                bottoms += vals
            ax4.set_title(f"Regional Totals{' — '+region_lbl if region_lbl!='All' else ''}",fontsize=10,fontweight="bold")
            ax4.set_xticks(x2); ax4.set_xticklabels(xlbls)
            ax4.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax4.legend(fontsize=7,loc="upper left"); ax4.grid(True,axis="y")

            # (1,2) 4-week rolling avg
            ax5 = fig.add_subplot(gs[1,2])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    roll = df["cpw"].rolling(4,min_periods=1).mean()
                    ax5.plot(df["week"],roll,color=col,lw=2,label=str(yr))
            ax5.set_title("4-Week Rolling Avg",fontsize=10,fontweight="bold")
            ax5.set_xlabel("Week"); ax5.set_ylabel("Avg Customers/Wk")
            ax5.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax5.legend(fontsize=8); ax5.grid(True,axis="y")

            # (1,3) YoY delta
            ax6 = fig.add_subplot(gs[1,3])
            if 2023 in active and 2024 in active and not w23.empty and not w24.empty:
                wks = np.arange(wk_lo,wk_hi+1)
                delta = [safe(w24,k)-safe(w23,k) for k in wks]
                cols  = [C24 if d>=0 else CTGT for d in delta]
                ax6.bar(wks,delta,color=cols,alpha=0.85,width=0.85)
                ax6.axhline(0,color=TEXT,lw=0.8)
                ax6.set_title("2024 vs 2023 Weekly Δ",fontsize=10,fontweight="bold")
                ax6.set_xlabel("Week"); ax6.set_ylabel("Δ Customers/Wk")
                ax6.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
                ax6.grid(True,axis="y")
            else:
                ax6.axis("off")
                ax6.text(0.5,0.5,"Select both years\nto see comparison",
                         ha="center",va="center",color=TEXT_DIM,fontsize=10,transform=ax6.transAxes)

        # ── CUMULATIVE GROWTH focused ─────────────────────────────────────────
        elif focus == "Cumulative Growth":
            gs = GridSpec(1,2,figure=fig,hspace=0.4,wspace=0.3,
                          left=0.06,right=0.97,top=0.9,bottom=0.1)
            ax1 = fig.add_subplot(gs[0,0])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    ax1.plot(df["week"],df["twl"],color=col,lw=2.5,label=str(yr))
                    ax1.fill_between(df["week"],df["twl"],alpha=0.14,color=col)
                    last=df.iloc[-1]
                    ax1.annotate(f"{int(last['twl']):,}",xy=(last["week"],last["twl"]),
                                 fontsize=9,color=col,fontweight="bold",xytext=(-30,8),textcoords="offset points")
            ax1.set_title("Cumulative Waiting List — All Weeks",fontsize=11,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Total Waiting List")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=9); ax1.grid(True,axis="y"); ax1.set_xlim(wk_lo,wk_hi)

            # Week-on-week cumulative gain
            ax2 = fig.add_subplot(gs[0,1])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    gain = df["twl"].diff().fillna(df["twl"].iloc[0])
                    ax2.plot(df["week"],gain,color=col,lw=2,label=str(yr))
                    ax2.fill_between(df["week"],gain,alpha=0.1,color=col)
            ax2.set_title("Weekly Net Gain to Waiting List",fontsize=11,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Customers Added")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=9); ax2.grid(True,axis="y"); ax2.set_xlim(wk_lo,wk_hi)

        # ── WEEKLY VOLUME focused ─────────────────────────────────────────────
        elif focus == "Weekly Volume":
            gs = GridSpec(2,2,figure=fig,hspace=0.5,wspace=0.35,
                          left=0.06,right=0.97,top=0.93,bottom=0.1)
            wk_range = np.arange(wk_lo,wk_hi+1)
            n = max(len(YEAR_META),1); bw = 0.7/n
            offs = np.linspace(-(n-1)/2*bw,(n-1)/2*bw,n)

            ax1 = fig.add_subplot(gs[0,:])
            for (yr,df,s,col),off in zip(YEAR_META,offs):
                cpw = [safe(df,k) for k in wk_range]
                ax1.bar(wk_range+off,cpw,width=bw,color=col,alpha=0.82,label=str(yr))
                if s["avg"]: ax1.axhline(s["avg"],color=col,lw=1.2,ls=":",alpha=0.8,label=f"{yr} avg")
            ax1.axvspan(47.5,52.5,color=CTGT,alpha=0.08,label="Q4 drop zone")
            ax1.set_title("Weekly Customers Added — Full View",fontsize=11,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Customers / Week")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=8,ncol=4); ax1.grid(True,axis="y"); ax1.set_xlim(wk_lo-0.5,wk_hi+0.5)

            ax2 = fig.add_subplot(gs[1,0])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    roll = df["cpw"].rolling(4,min_periods=1).mean()
                    ax2.plot(df["week"],roll,color=col,lw=2,label=str(yr))
            ax2.set_title("4-Week Rolling Average",fontsize=10,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Avg Customers/Wk")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y")

            ax3 = fig.add_subplot(gs[1,1])
            for yr,df,s,col in YEAR_META:
                if not df.empty and len(df)>1:
                    delta = df["cpw"].diff().dropna()
                    ax3.bar(df["week"].iloc[1:],delta,
                            color=[col if v>=0 else CTGT for v in delta],alpha=0.8,width=0.7,label=str(yr))
            ax3.axhline(0,color=TEXT,lw=0.8)
            ax3.set_title("Week-on-Week Volume Change",fontsize=10,fontweight="bold")
            ax3.set_xlabel("Week"); ax3.set_ylabel("Δ Customers")
            ax3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax3.legend(fontsize=8); ax3.grid(True,axis="y")

        # ── REGIONAL BREAKDOWN focused ────────────────────────────────────────
        elif focus == "Regional Breakdown":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.38,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            # Stacked bar by year
            ax1 = fig.add_subplot(gs[0,0])
            active_yrs = [yr for yr in [2023,2024] if yr in active]
            x = np.arange(len(active_yrs))
            bottoms = np.zeros(len(x))
            for reg in REGIONS:
                vals = [sum(self.regional[yr].get(reg,[0]*12)) for yr in active_yrs]
                vals = np.array(vals,dtype=float)
                if vals.sum()==0: continue
                ax1.bar(x,vals,0.55,bottom=bottoms,color=REG_COLORS.get(reg,"#888"),label=reg,alpha=0.9)
                bottoms += vals
            ax1.set_title("Annual Total by Region",fontsize=10,fontweight="bold")
            ax1.set_xticks(x); ax1.set_xticklabels([str(y) for y in active_yrs])
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=8); ax1.grid(True,axis="y")

            # Monthly breakdown for selected region
            ax2 = fig.add_subplot(gs[0,1])
            xlbls = MONTHS; x2 = np.arange(12)
            n = max(len([yr for yr in [2023,2024] if yr in active]),1); bw = 0.7/n
            offs = np.linspace(-(n-1)/2*bw,(n-1)/2*bw,n)
            regs_to_show = REGIONS if region_lbl=="All" else [region_lbl]
            idx=0
            for yr in [2023,2024]:
                if yr not in active: continue
                col = C23 if yr==2023 else C24
                monthly = [0]*12
                for reg in regs_to_show:
                    vals = self.regional[yr].get(reg,[0]*12)
                    for i,v in enumerate(vals): monthly[i] += v
                ax2.bar(x2+offs[idx],monthly,bw,color=col,alpha=0.85,label=str(yr))
                idx+=1
            rl = region_lbl if region_lbl!="All" else "All Regions"
            ax2.set_title(f"Monthly Additions — {rl}",fontsize=10,fontweight="bold")
            ax2.set_xticks(x2); ax2.set_xticklabels(xlbls,fontsize=8,rotation=30)
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y")
            ax2.set_ylabel("Customers Added")

            # Region share pie (most recent active year)
            ax3 = fig.add_subplot(gs[0,2])
            yr_for_pie = max(active) if active else 2024
            pie_vals = [sum(self.regional[yr_for_pie].get(r,[0]*12)) for r in REGIONS]
            pie_cols  = [REG_COLORS[r] for r in REGIONS]
            nonzero   = [(v,c,r) for v,c,r in zip(pie_vals,pie_cols,REGIONS) if v>0]
            if nonzero:
                pv,pc,pr = zip(*nonzero)
                wedges,texts,autotexts = ax3.pie(pv,colors=pc,startangle=90,
                    autopct="%1.1f%%",pctdistance=0.75,
                    wedgeprops=dict(width=0.55,edgecolor=BG,linewidth=2))
                for at in autotexts: at.set_fontsize(7); at.set_color(TEXT)
                ax3.legend([mpatches.Patch(color=c,label=r) for c,r in zip(pc,pr)],
                           loc="lower center",ncol=2,frameon=False,fontsize=7,
                           labelcolor=TEXT,bbox_to_anchor=(0.5,-0.15))
            ax3.set_title(f"Region Share — {yr_for_pie}",fontsize=10,fontweight="bold")

        # ── QUARTERLY ANALYSIS focused ────────────────────────────────────────
        elif focus == "Quarterly Analysis":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.38,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            ax1 = fig.add_subplot(gs[0,0])
            qlabels = ["Q1\nWk1-13","Q2\nWk14-26","Q3\nWk27-39","Q4\nWk40-52"]
            x = np.arange(4); n = max(len(YEAR_META),1); bw = 0.7/n
            offs = np.linspace(-(n-1)/2*bw,(n-1)/2*bw,n)
            for (yr,df,s,col),off in zip(YEAR_META,offs):
                qvals = [s["q1_avg"],s["q2_avg"],s["q3_avg"],s["q4_avg"]]
                ax1.bar(x+off,qvals,bw,color=col,alpha=0.85,label=str(yr))
                for i,v in enumerate(qvals):
                    ax1.text(i+off,v+10,f"{v:.0f}",ha="center",fontsize=7,color=col)
            ax1.set_title("Quarterly Avg Customers/Wk",fontsize=10,fontweight="bold")
            ax1.set_xticks(x); ax1.set_xticklabels(qlabels,fontsize=8)
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=8); ax1.grid(True,axis="y")

            # Q-to-Q change line
            ax2 = fig.add_subplot(gs[0,1])
            for yr,df,s,col in YEAR_META:
                qvals = [s["q1_avg"],s["q2_avg"],s["q3_avg"],s["q4_avg"]]
                ax2.plot([1,2,3,4],qvals,color=col,lw=2.2,marker="o",ms=7,label=str(yr))
                for i,v in enumerate(qvals):
                    ax2.text(i+1,v+15,f"{v:.0f}",ha="center",fontsize=7.5,color=col)
            ax2.set_title("Quarterly Trend Line",fontsize=10,fontweight="bold")
            ax2.set_xticks([1,2,3,4]); ax2.set_xticklabels(["Q1","Q2","Q3","Q4"])
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y")
            ax2.set_ylabel("Avg Customers/Wk")

            # Q4 drop-off comparison
            ax3 = fig.add_subplot(gs[0,2])
            for yr,df,s,col in YEAR_META:
                if not df.empty:
                    q3d = df[df["week"].between(27,39)]["cpw"]
                    q4d = df[df["week"].between(40,52)]["cpw"]
                    ax3.plot(df[df["week"].between(27,52)]["week"],
                             df[df["week"].between(27,52)]["cpw"],
                             color=col,lw=2,label=str(yr),alpha=0.9)
                    if not q3d.empty and not q4d.empty:
                        q3_m = q3d.mean(); q4_m = q4d.mean()
                        drop = (q4_m-q3_m)/q3_m*100
                        ax3.axhline(q3_m,color=col,lw=0.8,ls="--",alpha=0.5)
                        ax3.text(40,q3_m+30,f"{yr} Q3→Q4: {drop:.0f}%",
                                 color=col,fontsize=7.5)
            ax3.axvspan(40,52.5,color=CTGT,alpha=0.07)
            ax3.set_title("Q3–Q4 Volume Decay Detail",fontsize=10,fontweight="bold")
            ax3.set_xlabel("Week"); ax3.set_ylabel("Customers / Week")
            ax3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax3.legend(fontsize=8); ax3.grid(True,axis="y")

        # ── ROLLING AVERAGE focused ───────────────────────────────────────────
        elif focus == "Rolling Average":
            gs = GridSpec(1,2,figure=fig,hspace=0.4,wspace=0.35,
                          left=0.06,right=0.97,top=0.9,bottom=0.1)
            for window, ax_idx, title in [(4,0,"4-Week Rolling Average"),(8,1,"8-Week Rolling Average")]:
                ax = fig.add_subplot(gs[0,ax_idx])
                for yr,df,s,col in YEAR_META:
                    if not df.empty:
                        roll = df["cpw"].rolling(window,min_periods=1).mean()
                        ax.plot(df["week"],roll,color=col,lw=2.2,label=str(yr))
                        ax.fill_between(df["week"],roll,alpha=0.08,color=col)
                        if s["avg"]: ax.axhline(s["avg"],color=col,lw=0.8,ls=":",alpha=0.6)
                ax.set_title(title,fontsize=11,fontweight="bold")
                ax.set_xlabel("Week"); ax.set_ylabel("Avg Customers/Wk")
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
                ax.legend(fontsize=9); ax.grid(True,axis="y"); ax.set_xlim(wk_lo,wk_hi)

        self.hist_canvas.draw()

    # ══════════════════════════════════════════════════════════════════════════
    #  LIVE 2025 SECTION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_live_section(self):
        s23, s24, s25 = self.s23, self.s24, self.s25
        inner = self.inner
        win   = self.winfo_toplevel()

        weeks_so_far = len(self.wl25)
        remaining    = max(0, 52 - weeks_so_far)
        last4_avg    = round(self.wl25["cpw"].tail(4).mean(), 0)
        projected    = int(s25["final"] + last4_avg * remaining) if remaining > 0 else s25["final"]
        needed_pw    = round((TARGET_2025 - s25["final"]) / remaining, 0) if remaining > 0 else 0
        on_track     = projected >= TARGET_2025

        section_label(inner,
            "▸  LIVE DATA  ·  2025  ·  TARGET: 87,000  ·  IN-YEAR PROGRESS",
            C25, LIVE_DIV)

        # ── KPI row ───────────────────────────────────────────────────────────
        live_kpi = tk.Frame(inner, bg=BG)
        live_kpi.pack(fill="x", padx=10, pady=(2,0))
        for c in range(8): live_kpi.columnconfigure(c, weight=1)

        kpi_card(live_kpi,"2025 CURRENT TOTAL", f"{s25['final']:,}",       f"{self.prog_pct}% of {TARGET_2025:,} target", C25, 0)
        kpi_card(live_kpi,"WEEKS RECORDED",     f"{weeks_so_far} / 52",    f"{remaining} weeks remaining",                TEAL,0+1)
        kpi_card(live_kpi,"CURRENT AVG /WK",    f"{s25['avg']:,.0f}",       f"Last 4-wk avg: {last4_avg:,.0f}",           C25, 2)
        kpi_card(live_kpi,"SHORTFALL",           f"{self.shortfall:,}",     f"to reach {TARGET_2025:,} target",           CTGT,3)
        if remaining > 0:
            kpi_card(live_kpi,"NEEDED /WK",      f"{needed_pw:,.0f}",      f"{'✓ On track' if on_track else '✗ Behind pace'} vs {last4_avg:,.0f} current", C25 if on_track else CTGT,4)
            kpi_card(live_kpi,"PROJECTED FINAL", f"{projected:,}",         f"{'▲ Exceeds' if on_track else '▼ Misses'} target by {abs(projected-TARGET_2025):,}", C25 if on_track else CTGT,5)
        else:
            kpi_card(live_kpi,"YEAR STATUS",     "COMPLETE",               f"Final: {s25['final']:,} / Target: {TARGET_2025:,}",              C25 if self.shortfall==0 else CTGT,4)
            kpi_card(live_kpi,"VS TARGET",        f"{'▲' if self.shortfall==0 else '▼'} {abs(self.shortfall):,}", "above" if self.shortfall==0 else "below target", C25 if self.shortfall==0 else CTGT,5)
        kpi_card(live_kpi,"2025 PEAK WEEK",      f"Wk {s25['peak_wk']}",  f"{s25['peak_cpw']:,} customers",             ACCENT,6)
        kpi_card(live_kpi,"WoW VOLATILITY",       f"±{s25['std']:,.0f}",   "std dev customers/wk",                       ACCENT,7)

        insight_bar(inner, [
            ("▲", f"99.8% of 87K target reached — only {self.shortfall:,} remaining",                           C25),
            ("⚡", f"Biggest surge: Wk8 +1,168 customers; biggest drop: Wk10 −1,655",                           ACCENT),
            ("◆", f"Q4 avg {s25['q4_avg']:,.0f}/wk — unlike prior years, no late-year volume collapse",         TEAL),
            ("▲", f"2025 avg {s25['avg']:,.0f}/wk — +{s25['avg']-s24['avg']:,.0f} above 2024 pace",            C25),
        ])

        # ── Live filter bar ───────────────────────────────────────────────────
        lfbar = tk.Frame(inner, bg=BG, highlightbackground=GRID, highlightthickness=1)
        lfbar.pack(fill="x", padx=10, pady=(2,0))

        # Region dropdown
        lbl(lfbar, "REGION")
        self.l_region_var = tk.StringVar(master=win, value="All")
        ttk.Combobox(lfbar, textvariable=self.l_region_var,
                     values=["All"]+REGIONS, width=13, style="WL.TCombobox",
                     state="readonly").pack(side="left", padx=2)
        self.l_region_var.trace_add("write", lambda *_: self._refresh_live())
        sep(lfbar)

        # Week range
        lbl(lfbar, "WEEK RANGE")
        self.l_wk_lo = tk.IntVar(master=win, value=1)
        self.l_wk_hi = tk.IntVar(master=win, value=52)
        spin_cfg = dict(bg=PANEL,fg=TEXT,insertbackground=TEXT,buttonbackground=PANEL,
                        relief="flat",font=("Courier New",8),width=3)
        tk.Label(lfbar,text="from",bg=BG,fg=TEXT_DIM,font=("Courier New",7)).pack(side="left",padx=(4,1))
        s_lo = tk.Spinbox(lfbar,from_=1,to=52,textvariable=self.l_wk_lo,command=self._refresh_live,**spin_cfg)
        s_lo.pack(side="left",padx=2); s_lo.bind("<Return>",lambda e: self._refresh_live())
        tk.Label(lfbar,text="to",bg=BG,fg=TEXT_DIM,font=("Courier New",7)).pack(side="left",padx=(4,1))
        s_hi = tk.Spinbox(lfbar,from_=1,to=52,textvariable=self.l_wk_hi,command=self._refresh_live,**spin_cfg)
        s_hi.pack(side="left",padx=2); s_hi.bind("<Return>",lambda e: self._refresh_live())
        sep(lfbar)

        # Comparison overlay
        lbl(lfbar, "COMPARE VS")
        self.l_compare_var = tk.StringVar(master=win, value="Both (2023 & 2024)")
        ttk.Combobox(lfbar, textvariable=self.l_compare_var,
                     values=["None","2023 only","2024 only","Both (2023 & 2024)"],
                     width=16, style="WL.TCombobox", state="readonly").pack(side="left",padx=2)
        self.l_compare_var.trace_add("write", lambda *_: self._refresh_live())
        sep(lfbar)

        # Chart focus
        lbl(lfbar, "CHART FOCUS")
        self.l_chart_var = tk.StringVar(master=win, value="Overview")
        ttk.Combobox(lfbar, textvariable=self.l_chart_var,
                     values=["Overview","Target Tracking","Weekly Volume",
                             "Regional Breakdown","Pace Analysis","Volatility"],
                     width=16, style="WL.TCombobox", state="readonly").pack(side="left",padx=2)
        self.l_chart_var.trace_add("write", lambda *_: self._refresh_live())
        sep(lfbar)

        reset_btn(lfbar, self._reset_live)

        # ── Live chart canvas ─────────────────────────────────────────────────
        self.live_fig = plt.Figure(figsize=(18,8.5), dpi=90, facecolor=BG)
        lc_frame = tk.Frame(inner, bg=BG)
        lc_frame.pack(fill="x", padx=10, pady=(3,12))
        self.live_canvas = FigureCanvasTkAgg(self.live_fig, master=lc_frame)
        self.live_canvas.get_tk_widget().configure(bg=BG)
        self.live_canvas.get_tk_widget().pack(fill="x")
        self._refresh_live()

    def _reset_live(self):
        self.l_region_var.set("All")
        self.l_wk_lo.set(1); self.l_wk_hi.set(52)
        self.l_compare_var.set("Both (2023 & 2024)")
        self.l_chart_var.set("Overview")

    def _get_live_filtered(self):
        lo = max(1, self.l_wk_lo.get()); hi = min(52, self.l_wk_hi.get())
        if lo > hi: lo, hi = hi, lo
        return self.wl25[self.wl25["week"].between(lo,hi)].copy(), lo, hi

    def _get_live_regional(self, year):
        region = self.l_region_var.get()
        rd = self.regional.get(year,{})
        if region == "All":
            totals = [0]*12
            for vals in rd.values():
                for i,v in enumerate(vals): totals[i] += v
            return totals
        return rd.get(region,[0]*12)

    def _get_compare_dfs(self):
        cmp = self.l_compare_var.get()
        lo  = max(1,self.l_wk_lo.get()); hi = min(52,self.l_wk_hi.get())
        result = {}
        if "2023" in cmp: result[2023] = self.wl23[self.wl23["week"].between(lo,hi)]
        if "2024" in cmp: result[2024] = self.wl24[self.wl24["week"].between(lo,hi)]
        return result

    def _refresh_live(self):
        w25f, lo, hi = self._get_live_filtered()
        s25f = calc_stats(w25f) if not w25f.empty else self.s25
        cmp_dfs = self._get_compare_dfs()
        focus   = self.l_chart_var.get()
        fig     = self.live_fig
        fig.clf()

        weeks_so_far = len(w25f)
        remaining    = max(0, hi - weeks_so_far)
        last4_avg    = w25f["cpw"].tail(4).mean() if not w25f.empty else 0

        def safe(df, wk_):
            r = df[df["week"]==wk_]
            return int(r["cpw"].values[0]) if len(r) else 0

        # ── OVERVIEW ──────────────────────────────────────────────────────────
        if focus == "Overview":
            gs = GridSpec(2,4,figure=fig,hspace=0.52,wspace=0.35,
                          left=0.05,right=0.97,top=0.93,bottom=0.1)

            # (0,0:2) Cumulative with compare overlays + milestone markers
            ax1 = fig.add_subplot(gs[0,0:2])
            for yr,(col,ls) in {2023:(C23,"--"),2024:(C24,"--")}.items():
                if yr in cmp_dfs and not cmp_dfs[yr].empty:
                    df = cmp_dfs[yr]
                    ax1.plot(df["week"],df["twl"],color=col,lw=1.3,ls=ls,alpha=0.55,label=f"{yr} (hist)")
            if not w25f.empty:
                ax1.plot(w25f["week"],w25f["twl"],color=C25,lw=2.5,label="2025 (live)")
                ax1.fill_between(w25f["week"],w25f["twl"],alpha=0.15,color=C25)
            ax1.axhline(TARGET_2025,color=CTGT,lw=1.8,ls="--",label=f"Target {TARGET_2025:,}")
            for thresh,lbl_t in [(25000,"25K"),(50000,"50K"),(75000,"75K")]:
                row = w25f[w25f["twl"]>=thresh]
                if not row.empty:
                    wk_=int(row["week"].iloc[0]); tv=int(row["twl"].iloc[0])
                    ax1.scatter(wk_,tv,color=TEAL,s=40,zorder=5)
                    ax1.annotate(f"{lbl_t}(Wk{wk_})",xy=(wk_,tv),xytext=(4,8),
                                 textcoords="offset points",fontsize=6.5,color=TEAL)
            ax1.set_title("2025 Cumulative Growth vs Historical & Target",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Total Waiting List")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=7,loc="upper left"); ax1.grid(True,axis="y"); ax1.set_xlim(lo,hi)

            # (0,2:4) Weekly volume
            ax2 = fig.add_subplot(gs[0,2:4])
            if not w25f.empty:
                cpw25 = w25f["cpw"].values.astype(float)
                wks25 = w25f["week"].values
                avg25 = s25f["avg"]
                ax2.bar(wks25,cpw25,color=[C25 if v>=avg25 else "#3A7A4A" for v in cpw25],alpha=0.85,width=0.85)
                ax2.axhline(avg25,color=C25,lw=1.4,ls="--",label=f"2025 avg {avg25:,.0f}/wk")
            for yr,col in {2023:C23,2024:C24}.items():
                if yr in cmp_dfs:
                    s_cmp = calc_stats(cmp_dfs[yr])
                    if s_cmp["avg"]: ax2.axhline(s_cmp["avg"],color=col,lw=1,ls=":",alpha=0.7,label=f"{yr} avg {s_cmp['avg']:,.0f}/wk")
            ax2.set_title("2025 Weekly Volume (bright=above avg)",fontsize=10,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Customers / Week")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=7); ax2.grid(True,axis="y"); ax2.set_xlim(lo-0.5,hi+0.5)

            # (1,0) Target progress donut
            ax3 = fig.add_subplot(gs[1,0])
            ax3.set_xlim(0,1); ax3.set_ylim(0,1); ax3.axis("off")
            ax3.set_title("Target Progress",fontsize=10,fontweight="bold")
            frac = min(s25f["final"]/TARGET_2025,1.0)
            ang_f = np.linspace(np.pi/2,np.pi/2-2*np.pi*frac,300)
            ang_g = np.linspace(np.pi/2-2*np.pi*frac,np.pi/2-2*np.pi,100)
            donut_arc(ax3,ang_f,C25,0.28,0.42,0.5,0.54)
            donut_arc(ax3,ang_g,GRID,0.28,0.42,0.5,0.54)
            ax3.text(0.5,0.59,f"{round(100*s25f['final']/TARGET_2025,1)}%",ha="center",va="center",fontsize=22,fontweight="bold",color=C25)
            ax3.text(0.5,0.47,"of target reached",ha="center",va="center",fontsize=7.5,color=TEXT)
            ax3.text(0.5,0.28,f"Actual: {s25f['final']:,}  |  Target: {TARGET_2025:,}",ha="center",va="center",fontsize=7,color=TEXT)
            ax3.text(0.5,0.19,f"Shortfall: {max(0,TARGET_2025-s25f['final']):,}",ha="center",va="center",fontsize=9,color=CTGT,fontweight="bold")

            # (1,1) Quarterly 3-year comparison
            ax4 = fig.add_subplot(gs[1,1])
            qdata = {2023:self.s23,2024:self.s24,2025:s25f}
            qcols = {2023:C23,2024:C24,2025:C25}
            ql = ["Q1","Q2","Q3","Q4"]; x = np.arange(4); bw=0.25; off=-bw
            for yr in [2023,2024,2025]:
                s = qdata[yr]; col = qcols[yr]
                if yr in [2023,2024] and yr not in cmp_dfs and self.l_compare_var.get()!="None":
                    off+=bw; continue
                if yr==2025 and w25f.empty: off+=bw; continue
                qv = [s["q1_avg"],s["q2_avg"],s["q3_avg"],s["q4_avg"]]
                ax4.bar(x+off,qv,bw,color=col,alpha=0.85,label=str(yr))
                off+=bw
            ax4.set_title("Quarterly Avg — Year Comparison",fontsize=10,fontweight="bold")
            ax4.set_xticks(x); ax4.set_xticklabels(ql,fontsize=9)
            ax4.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax4.legend(fontsize=8); ax4.grid(True,axis="y"); ax4.set_ylabel("Avg/Wk")

            # (1,2) WoW delta 2025
            ax5 = fig.add_subplot(gs[1,2])
            if not w25f.empty and len(w25f)>1:
                delta = w25f["cpw"].diff().dropna()
                ax5.bar(w25f["week"].iloc[1:],delta,color=[C25 if v>=0 else CTGT for v in delta],alpha=0.85)
                ax5.axhline(0,color=TEXT,lw=0.8)
            ax5.set_title("Week-on-Week Volume Change — 2025",fontsize=10,fontweight="bold")
            ax5.set_xlabel("Week"); ax5.set_ylabel("Δ Customers")
            ax5.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k)); ax5.grid(True,axis="y")

            # (1,3) Regional 2025 vs 2024
            ax6 = fig.add_subplot(gs[1,3])
            t24 = {r:sum(self.regional[2024].get(r,[0]*12)) for r in REGIONS}
            t25 = {r:sum(self.regional[2025].get(r,[0]*12)) for r in REGIONS}
            y = np.arange(len(REGIONS))
            ax6.barh(y-0.2,[t24[r] for r in REGIONS],0.35,color=C24,alpha=0.8,label="2024")
            ax6.barh(y+0.2,[t25[r] for r in REGIONS],0.35,color=[REG_COLORS[r] for r in REGIONS],alpha=0.85,label="2025")
            ax6.set_yticks(y); ax6.set_yticklabels(REGIONS,fontsize=8)
            ax6.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax6.set_title("Regional Totals — 2024 vs 2025",fontsize=10,fontweight="bold")
            ax6.set_xlabel("Annual Total"); ax6.legend(fontsize=8); ax6.grid(True,axis="x")

        # ── TARGET TRACKING focused ───────────────────────────────────────────
        elif focus == "Target Tracking":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.35,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            # Cumulative with full projection
            ax1 = fig.add_subplot(gs[0,0:2])
            for yr,(col,ls) in {2023:(C23,"--"),2024:(C24,"--")}.items():
                if yr in cmp_dfs and not cmp_dfs[yr].empty:
                    df=cmp_dfs[yr]
                    ax1.plot(df["week"],df["twl"],color=col,lw=1.2,ls=ls,alpha=0.5,label=f"{yr}")
            if not w25f.empty:
                ax1.plot(w25f["week"],w25f["twl"],color=C25,lw=2.5,label="2025")
                ax1.fill_between(w25f["week"],w25f["twl"],alpha=0.15,color=C25)
                # Projection cone
                last_wk = int(w25f["week"].iloc[-1]); last_twl = int(w25f["twl"].iloc[-1])
                if last_wk < 52:
                    rem_wks = np.arange(last_wk,53)
                    steps   = np.arange(1,len(rem_wks)+1)
                    avg_use = last4_avg if last4_avg>0 else s25f["avg"]
                    ax1.plot(rem_wks,last_twl+avg_use*steps,color=C25,lw=1.5,ls=":",label="Projected (current pace)")
                    ax1.fill_between(rem_wks,last_twl+avg_use*steps*0.9,last_twl+avg_use*steps*1.1,alpha=0.15,color=C25)
            ax1.axhline(TARGET_2025,color=CTGT,lw=2,ls="--",label=f"Target {TARGET_2025:,}")
            # Milestone dots
            for thresh,lbl_t in [(25000,"25K"),(50000,"50K"),(75000,"75K"),(87000,"TARGET")]:
                row=w25f[w25f["twl"]>=thresh]
                if not row.empty:
                    wk_=int(row["week"].iloc[0]); tv=int(row["twl"].iloc[0])
                    ax1.scatter(wk_,tv,color=CTGT if lbl_t=="TARGET" else TEAL,s=50,zorder=6)
                    ax1.annotate(f"{lbl_t}(Wk{wk_})",xy=(wk_,tv),xytext=(4,8),
                                 textcoords="offset points",fontsize=6.5,color=CTGT if lbl_t=="TARGET" else TEAL)
            ax1.set_title("2025 Target Tracking — Actuals, Projection & Milestones",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Total Waiting List")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=7,loc="upper left"); ax1.grid(True,axis="y"); ax1.set_xlim(lo,52)

            # Target progress donut (large)
            ax2 = fig.add_subplot(gs[0,2])
            ax2.set_xlim(0,1); ax2.set_ylim(0,1); ax2.axis("off")
            ax2.set_title("Target Gauge",fontsize=11,fontweight="bold")
            frac = min(s25f["final"]/TARGET_2025,1.0)
            ang_f=np.linspace(np.pi/2,np.pi/2-2*np.pi*frac,300)
            ang_g=np.linspace(np.pi/2-2*np.pi*frac,np.pi/2-2*np.pi,100)
            donut_arc(ax2,ang_f,C25,0.25,0.44,0.5,0.55)
            donut_arc(ax2,ang_g,GRID,0.25,0.44,0.5,0.55)
            ax2.text(0.5,0.61,f"{round(100*s25f['final']/TARGET_2025,1)}%",ha="center",va="center",fontsize=26,fontweight="bold",color=C25)
            ax2.text(0.5,0.49,"of target reached",ha="center",va="center",fontsize=8,color=TEXT)
            ax2.text(0.5,0.34,f"Actual: {s25f['final']:,}",ha="center",va="center",fontsize=9,color=TEXT)
            ax2.text(0.5,0.25,f"Target: {TARGET_2025:,}",ha="center",va="center",fontsize=9,color=CTGT)
            ax2.text(0.5,0.15,f"Shortfall: {max(0,TARGET_2025-s25f['final']):,}",ha="center",va="center",fontsize=10,color=CTGT,fontweight="bold")

        # ── WEEKLY VOLUME focused ─────────────────────────────────────────────
        elif focus == "Weekly Volume":
            gs = GridSpec(2,2,figure=fig,hspace=0.5,wspace=0.35,
                          left=0.06,right=0.97,top=0.93,bottom=0.1)

            ax1 = fig.add_subplot(gs[0,:])
            if not w25f.empty:
                cpw25 = w25f["cpw"].values.astype(float)
                avg25 = s25f["avg"]
                ax1.bar(w25f["week"],cpw25,color=[C25 if v>=avg25 else "#3A7A4A" for v in cpw25],alpha=0.85,width=0.85,label="2025")
                ax1.axhline(avg25,color=C25,lw=1.4,ls="--",label=f"2025 avg {avg25:,.0f}")
                # Peak annotation
                pk_i=int(np.argmax(cpw25))
                ax1.annotate(f"Wk{w25f['week'].iloc[pk_i]}\n{int(cpw25[pk_i]):,}",
                             xy=(w25f["week"].iloc[pk_i],cpw25[pk_i]),
                             xytext=(0,8),textcoords="offset points",fontsize=7,color=TEAL,ha="center")
            for yr,col in {2023:C23,2024:C24}.items():
                if yr in cmp_dfs and not cmp_dfs[yr].empty:
                    df=cmp_dfs[yr]
                    ax1.step(df["week"],df["cpw"],color=col,lw=1.2,alpha=0.6,where="mid",label=str(yr))
            ax1.set_title("2025 Weekly Volume vs Historical",fontsize=11,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Customers / Week")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=8,ncol=4); ax1.grid(True,axis="y"); ax1.set_xlim(lo-0.5,hi+0.5)

            ax2 = fig.add_subplot(gs[1,0])
            if not w25f.empty:
                for win_,col_ in [(4,C25),(8,TEAL)]:
                    roll=w25f["cpw"].rolling(win_,min_periods=1).mean()
                    ax2.plot(w25f["week"],roll,color=col_,lw=2,label=f"{win_}-wk rolling")
                ax2.fill_between(w25f["week"],w25f["cpw"].rolling(4,min_periods=1).mean()*0.9,
                                 w25f["cpw"].rolling(4,min_periods=1).mean()*1.1,alpha=0.1,color=C25)
            ax2.set_title("Rolling Averages (4-wk & 8-wk)",fontsize=10,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Avg Customers/Wk")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y")

            ax3 = fig.add_subplot(gs[1,1])
            if not w25f.empty and len(w25f)>1:
                delta=w25f["cpw"].diff().dropna()
                ax3.bar(w25f["week"].iloc[1:],delta,color=[C25 if v>=0 else CTGT for v in delta],alpha=0.85,width=0.85)
                ax3.axhline(0,color=TEXT,lw=0.8)
                ax3.axhline(delta.mean(),color=ACCENT,lw=1,ls=":",label=f"Mean Δ {delta.mean():.0f}")
            ax3.set_title("Week-on-Week Change — 2025",fontsize=10,fontweight="bold")
            ax3.set_xlabel("Week"); ax3.set_ylabel("Δ Customers")
            ax3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax3.legend(fontsize=8); ax3.grid(True,axis="y")

        # ── REGIONAL BREAKDOWN focused ────────────────────────────────────────
        elif focus == "Regional Breakdown":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.38,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            # Horizontal bar: 2025 vs 2024 per region
            ax1 = fig.add_subplot(gs[0,0])
            t24={r:sum(self.regional[2024].get(r,[0]*12)) for r in REGIONS}
            t25={r:sum(self.regional[2025].get(r,[0]*12)) for r in REGIONS}
            y=np.arange(len(REGIONS))
            bars24=ax1.barh(y-0.2,[t24[r] for r in REGIONS],0.35,color=C24,alpha=0.8,label="2024")
            bars25=ax1.barh(y+0.2,[t25[r] for r in REGIONS],0.35,color=[REG_COLORS[r] for r in REGIONS],alpha=0.9,label="2025")
            for i,r in enumerate(REGIONS):
                chg=((t25[r]-t24[r])/t24[r]*100) if t24[r] else 0
                ax1.text(max(t24[r],t25[r])+300,i,f"{chg:+.0f}%",va="center",fontsize=7,
                         color=C25 if chg>=0 else CTGT)
            ax1.set_yticks(y); ax1.set_yticklabels(REGIONS,fontsize=9)
            ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.set_title("Regional Annual Totals — 2024 vs 2025",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Annual Total"); ax1.legend(fontsize=8); ax1.grid(True,axis="x")

            # Monthly breakdown for selected region
            ax2 = fig.add_subplot(gs[0,1])
            x2=np.arange(12)
            for yr,col in [(2024,C24),(2025,C25)]:
                monthly=self._get_live_regional(yr)
                ax2.bar(x2+(-0.2 if yr==2024 else 0.2),monthly,0.38,color=col,alpha=0.85,label=str(yr))
            rl=self.l_region_var.get() if self.l_region_var.get()!="All" else "All Regions"
            ax2.set_title(f"Monthly Additions — {rl}",fontsize=10,fontweight="bold")
            ax2.set_xticks(x2); ax2.set_xticklabels(MONTHS,fontsize=8,rotation=30)
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y"); ax2.set_ylabel("Customers Added")

            # 2025 region share pie
            ax3 = fig.add_subplot(gs[0,2])
            pie_vals=[sum(self.regional[2025].get(r,[0]*12)) for r in REGIONS]
            pie_cols=[REG_COLORS[r] for r in REGIONS]
            nz=[(v,c,r) for v,c,r in zip(pie_vals,pie_cols,REGIONS) if v>0]
            if nz:
                pv,pc,pr=zip(*nz)
                _,_,ats=ax3.pie(pv,colors=pc,startangle=90,autopct="%1.1f%%",pctdistance=0.75,
                                wedgeprops=dict(width=0.55,edgecolor=BG,linewidth=2))
                for at in ats: at.set_fontsize(7); at.set_color(TEXT)
                ax3.legend([mpatches.Patch(color=c,label=r) for c,r in zip(pc,pr)],
                           loc="lower center",ncol=2,frameon=False,fontsize=7,
                           labelcolor=TEXT,bbox_to_anchor=(0.5,-0.12))
            ax3.set_title("2025 Region Share",fontsize=10,fontweight="bold")

        # ── PACE ANALYSIS focused ─────────────────────────────────────────────
        elif focus == "Pace Analysis":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.38,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            # Required pace vs actual pace line
            ax1 = fig.add_subplot(gs[0,0:2])
            if not w25f.empty:
                # Actual cumulative
                ax1.plot(w25f["week"],w25f["twl"],color=C25,lw=2.5,label="Actual 2025")
                ax1.fill_between(w25f["week"],w25f["twl"],alpha=0.12,color=C25)
                # Required pace line (linear to target)
                req = np.linspace(0,TARGET_2025,53)
                ax1.plot(np.arange(0,53),req,color=CTGT,lw=1.5,ls="--",label=f"Required pace → {TARGET_2025:,}")
                # Historical pace references
                for yr,col in {2023:C23,2024:C24}.items():
                    if yr in cmp_dfs and not cmp_dfs[yr].empty:
                        df=cmp_dfs[yr]
                        ax1.plot(df["week"],df["twl"],color=col,lw=1.2,ls=":",alpha=0.55,label=str(yr))
                # Gap shading
                req_at_wks = np.interp(w25f["week"],np.arange(0,53),req)
                above = w25f["twl"].values >= req_at_wks
                ax1.fill_between(w25f["week"],w25f["twl"],req_at_wks,
                                 where=above,color=C25,alpha=0.2,label="Ahead of pace")
                ax1.fill_between(w25f["week"],w25f["twl"],req_at_wks,
                                 where=~above,color=CTGT,alpha=0.2,label="Behind pace")
            ax1.axhline(TARGET_2025,color=CTGT,lw=1.8,ls="--")
            ax1.set_title("2025 Actual vs Required Pace to Target",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Cumulative Total")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=7,loc="upper left"); ax1.grid(True,axis="y"); ax1.set_xlim(lo,52)

            # Weekly pace gap bar
            ax2 = fig.add_subplot(gs[0,2])
            if not w25f.empty:
                req_wk = TARGET_2025/52  # flat required pace per week
                gaps = w25f["cpw"] - req_wk
                ax2.bar(w25f["week"],gaps,color=[C25 if v>=0 else CTGT for v in gaps],alpha=0.85,width=0.85)
                ax2.axhline(0,color=TEXT,lw=1)
                ax2.axhline(req_wk,color=CTGT,lw=1,ls="--",label=f"Target pace: {req_wk:.0f}/wk",alpha=0.5)
            ax2.set_title("Weekly Volume vs Required Pace",fontsize=10,fontweight="bold")
            ax2.set_xlabel("Week"); ax2.set_ylabel("Δ from Required Pace")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.legend(fontsize=8); ax2.grid(True,axis="y")

        # ── VOLATILITY focused ────────────────────────────────────────────────
        elif focus == "Volatility":
            gs = GridSpec(1,3,figure=fig,hspace=0.4,wspace=0.38,
                          left=0.05,right=0.97,top=0.9,bottom=0.1)

            # Bollinger-band style ±1σ envelope
            ax1 = fig.add_subplot(gs[0,0:2])
            if not w25f.empty:
                roll_mean = w25f["cpw"].rolling(4,min_periods=1).mean()
                roll_std  = w25f["cpw"].rolling(4,min_periods=1).std().fillna(0)
                ax1.plot(w25f["week"],w25f["cpw"],color=C25,lw=1.5,alpha=0.7,label="Weekly CPW")
                ax1.plot(w25f["week"],roll_mean,color=TEAL,lw=2,label="4-wk mean")
                ax1.fill_between(w25f["week"],roll_mean-roll_std,roll_mean+roll_std,
                                 alpha=0.2,color=TEAL,label="±1 std dev band")
                ax1.axhline(s25f["avg"],color=C25,lw=1,ls="--",alpha=0.7,label=f"Annual avg {s25f['avg']:,.0f}")
            # Add historical lines for context
            for yr,col in {2023:C23,2024:C24}.items():
                if yr in cmp_dfs and not cmp_dfs[yr].empty:
                    df=cmp_dfs[yr]; rm=df["cpw"].rolling(4,min_periods=1).mean()
                    ax1.plot(df["week"],rm,color=col,lw=1,ls=":",alpha=0.5,label=f"{yr} 4-wk mean")
            ax1.set_title("2025 Weekly Volume with Rolling ±1σ Band",fontsize=10,fontweight="bold")
            ax1.set_xlabel("Week"); ax1.set_ylabel("Customers / Week")
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax1.legend(fontsize=7); ax1.grid(True,axis="y"); ax1.set_xlim(lo,hi)

            # Distribution boxplot all three years
            ax2 = fig.add_subplot(gs[0,2])
            box_data=[]; box_labels=[]; box_colors=[]
            for yr,df,col in [(2023,self.wl23,C23),(2024,self.wl24,C24),(2025,w25f,C25)]:
                d=df["cpw"].dropna().values
                if len(d)>0:
                    box_data.append(d); box_labels.append(str(yr)); box_colors.append(col)
            if box_data:
                bp=ax2.boxplot(box_data,patch_artist=True,widths=0.55,
                               medianprops=dict(color="white",linewidth=2),
                               whiskerprops=dict(color=TEXT_DIM),
                               capprops=dict(color=TEXT_DIM),
                               flierprops=dict(marker="o",ms=4,alpha=0.5))
                for patch,col in zip(bp["boxes"],box_colors):
                    patch.set_facecolor(col); patch.set_alpha(0.75)
                ax2.set_xticklabels(box_labels)
            ax2.set_title("Distribution of Weekly Volume",fontsize=10,fontweight="bold")
            ax2.set_ylabel("Customers / Week")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_k))
            ax2.grid(True,axis="y")

        self.live_canvas.draw()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        candidates = [
            os.path.join(here, "Data set examples_Main.xlsx"),
            os.path.join(here, "Copy_of_Data_set_examples_Main.xlsx"),
            os.path.join(here, "data.xlsx"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path is None:
            import tkinter.filedialog as fd
            _r = tk.Tk(); _r.withdraw()
            path = fd.askopenfilename(title="Select Excel file",
                                      filetypes=[("Excel files","*.xlsx *.xls")])
            _r.destroy()
        if not path:
            print("No data file selected. Exiting."); sys.exit(1)

    root = tk.Tk()
    app  = WaitingListDashboard(master=root, data_path=path)
    app.pack(fill="both", expand=True)
    root.mainloop()