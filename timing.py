import pandas as pd
import tkinter as tk
from tkinter import ttk
from datetime import date
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

today = pd.Timestamp.today()
currentDate = pd.Timestamp.today().strftime("%d %b %Y")

bgDark = "#0D0E11"
bgCards = "#16181F"
bgSurface = "#1C1F28"
accent = "#1B4FBF"
border = "#252830"
primaryText = "#EEF0F5"
secondaryText = "#6B7280"
green = "#1A6B3C"
textGreen = "#4ADE80"
amber = "#D4621A"
textAmber = "#FB923C"
red = "#8B1A1A"
textRed = "#F87171"
gold = "#C9A84C"

milestones = [("Kickoff", "Baseline_Programme_Kickoff", "Approved_Programme_Kickoff"),
              ("Concept Alignment", "Baseline_Concept_Alignment_Complete", "Approved_Concept_Alignment_Complete"),
              ("Design Readiness", "Baseline_Design_Readiness_Achieved", "Approved_Design_Readiness_Achieved"),
              ("Build Preperation", "Baseline_Build_Preparation_Complete", "Approved_Build_Preparation_Complete"),
              ("Validation Phase", "Baseline_Validation_Phase_Complete", "Approved_Validation_Phase_Complete"),
              ("Production Readiness", "Baseline_Production_Readiness_Review", "Approved_Production_Readiness_Review"),
              ("Completion", "Baseline_Programme_Completion", "Approved_Programme_Completion"),
              ]


class Dashboard(tk.Toplevel):

    def __init__(self, master=None, data_path="Data set examples_Main.xlsx"):
        super().__init__(master)
        print("dashboard called")

        self.title("Project Timeline Dashboard")
        self.geometry("1500x900")
        self.configure(background=bgDark)

        # ── Load & prepare data ──────────────────────────────────────────────
        self.df = pd.read_excel(data_path, sheet_name="Timing")
        df = self.df

        df["Baseline_Programme_Completion"] = pd.to_datetime(
            df["Baseline_Programme_Completion"], format="mixed", dayfirst=True, errors="coerce")
        df["Approved_Programme_Completion"] = pd.to_datetime(
            df["Approved_Programme_Completion"], format="mixed", dayfirst=True, errors="coerce")

        df["slip_time"] = (
                df["Approved_Programme_Completion"] - df["Baseline_Programme_Completion"]
        ).dt.days.fillna(0).astype(int)
        df["dtd"] = (df["Approved_Programme_Completion"] - today).dt.days

        df["Platform_Name"] = df["Platform_Name"].str.strip().str.replace("PLATFORM_", "", regex=False)
        df["Programme_ID"] = df["Programme_ID"].str.strip().str.replace("PRG_", "", regex=False)
        df["Project_Status"] = df["Project_Status"].str.strip()

        programmeList = ["ALL"] + sorted(df["Programme_ID"].unique())
        platformList = ["ALL"] + sorted(df["Platform_Name"].unique())

        # ── Styles ───────────────────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox", fieldbackgound=bgSurface, fg=gold, arrowcolor=primaryText,
                        bordercolor=secondaryText, lightcolor=bgSurface, darkcolor=bgSurface)
        style.map("Dark.TCombobox", fieldbackground=[("readonly", bgSurface)],
                  foreground=[("readonly", primaryText)], background=[("readonly", bgSurface)])
        style.configure("Treeview", bg=bgDark, fg=primaryText, fieldbackground=bgDark,
                        rowheight=25, font=("Sans Serif", 10))
        style.configure("Treeview.Heading", bg=bgDark, fg=primaryText,
                        font=("Sans Serif", 10, "bold"), relief="flat")
        style.map("Treeview", bg=[("selected", bgSurface)])
        style.configure("Dark.Vertical.TScrollbar", bg=bgSurface, troughcolor=bgDark,
                        bordercolor=secondaryText, darkcolor=bgSurface, lightcolor=bgSurface)
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", secondaryText), ("disabled", bgSurface)])

        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, background=bgSurface, height=58)
        header.pack(fill="x")

        tk.Button(header, text="Back", bg=bgSurface, fg=gold, command=self.on_button_click).pack(side="left",
                                                                                                 padx=(10, 4), pady=8)
        tk.Label(header, text="➤", background=bgSurface, fg=accent,
                 font=("Sans Serif", 25, "bold")).pack(side="left", padx=(18, 6))
        tk.Label(header, text="TIMING DASHBOARD", background=bgSurface, fg=gold,
                 font=("Sans Serif", 20, "bold")).pack(side="left")
        tk.Label(header, text=currentDate, background=bgCards, fg=secondaryText,
                 font=("Sans Serif", 15)).pack(side="right", padx=20)

        tk.Frame(self, background=gold, height=2).pack(fill="x")

        controls = tk.Frame(header, background=bgSurface)
        controls.pack(side="right", padx=15, pady=12)

        programmeFrame = tk.Frame(controls, bg=bgSurface)
        programmeFrame.pack(side="right", padx=20)

        tk.Label(controls, text="Programme", background=bgSurface, fg=gold,
                 font=("Sans Sarif", 10)).pack(side="left", padx=(0, 5))
        self.programmeSelection = tk.StringVar(value="ALL")
        dropdownProgramme = ttk.Combobox(programmeFrame, textvariable=self.programmeSelection,
                                         values=programmeList, width=15, state="readonly",
                                         style="Dark.TCombobox")
        dropdownProgramme.pack(padx=(0, 10))

        platformFrame = tk.Frame(controls, bg=bgSurface)
        platformFrame.pack(side="left", padx=20)

        tk.Label(controls, text="Platform", background=bgSurface, fg=gold,
                 font=("Sans Sarif", 10)).pack(padx=(0, 5))
        self.platformSelection = tk.StringVar(value="ALL")
        dropdownPlatform = ttk.Combobox(platformFrame, textvariable=self.platformSelection,
                                        values=platformList, width=15, state="readonly",
                                        style="Dark.TCombobox")
        dropdownPlatform.pack(padx=(0, 10))

        # ── Summary Cards ────────────────────────────────────────────────────
        cardFrame = tk.Frame(self, background=bgDark)
        cardFrame.pack(fill="x", padx=20, pady=15)
        for col in range(4):
            cardFrame.columnconfigure(col, weight=1)

        self.cardOnTrack, self.cardOnSub = self._summary_card(cardFrame, 0, green, textGreen, "ON TRACK")
        self.cardTotal, self.cardTotalSub = self._summary_card(cardFrame, 1, accent, primaryText, "TOTAL")
        self.cardRisk, self.cardRiskSub = self._summary_card(cardFrame, 2, amber, textAmber, "AT RISK")
        self.cardDelayed, self.cardDelayedSub = self._summary_card(cardFrame, 3, red, textRed, "DELAYED")

        # ── Graphs ───────────────────────────────────────────────────────────
        graphCon = tk.Frame(self, bg=bgDark, height=250)
        graphCon.pack(fill="x", expand=False, padx=20, pady=(10, 20))
        graphCon.pack_propagate(False)
        graphCon.columnconfigure(0, weight=1)
        graphCon.columnconfigure(1, weight=1)
        graphCon.rowconfigure(0, weight=1)

        leftGraph = tk.Frame(graphCon, bg=bgDark)
        leftGraph.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        rightGraph = tk.Frame(graphCon, bg=bgDark)
        rightGraph.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.figure1 = Figure(figsize=(5, 2), dpi=80)
        self.ax1 = self.figure1.add_subplot(111)
        self.canva1 = FigureCanvasTkAgg(self.figure1, master=leftGraph)
        self.canva1.get_tk_widget().pack(fill="both", expand=True)

        self.figure2 = Figure(figsize=(5, 2), dpi=80)
        self.ax2 = self.figure2.add_subplot(111)
        self.canva2 = FigureCanvasTkAgg(self.figure2, master=rightGraph)
        self.canva2.get_tk_widget().pack(fill="both", expand=True)

        # ── Table ────────────────────────────────────────────────────────────
        tableFrame = tk.Frame(self, bg=bgDark)
        tableFrame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        tableCard = tk.Frame(tableFrame, bg=bgDark, highlightthickness=1, highlightbackground=bgSurface)
        tableCard.pack(fill="both", expand=True)

        tableHeader = tk.Frame(tableCard, bg=bgSurface)
        tableHeader.pack(fill="x")
        tk.Frame(tableCard, bg=bgSurface, height=1).pack(fill="x")

        leftHeader = tk.Frame(tableHeader, bg=bgSurface)
        leftHeader.pack(side="left", padx=15, pady=10)

        tk.Label(leftHeader, text="Vehicle Timing Report", bg=bgSurface, fg=primaryText,
                 font=("Sans Serif", 10, "bold")).pack(side="left")

        self.countLabel = tk.Label(leftHeader, text="", bg=bgSurface, fg=primaryText,
                                   font=("Sans Serif", 10), padx=8, pady=2)
        self.countLabel.pack(side="left", padx=8)

        rightHeader = tk.Frame(tableHeader, bg=bgSurface)
        rightHeader.pack(side="right", padx=12, pady=8)

        tk.Label(rightHeader, text="Status", bg=bgSurface, fg=gold,
                 font=("Sans Serif", 10)).pack(side="left", padx=(0, 5))
        self.status = tk.StringVar(value="ALL")
        StatDropdown = ttk.Combobox(rightHeader, textvariable=self.status,
                                    values=["ALL", "On Track", "At Risk", "Delayed"],
                                    width=10, state="readonly", style="Dark.TCombobox")
        StatDropdown.pack(side="left", padx=(0, 10))

        tk.Label(rightHeader, text="Search", bg=bgSurface, fg=gold,
                 font=("Sans Serif", 10)).pack(side="left", padx=(0, 5))
        self.search = tk.StringVar()
        searchBox = tk.Entry(rightHeader, textvariable=self.search, bg=secondaryText,
                             font=("Sans Serif", 10), width=20, relief="flat")
        searchBox.pack(side="left")

        columns = ["Programme", "Vehicle", "Platform", "PM Owner", "RAG", "DEADLINE", "Slip", "Days to Deadline"]
        columnsWidth = [90, 70, 80, 80, 90, 100, 70, 120]

        frame = tk.Frame(tableCard, bg=bgDark)
        frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", style="Dark.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")

        self.table = ttk.Treeview(frame, columns=columns, show="headings",
                                  yscrollcommand=scrollbar.set, style="Treeview")
        scrollbar.config(command=self.table.yview)

        for col, width in zip(columns, columnsWidth):
            self.table.heading(col, text=col.upper())
            if col == "PM Owner":
                self.table.column(col, width=width, minwidth=width, anchor="w", stretch=True)
            else:
                self.table.column(col, width=width, minwidth=width, anchor="w", stretch=False)

        self.table.pack(fill="both", expand=True)

        self.table.tag_configure("On Track", foreground=green, background=bgDark)
        self.table.tag_configure("At Risk", foreground=amber, background=bgDark)
        self.table.tag_configure("Delayed", foreground=red, background=bgDark)

        bottom = tk.Frame(self.table, bg=bgSurface, height=40)
        bottom.pack(fill="x")

        statusBar = tk.Label(bottom, text="", bg=bgDark, fg=primaryText,
                             font=("Sans Serif", 10), anchor="center")
        statusBar.pack(side="right")

        key = tk.Frame(bottom, bg=bgDark)
        key.pack(side="right")
        tk.Label(key, text="✅ On Track", bg=bgDark, fg=green, font=("Sans Serif", 10, "bold")).pack(side="left")
        tk.Label(key, text="⚠️ At Risk", bg=bgDark, fg=amber, font=("Sans Serif", 10, "bold")).pack(side="left")
        tk.Label(key, text="❗Delayed", bg=bgDark, fg=textRed, font=("Sans Serif", 10, "bold")).pack(side="left")

        # ── Bind filters ─────────────────────────────────────────────────────
        dropdownProgramme.bind("<<ComboboxSelected>>", self._update_table)
        dropdownPlatform.bind("<<ComboboxSelected>>", self._update_table)
        StatDropdown.bind("<<ComboboxSelected>>", self._update_table)
        self.search.trace_add("write", self._update_table)

        self._update_table()

    def on_button_click(self):
        self.destroy()

    # ── Helper: create a summary card ────────────────────────────────────────
    def _summary_card(self, parent, column, bg_colour, fg_colour, name):
        card = tk.Frame(parent, bg=bg_colour, padx=20, pady=15)
        card.grid(row=0, column=column, sticky="nsew", padx=6)

        tk.Label(card, text=name, bg=bg_colour, fg=fg_colour,
                 font=("Sans Serif", 10, "bold")).pack(anchor="w")

        labelNumber = tk.Label(card, text="-", bg=bg_colour, fg="white",
                               font=("Sans Serif", 20, "bold"))
        labelNumber.pack(anchor="w", pady=(5, 1))

        subLabel = tk.Label(card, text="", bg=bg_colour, fg=fg_colour, font=("Sans Serif", 10))
        subLabel.pack(anchor="w")

        return labelNumber, subLabel

    # ── Formatting helpers ───────────────────────────────────────────────────
    @staticmethod
    def _rag_status(status):
        if status == "On Track":
            return "✅ On Track"
        elif status == "At Risk":
            return "⚠️ At Risk"
        else:
            return "❗Delayed"

    @staticmethod
    def _formatting_slip(slip):
        if slip == 0:
            return "0d"
        elif slip > 0:
            return "+" + str(slip) + "d"
        else:
            return str(slip) + "d"

    @staticmethod
    def _formatting_dtd(dtd):
        if pd.isna(dtd):
            return "-"
        elif dtd < 0:
            return str(abs(dtd)) + "d overdue"
        else:
            return str(dtd) + "d remaining"

    # ── Main update method ───────────────────────────────────────────────────
    def _update_table(self, *args):
        filtered = self.df.copy()

        programmeSelect = self.programmeSelection.get()
        if programmeSelect != "ALL":
            filtered = filtered[filtered["Programme_ID"] == programmeSelect]

        platformSelect = self.platformSelection.get()
        if platformSelect != "ALL":
            filtered = filtered[filtered["Platform_Name"] == platformSelect]

        selectedStatus = self.status.get()
        if selectedStatus != "ALL":
            filtered = filtered[filtered["Project_Status"] == selectedStatus]

        searchText = self.search.get().lower()
        if searchText:
            find = (
                    filtered["Platform_Name"].str.lower().str.contains(searchText, na=False) |
                    filtered["Vehicle_Code"].str.lower().str.contains(searchText, na=False) |
                    filtered["PM_Owner"].str.lower().str.contains(searchText, na=False)
            )
            filtered = filtered[find]

        total = len(filtered)
        onTrack = len(filtered[filtered["Project_Status"] == "On Track"])
        atRisk = len(filtered[filtered["Project_Status"] == "At Risk"])
        delayed = len(filtered[filtered["Project_Status"] == "Delayed"])
        numOfProgrammes = filtered["Programme_ID"].nunique()
        avg_slip = round(filtered["slip_time"].mean(), 0) if total > 0 else 0

        self.cardOnTrack.config(text=str(onTrack))
        self.cardOnSub.config(text=(str(round(onTrack / total * 100)) + "%") if total > 0 else "0%")

        self.cardTotal.config(text=str(total))
        self.cardTotalSub.config(text=str(numOfProgrammes) + " Programmes")

        self.cardRisk.config(text=str(atRisk))
        self.cardRiskSub.config(text=(str(round(atRisk / total * 100)) + "%") if total > 0 else "0%")

        self.cardDelayed.config(text=str(delayed))
        self.cardDelayedSub.config(text="avg slip " + str(avg_slip) + " days")

        self.countLabel.config(text=total)

        for row in self.table.get_children():
            self.table.delete(row)

        for _, row in filtered.iterrows():
            tag = row["Project_Status"]
            deadline = row["Approved_Programme_Completion"].strftime("%d %b %Y") \
                if pd.notna(row["Approved_Programme_Completion"]) else "--"

            self.table.insert("", "end", tags=(tag,), values=(
                row["Programme_ID"],
                row["Vehicle_Code"],
                row["Platform_Name"],
                row["PM_Owner"],
                self._rag_status(row["Project_Status"]),
                deadline,
                self._formatting_slip(row["slip_time"]),
                self._formatting_dtd(row["dtd"])
            ))

        # ── Trend Graph ──────────────────────────────────────────────────────
        self.ax1.clear()
        trenddf = filtered.dropna(subset=["Approved_Programme_Completion"]).copy()
        trenddf["Month"] = trenddf["Approved_Programme_Completion"].dt.to_period("M")
        monthly = trenddf.groupby("Month")["slip_time"].mean().reset_index()
        monthly["Month"] = monthly["Month"].dt.to_timestamp()

        if len(monthly) > 0:
            self.ax1.plot(monthly["Month"], monthly["slip_time"],
                          marker="o", linestyle="-", linewidth=2)

        self.ax1.set_title("Slip Time Trend", color=primaryText, fontsize=12, fontweight="bold")
        self.ax1.set_facecolor(bgDark)
        self.figure1.patch.set_facecolor(bgDark)
        for spine in self.ax1.spines.values():
            spine.set_visible(False)
        self.ax1.tick_params(colors=primaryText)
        self.ax1.grid(axis="y", linestyle="--", alpha=0.3)
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
        self.figure1.autofmt_xdate()
        self.canva1.draw()

        # ── Pie Chart ────────────────────────────────────────────────────────
        self.ax2.clear()
        labels = ["On Track", "At Risk", "Delayed"]
        values = [onTrack, atRisk, delayed]

        if sum(values) > 0:
            self.ax2.pie(
                values, labels=labels, colors=[green, amber, red],
                autopct="%1.1f%%", pctdistance=1.1, labeldistance=1.5,
                startangle=90, textprops={"color": primaryText},
                wedgeprops={"width": 0.4}
            )

        self.ax2.set_title("Project Status Distribution", color=primaryText,
                           fontsize=12, fontweight="bold")
        self.ax2.set_facecolor(bgDark)
        self.figure2.patch.set_facecolor(bgDark)
        self.canva2.draw()

if __name__ == "__main__":  # starts app
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()