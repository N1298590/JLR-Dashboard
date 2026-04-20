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
accent =  "#1B4FBF"
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

def dashboard():

    df = pd.read_excel(r"JLR Coursework\Data Analysis Coursework\Data set examples_Main.xlsx", sheet_name= "Timing")
    print("dashboard called")
    def rag_status(status):
            if status == "On Track":
                return "✅ On Track"
            elif status == "At Risk":
                return "⚠️ At Risk"
            else:
                return "❗Delayed"
            
    def formatting_slip(slip):
            if slip == 0:
                return "0d"
            elif slip > 0:
                slip = "+" + str(slip) + "d"
                return slip
            else:
                return str(slip) + "d"
            
    def formatting_dtd(dtd):
            if pd.isna(dtd):
                return "-"
            elif dtd < 0:
                dtd = str(abs(dtd)) + "d overdue"
                return dtd
            else:
                dtd = str(dtd) + "d remaining"
                return dtd
            

    df["Baseline_Programme_Completion"] = pd.to_datetime(df["Baseline_Programme_Completion"], format= "mixed",dayfirst= True, errors = "coerce")
    df["Approved_Programme_Completion"] = pd.to_datetime(df["Approved_Programme_Completion"], format= "mixed",dayfirst= True, errors = "coerce")

    df["slip_time"] = (df["Approved_Programme_Completion"] - df["Baseline_Programme_Completion"]).dt.days.fillna(0).astype(int)
    df["dtd"] = (df["Approved_Programme_Completion"] - today).dt.days 

    df["Platform_Name"] = df["Platform_Name"].str.strip().str.replace("PLATFORM_", "", regex= False)
    df["Programme_ID"] = df["Programme_ID"].str.strip().str.replace("PRG_", "", regex = False)
    df["Project_Status"] = df["Project_Status"].str.strip()

    programmeList = ["ALL"] + sorted(df["Programme_ID"].unique())
    platformList = ["ALL"] + sorted(df["Platform_Name"].unique())


    window = tk.Tk()
    window.title("Project Timeline Dashboard")
    window.geometry("1500x900")
    window.configure(background= bgDark)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TCombobox", fieldbackgound = bgSurface, fg = gold, arrowcolor = primaryText, bordercolor = secondaryText, lightcolor = bgSurface, darkcolor = bgSurface)

    style.map("Dark.TCombobox", fieldbackground = [("readonly", bgSurface)], foreground = [("readonly", primaryText)], background = [("readonly", bgSurface)])




    header = tk.Frame(window, background= bgSurface, height= 58)
    header.pack(fill= "x")

    def summary_cards(column,bg_colour, fg_colour,name):
            
            card = tk.Frame(cardFrame, bg = bg_colour, padx= 20, pady=15)
            card.grid(row= 0, column= column, sticky= "nsew", padx= 6)

            tk.Label(card, text = name, bg = bg_colour, fg = fg_colour, font= ("Sans Serif", 10, "bold")).pack(anchor= "w")

            labelNumber = tk.Label(card, text= "-", bg= bg_colour, fg = "white", font =("Sans Serif", 20, "bold"))
            labelNumber.pack(anchor= "w", pady =(5, 1))

            subLabel = tk.Label(card, text= "", bg= bg_colour, fg= fg_colour, font= ("Sans Serif", 10))
            subLabel.pack(anchor= "w")

            return labelNumber, subLabel
            
    # Adding an icon on the header
    tk.Label(header, text = "➤", background= bgSurface, fg= accent, font= ("Sans Serif", 25, "bold")).pack(side= "left", padx=(18,6))

    # Adding title
    tk.Label(header, text= "TIMING DASHBOARD", background= bgSurface, fg = gold, font= ("Sans Serif", 20, "bold")).pack(side= "left")


    tk.Label(header, text= currentDate, background= bgCards, fg = secondaryText, font= ("Sans Serif", 15)).pack(side= "right", padx =20)

    tk.Frame(window, background= gold, height = 2).pack(fill = "x")    

    controls = tk.Frame(header, background= bgSurface)
    controls.pack(side= "right", padx =15, pady = 12)

    programmeFrame = tk.Frame(controls, bg= bgSurface)
    programmeFrame.pack(side= "right", padx =20)

    tk.Label(controls, text= "Programme", background= bgSurface, fg = gold, font = ("Sans Sarif", 10)).pack(side= "left", padx= (0,5))
    programmeSelection = tk.StringVar(value= "ALL")
    dropdownProgramme = ttk.Combobox(programmeFrame, textvariable= programmeSelection, values= programmeList, width= 15, state= "readonly", style="Dark.TCombobox")
    dropdownProgramme.pack(padx= (0,10))

    platformFrame = tk.Frame(controls, bg= bgSurface)
    platformFrame.pack(side = "left", padx =20)

    tk.Label(controls, text = "Platform", background= bgSurface, fg = gold, font = ("Sans Sarif", 10)).pack( padx= (0,5))
    platformSelection = tk.StringVar(value= "ALL")
    dropdownPlatform = ttk.Combobox(platformFrame, textvariable= platformSelection, values = platformList, width = 15, state = "readonly", style= "Dark.TCombobox")
    dropdownPlatform.pack(padx = (0,10))

    # Summary Cards
    cardFrame = tk.Frame(window, background= bgDark)
    cardFrame.pack(fill= "x", padx= 20, pady= 15)

    cardFrame.columnconfigure(0, weight= 1,)
    cardFrame.columnconfigure(1, weight= 1)
    cardFrame.columnconfigure(2, weight= 1)
    cardFrame.columnconfigure(3, weight= 1)


    cardOnTrack, cardOnSub = summary_cards(0,green, textGreen,"ON TRACK")
    cardTotal, cardTotalSub = summary_cards(1, accent, primaryText,"TOTAL")
    cardRisk, cardRiskSub = summary_cards(2, amber, textAmber,"AT RISK")
    cardDelayed, cardDelayedSub = summary_cards(3, red, textRed ,"DELAYED")

    graphCon = tk.Frame(window, bg= bgDark, height= 250)
    graphCon.pack(fill= "x", expand = False, padx= 20, pady= (10,20))
    graphCon.pack_propagate(False)
    graphCon.columnconfigure(0, weight= 1)
    graphCon.columnconfigure(1, weight= 1)
    graphCon.rowconfigure(0, weight=1)

    leftGraph = tk.Frame(graphCon, bg= bgDark)  
    leftGraph.grid(row= 0, column= 0, sticky= "nsew", padx= (0,10))

    rightGraph = tk.Frame(graphCon, bg= bgDark) 
    rightGraph.grid(row= 0, column= 1, sticky= "nsew", padx= (10,0))    

    figure1 = Figure(figsize=(5,2), dpi=80)    
    ax1 = figure1.add_subplot(111)

    canva1 = FigureCanvasTkAgg(figure1, master= leftGraph)
    canva1.get_tk_widget().pack(fill= "both", expand = True)

    figure2 = Figure(figsize=(5,2), dpi=80)
    ax2 = figure2.add_subplot(111)  
    canva2 = FigureCanvasTkAgg(figure2, master= rightGraph) 
    canva2.get_tk_widget().pack(fill="both", expand=True)



    tableFrame = tk.Frame(window, bg= bgDark)
    tableFrame.pack(fill= "both", expand= True, padx =20, pady=(0,15))

    tableCard = tk.Frame(tableFrame, bg= bgDark, highlightthickness= 1, highlightbackground= bgSurface)
    tableCard.pack(fill="both", expand= True)

    tableHeader = tk.Frame(tableCard, bg=bgSurface) 
    tableHeader.pack(fill="x")
    tk.Frame(tableCard, bg= bgSurface, height= 1).pack(fill = "x")


    leftHeader = tk.Frame(tableHeader, bg= bgSurface)
    leftHeader.pack(side= "left", padx= 15, pady= 10)

    tk.Label(leftHeader, text= "Vehicle Timing Report", bg = bgSurface , fg= primaryText, font=("Sans Serif", 10, "bold")).pack(side= "left")

    countLabel = tk.Label(leftHeader, text= "", bg= bgSurface, fg = primaryText, font =("Sans Serif", 10), padx=8, pady= 2)
    countLabel.pack(side= "left", padx= 8)

    rightHeader = tk.Frame(tableHeader, bg= bgSurface)
    rightHeader.pack(side= "right", padx = 12, pady = 8)
    tk.Label(rightHeader, text = "Status", bg = bgSurface, fg = gold , font=("Sans Serif", 10)).pack(side = "left", padx = (0,5))

    status = tk.StringVar(value= "ALL")
    StatDropdown = ttk.Combobox(rightHeader, textvariable= status, values = ["ALL", "On Track", "At Risk", "Delayed"], width = 10, state = "readonly", style="Dark.TCombobox")
    StatDropdown.pack(side = "left", padx= (0,10))


    tk.Label(rightHeader, text = "Search", bg= bgSurface, fg =  gold, font=("Sans Serif", 10)).pack(side="left", padx= (0,5))

    search = tk.StringVar()
    searchBox = tk.Entry(rightHeader, textvariable= search, bg= secondaryText,font= ("Sans Serif", 10), width = 20, relief= "flat")
    searchBox.pack(side= "left")

    columns = ["Programme", "Vehicle", "Platform", "PM Owner", "RAG", "DEADLINE", "Slip", "Days to Deadline"]
    columnsWidth = [90,70,80,80,90,100,70,120]

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", bg= bgDark, fg = primaryText, fieldbackground = bgDark, rowheight = 25, font =("Sans Serif", 10))

    style.configure("Treeview.Heading",bg= bgDark, fg= primaryText, font= ("Sans Serif", 10, "bold"), relief = "flat")
    style.map("Treeview", bg= [("selected", bgSurface)])


    frame = tk.Frame(tableCard, bg= bgDark)
    frame.pack(fill= "both", expand = True)

    style.configure("Dark.Vertical.TScrollbar", bg = bgSurface, troughcolor = bgDark, bordercolor = secondaryText, darkcolor = bgSurface, lightcolor = bgSurface)
    style.map("Dark.Vertical.TScrollbar", background = [("active", secondaryText),("disabled", bgSurface)])


    scrollbar = ttk.Scrollbar(frame, orient="vertical", style="Dark.Vertical.TScrollbar")
    scrollbar.pack(side= "right",fill = "y")

    table = ttk.Treeview(frame, columns= columns, show= "headings", yscrollcommand= scrollbar.set, style= "Treeview")
    scrollbar.config(command = table.yview)

    for col, width in zip(columns, columnsWidth):
            table.heading(col, text = col.upper())
            if col == "PM Owner":
                table.column(col, width= width, minwidth= width, anchor = "w", stretch = True)
            else:
                table.column(col, width = width, minwidth = width, anchor = "w", stretch = False)

    table.pack(fill = "both", expand = True)

    table.tag_configure("On Track", foreground=  green, background=bgDark)
    table.tag_configure("At Risk", foreground = amber, background= bgDark)
    table.tag_configure("Delayed", foreground = red, background= bgDark)

    bottom = tk.Frame(table, bg = bgSurface, height= 40)
    bottom.pack(fill= "x")

    statusBar = tk.Label(bottom, text= "",  bg=bgDark, fg= primaryText, font = ("Sans Serif", 10 ), anchor= "center")
    statusBar.pack(side= "right")

    key = tk.Frame(bottom, bg= bgDark)
    key.pack(side = "right")
    tk.Label(key, text="✅ On Track", bg=bgDark, fg=green, font = ("Sans Serif", 10, "bold")).pack(side = "left")
    tk.Label(key, text="⚠️ At Risk", bg=bgDark, fg= amber, font = ("Sans Serif", 10, "bold")).pack(side = "left")
    tk.Label(key, text="❗Delayed", bg=bgDark, fg=textRed, font = ("Sans Serif", 10, "bold")).pack(side = "left")


    def updateTable(*args):
        
        filtered = df.copy()
        
            

        programmeSelect = programmeSelection.get()
        if programmeSelect != "ALL":
            filtered = filtered[filtered["Programme_ID"] == programmeSelect]
            
        platformSelect = platformSelection.get()
        if platformSelect != "ALL":
            filtered = filtered[filtered["Platform_Name"] == platformSelect]

        selectedStatus = status.get()
        if selectedStatus != "ALL":
            filtered = filtered[filtered["Project_Status"] == selectedStatus]


        searchText = search.get().lower()
        if  searchText != "":
            find = (
                filtered["Platform_Name"].str.lower().str.contains(searchText, na= False)|
                filtered["Vehicle_Code"].str.lower().str.contains(searchText, na= False)|
                filtered["PM_Owner"].str.lower().str.contains(searchText, na= False)
                ) 
            filtered = filtered[find]


        total = len(filtered)
        onTrack = len(filtered[filtered["Project_Status"] == "On Track"])
        atRisk = len(filtered[filtered["Project_Status"] == "At Risk"])
        delayed = len(filtered[filtered["Project_Status"] == "Delayed"])
        numOfProgrammes = filtered["Programme_ID"].nunique()

        if total > 0 :
            avg_slip = round(filtered["slip_time"].mean(),0)
        else:
            avg_slip = 0 

        cardOnTrack.config(text = str(onTrack))
        cardOnSub.config(text = str(round(onTrack/ total * 100)) + "%")

        cardTotal.config(text = str(total))
        cardTotalSub.config(text = str(numOfProgrammes) + " Programmes")

        cardRisk.config(text = str(atRisk))
        cardRiskSub.config(text = str(round(atRisk / total * 100)) + "%")

        cardDelayed.config(text= str(delayed))
        cardDelayedSub.config(text = "avg slip " + str(avg_slip) + " days")

        countLabel.config(text = total)

        for rows in table.get_children():
            table.delete(rows)

        i = 0
        for index, row in filtered.iterrows():
            
            tag = row["Project_Status"]

            if pd.notna(row["Approved_Programme_Completion"]):
                deadline = row["Approved_Programme_Completion"].strftime("%d %b %Y")
            else:
                deadline = "--"

            table.insert("", "end", tags = (tag,), values= (
                row["Programme_ID"],
                row["Vehicle_Code"],
                row["Platform_Name"],
                row["PM_Owner"],
                rag_status(row["Project_Status"]),
                deadline,
                formatting_slip(row["slip_time"]),
                formatting_dtd(row["dtd"])
                ))

            i = i + 1


        # Trend Graph
        ax1.clear()

        trenddf = filtered.copy()
        trenddf = trenddf.dropna(subset=["Approved_Programme_Completion"])

        trenddf["Month"] = trenddf["Approved_Programme_Completion"].dt.to_period("M")
        monthly = trenddf.groupby("Month")["slip_time"].mean().reset_index()
        monthly["Month"] = monthly["Month"].dt.to_timestamp()

        if len(monthly) > 0:
            ax1.plot(
                monthly["Month"],
                monthly["slip_time"],
                marker="o",
                linestyle="-",
                linewidth=2
            )

        ax1.set_title(
            "Slip Time Trend",
            color=primaryText,
            fontsize=12,
            fontweight="bold"
        )

        ax1.set_facecolor(bgDark)
        figure1.patch.set_facecolor(bgDark)

        for spine in ax1.spines.values():
            spine.set_visible(False)

        ax1.tick_params(colors=primaryText)
        ax1.grid(axis="y", linestyle="--", alpha=0.3)

        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
        figure1.autofmt_xdate()

        canva1.draw()
        # Pie Chart
        ax2.clear()

        labels = ["On Track", "At Risk", "Delayed"]
        values = [onTrack, atRisk, delayed]

        if sum(values) > 0:
            ax2.pie(
                values,
                labels=labels,
                colors=[green, amber, red],
                autopct="%1.1f%%",
                pctdistance=1.1,
                labeldistance=1.5,
                startangle=90,
                textprops={"color": primaryText},
                wedgeprops = {"width": 0.4}
            )

        ax2.set_title(
            "Project Status Distribution",
            color=primaryText,
            fontsize=12,
            fontweight="bold"
        )

        ax2.set_facecolor(bgDark)
        figure2.patch.set_facecolor(bgDark)

        canva2.draw()

    dropdownProgramme.bind("<<ComboboxSelected>>", updateTable)
    dropdownPlatform.bind("<<ComboboxSelected>>", updateTable)
    StatDropdown.bind("<<ComboboxSelected>>", updateTable)
    search.trace_add("write", updateTable)


    updateTable()
    window.mainloop()

dashboard()
