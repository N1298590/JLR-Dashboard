import pandas as pd
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# create class and group everything into an object
class Dashboard:
    def __init__(self, root):  # makes code run automatically on startup
        self.root = root  # makes window tiles with appropriate size and colour
        self.root.title("Quality WCPA Dashboard")
        self.root.geometry("1400x800")
        self.root.configure(bg="#0F172A")

        self.df = self.load_data()  # pie chart click tracker and separates full dataset from what's currently viewed
        self.filtered_df = self.df.copy()
        self.active_component_group_filter = None

        self.setup_layout()
        self.update_display(self.df)  # builds ui and fills with data

    def on_button_click(self):
        self.root.destroy()


    def load_data(self):  # loading data
        df = pd.read_excel("Data set examples_Main.xlsx")
        df.columns = df.columns.str.strip()
        df = df[df['Programme_ID'].notna()]  # removes irrelevant data
        df = df[df['Score'].notna()]
        df = df.drop(columns=[c for c in df.columns if 'Unnamed' in str(c)], errors='ignore')

        df['Programme_ID'] = df['Programme_ID'].astype(str).str.replace('prg_', '', case=False,
                                                                        regex=True).str.strip()  # cleans up ui by removing the repeated characters
        df["Component_Group"] = df["Component"].apply(self.group_component)  # makes clean groups
        return df.reset_index(drop=True)

    def group_component(self, comp):  # maps names to categories to remove clutter
        c = str(comp).lower()
        if any(k in c for k in ["brake", "steering", "suspension", "chassis"]):
            return "Chassis & Dynamics"
        if any(k in c for k in ["electrical", "power electronics", "wiring", "sensor", "display"]):
            return "Electrical & Electronics"
        if any(k in c for k in ["infotainment", "software", "control software"]):
            return "Software & Infotainment"
        if any(k in c for k in ["interior", "trim", "lighting", "seating", "hvac"]):
            return "Interior Systems"
        if any(k in c for k in ["assembly", "fixture", "tool", "manufacturing", "fastener"]):
            return "Manufacturing"
        if any(k in c for k in ["battery", "powertrain", "charging"]):
            return "Powertrain & Energy"
        return "Other"

    def setup_layout(self):  # builds everything on screen
        sidebar = tk.Frame(self.root, bg="#1E293B", width=250)  # creates sidebar
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(sidebar, text="◀  BACK", bg='#21262D', fg='#58A6FF',
                  font=("Courier New", 8, "bold"), bd=0, padx=10, pady=6,
                  activebackground="#161B22", activeforeground='#E6EDF3',
                  cursor="hand2",
                  command=self.on_button_click).pack(side="left", padx=(10, 4), pady=8)

        self.create_dropdown(sidebar, "Programme", "Programme_ID")  # dropdowns for ui
        self.create_dropdown(sidebar, "Component", "Component")
        self.create_dropdown(sidebar, "Assignee", "Assignee")
        self.create_dropdown(sidebar, "Programme Phase", "Programme_Phase")

        tk.Button(sidebar, text="Apply Filter", command=self.apply_filter,
                  bg="#3B82F6", fg="black").pack(pady=10)

        main = tk.Frame(self.root, bg="#0F172A")
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        kpi_frame = tk.Frame(main, bg="#0F172A")  # KPI
        kpi_frame.pack(fill=tk.X, pady=10)

        self.kpi_labels = []  # shows total issues average scoe and high risk issues
        for i in range(3):
            frame = tk.Frame(kpi_frame, bg="#1E293B", width=180, height=70)
            frame.pack(side=tk.LEFT, padx=10)
            frame.pack_propagate(False)
            label = tk.Label(frame, text="", bg="#1E293B",
                             fg="white", font=("Arial", 11, "bold"))
            label.pack(expand=True)
            self.kpi_labels.append(label)

        table_frame = tk.Frame(main)  # creates excel style table
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scroll_y = tk.Scrollbar(table_frame, orient=tk.VERTICAL)  # x and y axis scrollbars
        scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(
            table_frame,
            columns=list(self.df.columns),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Column widths sized to fit content
        col_widths = {
            'Programme_ID': 100,
            'Vehicle_Code': 90,
            'Platform_Name': 130,
            'Programme_Phase': 130,
            'Assignee': 110,
            'Process_Owner': 120,
            'Component': 160,
            'Concern': 260,
            'Comment': 260,
            'Score': 60,
            'Component_Group': 160,
        }
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 110), minwidth=60)
        self.tree.tag_configure('high_risk', background='#7f1d1d', foreground='white')  # highlights high risk

        graph_container = tk.Frame(main, bg="#0F172A")
        graph_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # make first figure wider to give legend room
        self.fig1 = Figure(figsize=(4.2, 3), facecolor="#1E293B")  # pie chart, bar chart, histogram
        self.fig2 = Figure(figsize=(3, 2.5), facecolor="#1E293B")
        self.fig3 = Figure(figsize=(3, 2.5), facecolor="#1E293B")

        self.ax1 = self.fig1.add_subplot(111)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax3 = self.fig3.add_subplot(111)

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=graph_container)  # embeds to tkinter
        self.canvas1.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=graph_container)
        self.canvas2.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=graph_container)
        self.canvas3.get_tk_widget().pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.fig1.canvas.mpl_connect("pick_event", self.on_pie_pick)  # enables pie chart click

    def create_dropdown(self, parent, label, column):  # filters
        tk.Label(parent, text=label, bg="#1E293B", fg="white").pack()
        var = tk.StringVar()
        box = ttk.Combobox(parent, textvariable=var, state="readonly")
        box['values'] = ["All"] + sorted(self.df[column].dropna().unique())
        box.current(0)
        box.pack(pady=5)
        setattr(self, f"{column}_var", var)

    def apply_filter(self):
        filtered = self.df.copy()
        for col in ["Programme_ID", "Component", "Assignee", "Programme_Phase"]:
            val = getattr(self, f"{col}_var").get()
            if val != "All":
                filtered = filtered[filtered[col] == val]
        if self.active_component_group_filter is not None:  # adds filtering from pie chart click
            filtered = filtered[filtered['Component_Group'] == self.active_component_group_filter]
        self.update_display(filtered)

    def update_display(self, data):  # updates table, kpi and graphs
        self.update_table(data)
        self.update_kpis(data)
        self.update_graphs(data)

    def update_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for _, row in data.iterrows():
            tag = 'high_risk' if row['Score'] >= 4 else ''  # marks high risk rows
            self.tree.insert("", "end", values=list(row), tags=(tag,))  # adds rows to table

    def update_kpis(self, data):
        total = len(data)
        avg = round(data['Score'].mean(), 2) if total else 0
        high = len(data[data['Score'] >= 4])
        self.kpi_labels[0].config(text=f"Total\n{total}")
        self.kpi_labels[1].config(text=f"Avg Score\n{avg}")
        self.kpi_labels[2].config(text=f"High Risk\n{high}")

    def update_graphs(self, data):
        self.ax1.clear()  # clears old graphs before redrawing
        self.ax2.clear()
        self.ax3.clear()
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor("#1E293B")
            ax.tick_params(colors='white', labelsize=8)

        if len(data) > 0:
            counts = data['Component_Group'].value_counts()

            # stable palette
            colors = self.get_palette(len(counts))

            wedges, texts, autotexts = self.ax1.pie(  # draws pie chart
                counts,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                radius=0.75,
                textprops={'color': 'white', 'fontsize': 8},
                colors=colors
            )

            self.ax1.set_title("Components", color="white", fontsize=10)
            self.ax1.set_aspect('equal')

            self.pie_original_colors = []
            for w, c in zip(wedges, colors):
                w.set_picker(True)  # makes slices clickable
                w.set_edgecolor('white')
                w.set_linewidth(0.8)
                self.pie_original_colors.append(c)

            self.ax1.legend(  # creates a legend for pie chart
                counts.index,
                loc="center left",
                bbox_to_anchor=(0.78, 0.5),
                fontsize=7,
                labelcolor="white"
            )

            self.pie_wedges = wedges
            self.pie_labels = list(counts.index)

            # visual highlight for active filter: preserve selected wedge color, dim others
            for i, w in enumerate(self.pie_wedges):
                if self.active_component_group_filter is None:
                    w.set_alpha(1.0)
                    w.set_linewidth(0.8)
                else:
                    if self.pie_labels[i] == self.active_component_group_filter:
                        w.set_alpha(1.0)
                        w.set_linewidth(2.0)
                    else:
                        w.set_alpha(0.35)
                        w.set_linewidth(0.8)

            # bar and histogram
            data['Programme_ID'].value_counts().plot(kind='bar', ax=self.ax2,
                                                     color='#60A5FA')  # shows issues per program
            self.ax2.set_xlabel("Programme", color="white", fontsize=9)
            self.ax2.set_ylabel("Count", color="white", fontsize=9)
            self.ax2.set_title("Issues by Programme", color="white", fontsize=10)
            self.ax2.tick_params(axis='x', rotation=45, colors='white')

            self.ax3.hist(data['Score'], bins=5, color='#34D399')  # shows distribution of scores
            self.ax3.set_xlabel("Score", color="white", fontsize=9)
            self.ax3.set_ylabel("Frequency", color="white", fontsize=9)
            self.ax3.set_title("Score Distribution", color="white", fontsize=10)

        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

    def get_palette(self, n):
        import matplotlib.pyplot as plt
        if n <= 10:
            cmap = plt.get_cmap('tab10')
        else:
            cmap = plt.get_cmap('tab20')
        return [cmap(i) for i in range(n)]

    def on_pie_pick(self, event):
        wedge = event.artist
        try:
            idx = self.pie_wedges.index(wedge)
        except ValueError:
            return
        label = self.pie_labels[idx]

        # toggle filter
        if self.active_component_group_filter == label:
            self.active_component_group_filter = None
        else:
            self.active_component_group_filter = label

        # keep clicked wedge color, emphasize it; dim others
        for i, w in enumerate(self.pie_wedges):
            w.set_facecolor(self.pie_original_colors[i])  # ensure original color retained
            if self.active_component_group_filter is None:
                w.set_alpha(1.0)
                w.set_linewidth(0.8)
            else:
                if self.pie_labels[i] == self.active_component_group_filter:
                    w.set_alpha(1.0)
                    w.set_linewidth(2.2)
                else:
                    w.set_alpha(0.25)
                    w.set_linewidth(0.8)

        self.apply_filter()
        self.canvas1.draw()


if __name__ == "__main__":  # starts app
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()