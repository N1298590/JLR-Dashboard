import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


def make_line_chart(ax):
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), color="#4A90D9", linewidth=2)
    ax.set_title("Line Chart", fontsize=10, fontweight="bold")
    ax.set_facecolor("#F7F9FC")

def make_bar_chart(ax):
    categories = ["A", "B", "C", "D", "E"]
    values = np.random.randint(10, 100, size=5)
    ax.bar(categories, values, color=["#E74C3C","#3498DB","#2ECC71","#F39C12","#9B59B6"])
    ax.set_title("Bar Chart", fontsize=10, fontweight="bold")
    ax.set_facecolor("#F7F9FC")

def make_scatter_chart(ax):
    x = np.random.randn(80)
    y = np.random.randn(80)
    ax.scatter(x, y, c="#E74C3C", alpha=0.6, s=30)
    ax.set_title("Scatter Plot", fontsize=10, fontweight="bold")
    ax.set_facecolor("#F7F9FC")

def make_pie_chart(ax):
    sizes = [25, 20, 30, 15, 10]
    labels = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    colors = ["#4A90D9","#E74C3C","#2ECC71","#F39C12","#9B59B6"]
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", textprops={"fontsize": 7})
    ax.set_title("Pie Chart", fontsize=10, fontweight="bold")

def make_histogram(ax):
    data = np.random.normal(50, 15, 300)
    ax.hist(data, bins=20, color="#2ECC71", edgecolor="white")
    ax.set_title("Histogram", fontsize=10, fontweight="bold")
    ax.set_facecolor("#F7F9FC")

def make_area_chart(ax):
    x = np.linspace(0, 10, 100)
    y = np.abs(np.sin(x) * np.cos(x / 2))
    ax.fill_between(x, y, alpha=0.5, color="#F39C12")
    ax.plot(x, y, color="#E67E22", linewidth=1.5)
    ax.set_title("Area Chart", fontsize=10, fontweight="bold")
    ax.set_facecolor("#F7F9FC")

CHARTS = [make_line_chart, make_bar_chart, make_scatter_chart,
          make_pie_chart, make_histogram, make_area_chart]

def on_button_click(idx):
    print(f"Button {BUTTON_NAME[idx]} clicked!")

BUTTON_NAME =  ['Quality WCPA', 'Supplier Readiness', 'timing',
                'Customer waiting list', 'feature readiness', ' button']


root = tk.Tk()
root.title("6 Graph Dashboard")
root.configure(bg="#2C3E50")
root.geometry("900x600")   # fixed window size — adjust to taste
root.resizable(True, True)

title_lbl = tk.Label(root, text="📊  Graph Dashboard", font=("Georgia", 14, "bold"),
                     bg="#2C3E50", fg="#ECF0F1", pady=6)
title_lbl.grid(row=0, column=0, columnspan=3)

for i, chart_func in enumerate(CHARTS):
    row, col = divmod(i, 3)
    frame = tk.Frame(root, bg="#34495E", bd=2, relief="flat",
                     highlightbackground="#4A90D9", highlightthickness=1)
    frame.grid(row=row * 2 + 1, column=col, padx=8, pady=(5, 0), sticky="nsew")

    fig, ax = plt.subplots(figsize=(2.6, 1.9), dpi=85)
    fig.patch.set_facecolor("#34495E")
    chart_func(ax)
    fig.tight_layout(pad=1.2)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

    btn = tk.Button(root, text=BUTTON_NAME[i],
                    font=("Helvetica", 9, "bold"),
                    bg="#4A90D9", fg="Black",
                    activebackground="#2980B9", activeforeground="white",
                    relief="flat", padx=12, pady=3, cursor="hand2",
                    command=lambda idx=i: on_button_click(idx))
    btn.grid(row=row * 2 + 2, column=col, pady=(3, 8))

for c in range(3):
    root.columnconfigure(c, weight=1)

root.mainloop()