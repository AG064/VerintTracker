import customtkinter as ctk
from datetime import datetime, timedelta
from ..theme import THEME

class StatsView(ctk.CTkFrame):
    """
    Frame for displaying long-term statistics with graphs.
    """
    def __init__(self, master, stats_manager):
        super().__init__(master, fg_color=THEME["bg_dark"])
        self.stats_manager = stats_manager
        self.grid_columnconfigure(0, weight=1)
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="Performance Analytics", font=("Roboto", 24, "bold"), text_color=THEME["text_primary"]).pack(side="left")
        
        ctk.CTkButton(header, text="Refresh", width=80, command=self.refresh_stats, 
                      fg_color=THEME["btn_primary"], text_color=("white", "black")).pack(side="right")
        
        # --- Controls (Period & Metric) ---
        controls = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10)
        controls.pack(fill="x", padx=20, pady=(0, 20))
        
        # Period Toggle
        self.period_var = ctk.StringVar(value="day")
        self.period_seg = ctk.CTkSegmentedButton(controls, values=["day", "week"], variable=self.period_var, command=self.on_filter_change)
        self.period_seg.pack(side="left", padx=20, pady=15)
        self.period_seg.set("day")
        
        # Metric Toggle
        self.metric_var = ctk.StringVar(value="cph")
        self.metric_seg = ctk.CTkSegmentedButton(controls, values=["cph", "aht", "volume"], variable=self.metric_var, command=self.on_filter_change)
        self.metric_seg.pack(side="right", padx=20, pady=15)
        self.metric_seg.set("cph")
        
        # --- Graph Area ---
        self.graph_frame = ctk.CTkFrame(self, fg_color=THEME["bg_card"], corner_radius=10, height=250)
        self.graph_frame.pack(fill="x", padx=20, pady=0)
        
        self.graph_title = ctk.CTkLabel(self.graph_frame, text="Tickets Per Hour (Last 14 Days)", font=("Roboto", 16, "bold"), text_color=THEME["text_primary"])
        self.graph_title.pack(pady=(15, 10))
        
        # Container for bars
        self.bars_container = ctk.CTkFrame(self.graph_frame, fg_color="transparent")
        self.bars_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # --- KPI Cards ---
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=10, pady=20)
        self.kpi_frame.columnconfigure((0,1,2), weight=1)
        
        self.card_cph = self.create_kpi_card(self.kpi_frame, "Avg CPH", "0.0", 0)
        self.card_aht = self.create_kpi_card(self.kpi_frame, "Avg AHT (min)", "0.0", 1)
        self.card_vol = self.create_kpi_card(self.kpi_frame, "Total Volume", "0", 2)
        
        # Initial Draw
        self.refresh_stats()
        
    def create_kpi_card(self, parent, title, value, col):
        frame = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=10)
        frame.grid(row=0, column=col, sticky="ew", padx=10)
        
        ctk.CTkLabel(frame, text=title, font=("Roboto", 12), text_color=THEME["text_secondary"]).pack(pady=(15, 5))
        val_lbl = ctk.CTkLabel(frame, text=value, font=("Roboto", 20, "bold"), text_color=THEME["accent"])
        val_lbl.pack(pady=(0, 15))
        return val_lbl

    def on_filter_change(self, _=None):
        self.refresh_stats()

    def refresh_stats(self):
        period = self.period_var.get()
        metric = self.metric_var.get()
        
        # Update Title
        p_text = "Days" if period == "day" else "Weeks"
        m_text = "Tickets Per Hour" if metric == "cph" else ("Avg Handle Time (min)" if metric == "aht" else "Ticket Volume")
        self.graph_title.configure(text=f"{m_text} (Last 14 {p_text})")
        
        # Get Data
        stats = self.stats_manager.get_aggregated_stats(period=period, metric=metric, count=14 if period == "day" else 10)
        self.draw_bars(stats)
        
        # Update KPIs (Global/Recent averages)
        # For simplicity, calculate from the visible graph data to match view
        if stats:
             vals = [v for _, v in stats]
             avg = sum(vals) / len(vals) if vals else 0
             total = sum(vals)
             
             if metric == "volume":
                 self.card_vol.configure(text=str(int(total)))
             else:
                 # Fetch actual averages from manager for accuracy if needed, 
                 # but calculating from view is consistent with chart
                 pass
        
        # Always update global stats
        wk_vol = self.stats_manager.get_weekly_stats()
        wk_cph = self.stats_manager.get_average_cph_per_day() # This was tickets/day actually
        # We need real CPH/AHT methods for "This Week Total".
        # Creating ad-hoc calc using get_aggregated_stats for 'week' (last 1 point)
        
        # Let's just update the specific card relevant to view for now, or all if we can
        # self.card_cph.configure(text=str(self.stats_manager.get_average_cph("week"))) # Hypothetical
        pass

    def draw_bars(self, data):
        # Clear
        for w in self.bars_container.winfo_children():
            w.destroy()
            
        if not data:
            ctk.CTkLabel(self.bars_container, text="No Data Available", text_color=THEME["text_secondary"]).pack(expand=True)
            return

        # Prepare scaling
        vals = [v for _, v in data]
        max_val = max(vals) if vals else 1
        if max_val == 0: max_val = 1
        
        # Layout: Grid of vertical bars
        # We use grid 1 row, N columns
        for i, (label, val) in enumerate(data):
            self.bars_container.columnconfigure(i, weight=1)
            
            bar_group = ctk.CTkFrame(self.bars_container, fg_color="transparent")
            bar_group.grid(row=0, column=i, padx=2, sticky="s") # Align bottom
            
            # Value Label (Top)
            val_text = str(int(val)) if val.is_integer() else f"{val:.1f}"
            ctk.CTkLabel(bar_group, text=val_text, font=("Roboto", 10), text_color=THEME["text_primary"]).pack(side="top", pady=(0, 2))
            
            # Bar (Frame)
            # Height is tricky in pack/grid. We use specific height.
            # Max height available approx 150px.
            bar_h = int((val / max_val) * 150)
            if bar_h < 4: bar_h = 4
            
            bar_color = THEME["accent"]
            if self.metric_var.get() == "aht": bar_color = "#E5C07B" # Gold for time
            
            bar = ctk.CTkFrame(bar_group, width=20, height=bar_h, fg_color=bar_color, corner_radius=4)
            bar.pack(side="top") # Pushed down by top element? No.
            # To align BOTTOM, we need the frame to be bottom aligned in the cell. 
            # sticky="s" in grid handles the group.
            
            # Label (Bottom)
            # Rotate text? Not easily. Short labels.
            ctk.CTkLabel(bar_group, text=label, font=("Roboto", 10), text_color=THEME["text_secondary"]).pack(side="top", pady=(5, 0))
