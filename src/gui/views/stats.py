import customtkinter as ctk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from ..theme import THEME

class StatsView(ctk.CTkFrame):
    """
    Frame for displaying long-term statistics with graphs.
    """
    def __init__(self, master, app_instance, stats_manager):
        super().__init__(master, fg_color=THEME["bg_dark"])
        self.app = app_instance
        self.stats_manager = stats_manager
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Graph expands
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="Performance Analytics", font=("Roboto", 24, "bold"), text_color=THEME["text_primary"]).pack(side="left")
        
        # --- Controls (Date Range & Metric) ---
        controls = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Date Selection
        date_frame = ctk.CTkFrame(controls, fg_color="transparent")
        date_frame.pack(side="left", padx=20, pady=15)
        
        today = datetime.now()
        start_def = (today - timedelta(days=14)).strftime("%Y-%m-%d")
        end_def = today.strftime("%Y-%m-%d")
        
        ctk.CTkLabel(date_frame, text="From:", text_color=THEME["text_secondary"]).pack(side="left", padx=5)
        self.start_date = ctk.CTkEntry(date_frame, width=100, fg_color=THEME["bg_dark"], text_color=THEME["text_primary"])
        self.start_date.insert(0, start_def)
        self.start_date.pack(side="left", padx=5)
        
        ctk.CTkLabel(date_frame, text="To:", text_color=THEME["text_secondary"]).pack(side="left", padx=5)
        self.end_date = ctk.CTkEntry(date_frame, width=100, fg_color=THEME["bg_dark"], text_color=THEME["text_primary"])
        self.end_date.insert(0, end_def)
        self.end_date.pack(side="left", padx=5)
        
        ctk.CTkButton(date_frame, text="Update", width=60, command=self.refresh_stats, 
                      fg_color=THEME["btn_primary"], text_color=("white", "black")).pack(side="left", padx=10)

        # Metric Toggle
        self.metric_var = ctk.StringVar(value="cph")
        self.metric_seg = ctk.CTkSegmentedButton(controls, values=["cph", "aht", "volume", "kpm", "cpm"], variable=self.metric_var, command=self.on_filter_change)
        self.metric_seg.pack(side="right", padx=20, pady=15)
        self.metric_seg.set("cph")
        
        # --- Graph Area & Cards ---
        # Split vertical space: Top = Cards, Bottom = Graph
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # KPI Cards (Top of content)
        self.kpi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.kpi_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.kpi_frame.columnconfigure((0,1,2,3,4), weight=1)
        
        self.card_cph = self.create_kpi_card(self.kpi_frame, "Avg CPH", "0.0", 0)
        self.card_aht = self.create_kpi_card(self.kpi_frame, "Avg AHT", "0.0", 1)
        self.card_vol = self.create_kpi_card(self.kpi_frame, "Volume", "0", 2)
        self.card_kpm = self.create_kpi_card(self.kpi_frame, "Avg KPM", "0.0", 3)
        self.card_cpm = self.create_kpi_card(self.kpi_frame, "Avg CPM", "0.0", 4)
        
        # Graph (Bottom of content)
        self.graph_container = ctk.CTkFrame(self.content_frame, fg_color=THEME["bg_card"], corner_radius=10)
        self.graph_container.grid(row=1, column=0, sticky="nsew")
        
        # Matplotlib setup
        # Use dark background for plot
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        
        # Theme colors are tuples (Light, Dark). Matplotlib needs a single string.
        # Since we use dark_background style, we use the dark theme color (index 1).
        bg_color = THEME["bg_card"][1]
        
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial Draw
        self.refresh_stats()
        
    def create_kpi_card(self, parent, title, value, col, row=0):
        frame = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=10)
        frame.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(frame, text=title, font=("Roboto", 12), text_color=THEME["text_secondary"]).pack(pady=(10, 2))
        val_lbl = ctk.CTkLabel(frame, text=value, font=("Roboto", 18, "bold"), text_color=THEME["accent"])
        val_lbl.pack(pady=(0, 10))
        return val_lbl

    def on_filter_change(self, _=None):
        self.refresh_stats()

    def refresh_stats(self):
        try:
            s_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
            e_date = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
        except ValueError:
            # Fallback if invalid date
            today = datetime.now()
            s_date = today - timedelta(days=14)
            e_date = today
        
        metric = self.metric_var.get()
        
        # fetch data
        stats = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric=metric)
        
        # Also fetch summary stats for cards for this range
        cph_data = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric="cph")
        aht_data = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric="aht")
        vol_data = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric="volume")
        kpm_data = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric="kpm")
        cpm_data = self.stats_manager.get_stats_range(s_date, e_date, period="day", metric="cpm")
        
        def avg(data):
            vals = [v for _, v in data if v > 0]
            if not vals: return 0.0
            return sum(vals) / len(vals)

        def total(data):
            return sum([v for _, v in data])

        self.card_cph.configure(text=f"{avg(cph_data):.1f}")
        self.card_aht.configure(text=f"{avg(aht_data):.1f}")
        self.card_vol.configure(text=str(int(total(vol_data))))
        self.card_kpm.configure(text=f"{avg(kpm_data):.0f}")
        self.card_cpm.configure(text=f"{avg(cpm_data):.0f}")

        # Update Plot
        self.ax.clear()
        
        if not stats:
            self.ax.text(0.5, 0.5, "No Data", ha='center', va='center', color='white')
        else:
            labels = [x[0] for x in stats]
            values = [x[1] for x in stats]
            x_pos = range(len(labels))
            
            # Line Chart with Points
            self.ax.plot(x_pos, values, marker='o', linestyle='-', linewidth=2, color='#61afef', label=metric.upper())
            
            # Fill area under line for "upstream/downstream" feel
            self.ax.fill_between(x_pos, values, alpha=0.3, color='#61afef')
            
            # Graphical Average Line
            average_val = avg(stats)
            self.ax.axhline(y=average_val, color='#e06c75', linestyle='--', label=f'Avg: {average_val:.1f}')
            
            # Target Line
            try:
                target_cph = float(self.app.config.get("target_cph", 7.5))
                target_val = None
                
                if metric == "cph":
                    target_val = target_cph
                elif metric == "aht":
                    # Target AHT (minutes) = 60 / Target CPH
                    if target_cph > 0:
                        target_val = 60 / target_cph
                        
                if target_val is not None:
                    # Green dotted line for target
                    self.ax.axhline(y=target_val, color='#98c379', linestyle=':', linewidth=2, label=f'Target: {target_val:.1f}')
            except Exception as e:
                print(f"Error drawing target line: {e}")
            
            # Formatting
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(labels, rotation=45, ha='right')
            self.ax.set_title(f"{metric.upper()} Trend", color='white')
            # Custom grid
            self.ax.grid(True, linestyle=':', alpha=0.4)
            self.ax.tick_params(colors='white')
            for spine in self.ax.spines.values():
                spine.set_color('#444')
            
            # Use dark theme color for legend background
            bg_color = THEME["bg_card"][1]
            self.ax.legend(facecolor=bg_color, edgecolor="none", labelcolor="white")
            self.fig.tight_layout()

        self.canvas.draw()

