import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Union
from collections import defaultdict

class StatsManager:
    def __init__(self, filepath="ticket_stats.json"):
        self.filepath = filepath
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load data from JSON file, creating it if it doesn't exist."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    # Ensure structure
                    if "tickets" not in data: data["tickets"] = []
                    
                    # Migration: Convert string timestamps to dicts
                    migrated_tickets = []
                    for t in data["tickets"]:
                        if isinstance(t, str):
                            migrated_tickets.append({"timestamp": t, "has_reply": True})
                        else:
                            migrated_tickets.append(t)
                    data["tickets"] = migrated_tickets
                    
                    if "activity" not in data: data["activity"] = {}
                    return data
            except Exception as e:
                print(f"Error loading stats: {e}")
                return {"tickets": [], "activity": {}}
        return {"tickets": [], "activity": {}}
        
    def _calculate_daily_metrics(self):
        """Calculate and update derived metrics (CPH, AHT) for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["activity"]:
            return

        stats = self.data["activity"][today]
        duration_seconds = stats.get("duration", 0)
        duration_hours = duration_seconds / 3600.0
        
        # Count tickets for today
        ticket_count = 0
        for t in self.data["tickets"]:
             # Handle both string and dict formats (though _load_data normalizes to dicts)
            ts = t["timestamp"] if isinstance(t, dict) else t
            if ts.startswith(today):
                ticket_count += 1
        
        # Update stats
        stats["ticket_count"] = ticket_count
        
        if duration_hours > 0:
            stats["cph"] = round(ticket_count / duration_hours, 2)
        else:
            stats["cph"] = 0.0
            
        if ticket_count > 0:
            stats["aht"] = round(duration_seconds / ticket_count, 2)
        else:
            stats["aht"] = 0.0

    def _save_data(self):
        # Ensure metrics are up-to-date before saving
        self._calculate_daily_metrics()
        
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
            
    def log_ticket(self, has_reply=True):
        """Log a ticket completion at the current time."""
        timestamp = datetime.now().isoformat()
        self.data["tickets"].append({"timestamp": timestamp, "has_reply": has_reply})
        self._save_data()
        return timestamp

    def update_activity(self, keys, clicks, duration_seconds):
        """Update activity stats for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["activity"]:
            self.data["activity"][today] = {"keys": 0, "clicks": 0, "duration": 0}
            
        self.data["activity"][today]["keys"] += keys
        self.data["activity"][today]["clicks"] += clicks
        self.data["activity"][today]["duration"] += duration_seconds
        self._save_data()

    def get_activity_stats(self, period="today"):
        """Get activity stats for a period (today, week, month)."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        if period == "today":
            return self.data["activity"].get(today_str, {"keys": 0, "clicks": 0, "duration": 0})
            
        start_date = None
        if period == "week":
            start_date = now - timedelta(days=now.weekday())
        elif period == "month":
            start_date = now.replace(day=1)
            
        if start_date:
            total_keys = 0
            total_clicks = 0
            total_duration = 0
            
            for date_str, stats in self.data["activity"].items():
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if date_obj >= start_date.replace(hour=0, minute=0, second=0, microsecond=0):
                    total_keys += stats.get("keys", 0)
                    total_clicks += stats.get("clicks", 0)
                    total_duration += stats.get("duration", 0)
                    
            return {"keys": total_keys, "clicks": total_clicks, "duration": total_duration}
            
        return {"keys": 0, "clicks": 0, "duration": 0}

    def get_average_kpm(self, period="week"):
        """Calculate average KPM for a period."""
        stats = self.get_activity_stats(period)
        minutes = stats["duration"] / 60
        if minutes < 1: return 0
        return int(stats["keys"] / minutes)

    def get_average_clicks_per_minute(self, period="week"):
        """Calculate average Clicks/Min for a period."""
        stats = self.get_activity_stats(period)
        minutes = stats["duration"] / 60
        if minutes < 1: return 0
        return int(stats["clicks"] / minutes)

        
    def get_tickets_for_range(self, start_date, end_date):
        """Get tickets between start_date and end_date (inclusive)."""
        tickets = []
        for ticket in self.data["tickets"]:
            # Handle potential legacy data if _load_data didn't catch it (safety)
            if isinstance(ticket, str):
                t_str = ticket
            else:
                t_str = ticket["timestamp"]
                
            t = datetime.fromisoformat(t_str)
            if start_date <= t <= end_date:
                tickets.append(t)
        return tickets
        
    def get_daily_stats(self):
        """Return dictionary of {date_str: count}."""
        stats = defaultdict(int)
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str):
                t_str = ticket
                has_reply = True
            else:
                t_str = ticket["timestamp"]
                has_reply = ticket.get("has_reply", True)
            
            if has_reply:
                date_str = t_str.split('T')[0]
                stats[date_str] += 1
        return dict(stats)
        
    def get_current_session_cph(self, session_start_time):
        """Calculate CPH for the current session."""
        now = datetime.now()
        duration_hours = (now - session_start_time).total_seconds() / 3600
        
        # Count tickets since session start
        count = 0
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str):
                t_str = ticket
                has_reply = True
            else:
                t_str = ticket["timestamp"]
                has_reply = ticket.get("has_reply", True)
                
            t = datetime.fromisoformat(t_str)
            if t >= session_start_time and has_reply:
                count += 1
                
        if duration_hours < 0.01: # Avoid division by zero or tiny numbers
            return 0.0
            
        return round(count / duration_hours, 2)
        
    def get_average_cph_per_day(self):
        """Calculate average tickets per day (for days with activity)."""
        daily = self.get_daily_stats()
        if not daily:
            return 0.0
        
        total_tickets = sum(daily.values())
        total_days = len(daily)
        
        # Note: This is tickets per day, not CPH. 
        # CPH requires knowing hours worked per day.
        # We will return tickets/day for now as a proxy or "Daily Volume".
        return round(total_tickets / total_days, 1)

    def get_weekly_stats(self):
        """Return tickets count for current week."""
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = 0
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str):
                t_str = ticket
                has_reply = True
            else:
                t_str = ticket["timestamp"]
                has_reply = ticket.get("has_reply", True)
                
            t = datetime.fromisoformat(t_str)
            if t >= start_of_week and has_reply:
                count += 1
        return count

    def get_monthly_stats(self):
        """Return tickets count for current month."""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        count = 0
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str):
                t_str = ticket
                has_reply = True
            else:
                t_str = ticket["timestamp"]
                has_reply = ticket.get("has_reply", True)
                
            t = datetime.fromisoformat(t_str)
            if t >= start_of_month and has_reply:
                count += 1
        return count

    def get_first_ticket_time_today(self):
        """Return the datetime of the first ticket logged today, or None."""
        today = datetime.now().date()
        first_time = None
        
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str):
                t_str = ticket
            else:
                t_str = ticket["timestamp"]
            
            try:
                t = datetime.fromisoformat(t_str)
                if t.date() == today:
                    if first_time is None or t < first_time:
                        first_time = t
            except ValueError:
                continue
        return first_time

    def get_daily_volume_list(self, days=7):
        """Return list of (date_str, count) tuples for the last N days."""
        daily_counts = self.get_daily_stats() # Returns {date: count}
        today = datetime.now().date()
        result = []
        
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            count = daily_counts.get(date_str, 0)
            result.append((date_str, count))
            
        return result

    def get_stats_range(self, start_date: datetime, end_date: datetime, period="day", metric="cph"):
        """
        Get stats for a specific date range.
        Returns: list of (label, value) tuples
        """
        data_points = []
        
        # 1. Gather raw data (tickets and duration) grouped by period key
        grouped_tickets = defaultdict(int)
        grouped_duration = defaultdict(float) # seconds
        grouped_keys = defaultdict(int) 
        grouped_clicks = defaultdict(int)
        period_keys = [] 
        key_labels = {}
        
        # Helper to generate keys
        def get_key(date_obj, p):
            if p == "day":
                return date_obj.strftime("%Y-%m-%d")
            elif p == "week":
                year, week, _ = date_obj.isocalendar()
                return f"{year}-W{week:02d}"
        
        # Generate target keys (x-axis)
        curr = start_date
        while curr <= end_date:
            k = get_key(curr, period)
            if k not in period_keys:
                period_keys.append(k)
                if period == "day":
                    key_labels[k] = curr.strftime("%a %d")
                else:
                    y, w, _ = curr.isocalendar()
                    key_labels[k] = f"Wk {w}"
            curr += timedelta(days=1)
                
        # Fill Aggregates
        # 1. Tickets
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str): t_str = ticket; has_reply = True
            else: t_str = ticket["timestamp"]; has_reply = ticket.get("has_reply", True)
            
            if not has_reply: continue
            
            try:
                t_date = datetime.fromisoformat(t_str)
                # Filter strictly by date range
                if start_date <= t_date <= end_date + timedelta(days=1): # inclusive enough
                    k = get_key(t_date, period)
                    if k in period_keys: # Only count if in list (safety)
                        grouped_tickets[k] += 1
            except: continue
            
        # 2. Duration (from activity)
        # activity keys are always YYYY-MM-DD
        for date_str, act_data in self.data["activity"].items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if start_date.date() <= date_obj.date() <= end_date.date():
                    target_k = get_key(date_obj, period)
                    grouped_duration[target_k] += act_data.get("duration", 0)
                    grouped_keys[target_k] += act_data.get("keys", 0)
                    grouped_clicks[target_k] += act_data.get("clicks", 0)
            except: continue
            
        # Calc Metric
        for k in period_keys:
            t_count = grouped_tickets[k]
            dur_sec = grouped_duration[k]
            total_keys = grouped_keys[k]
            total_clicks = grouped_clicks[k]
            val = 0.0
            
            if metric == "volume":
                val = t_count
            elif metric == "cph":
                hours = dur_sec / 3600
                if hours > 0.1: val = round(t_count / hours, 1)
                else: val = 0.0
            elif metric == "aht":
                # Average Handle Time (Minutes)
                if t_count > 0: val = round((dur_sec / 60) / t_count, 1)
                else: val = 0.0
            elif metric == "kpm": 
                 minutes = dur_sec / 60
                 if minutes > 1: val = round(total_keys / minutes, 1)
            elif metric == "cpm":
                 minutes = dur_sec / 60
                 if minutes > 1: val = round(total_clicks / minutes, 1)
                
            data_points.append((key_labels[k], val))
            
        return data_points

    def get_aggregated_stats(self, period="day", metric="cph", count=14):
        """
        Get stats aggregated by day or week.
        period: 'day' or 'week'
        metric: 'cph', 'aht', 'volume'
        Returns: list of (label, value) tuples
        """
        now = datetime.now()
        data_points = []
        
        # 1. Gather raw data (tickets and duration) grouped by period key
        grouped_tickets = defaultdict(int)
        grouped_duration = defaultdict(float) # seconds
        period_keys = [] # To maintain order
        key_labels = {}
        
        # Helper to generate keys
        def get_key(date_obj, p):
            if p == "day":
                return date_obj.strftime("%Y-%m-%d")
            elif p == "week":
                year, week, _ = date_obj.isocalendar()
                return f"{year}-W{week:02d}"
        
        # Generate target keys (x-axis)
        if period == "day":
            for i in range(count - 1, -1, -1):
                d = now - timedelta(days=i)
                k = get_key(d, "day")
                period_keys.append(k)
                key_labels[k] = d.strftime("%a %d") # Mon 23
        elif period == "week":
            # For weeks, start from current week and go back
            current_iso = now.isocalendar() # (year, week, day)
            # Need strict math for weeks. 
            # Simple approach: Iterate back by 7 days 'count' times
            curr = now
            for i in range(count):
                k = get_key(curr, "week")
                period_keys.insert(0, k) # Prepend
                # Label: "Wk 46"
                y, w, _ = curr.isocalendar()
                key_labels[k] = f"Wk {w}"
                curr -= timedelta(days=7)
                
        # Fill Aggregates
        # 1. Tickets
        for ticket in self.data["tickets"]:
            if isinstance(ticket, str): t_str = ticket; has_reply = True
            else: t_str = ticket["timestamp"]; has_reply = ticket.get("has_reply", True)
            
            if not has_reply: continue
            
            try:
                t_date = datetime.fromisoformat(t_str)
                k = get_key(t_date, period)
                if k in period_keys: # Only count if in range
                    grouped_tickets[k] += 1
                # If we asked for 7 days but have data for older keys not in list, ignore
            except: continue
            
        # 2. Duration (from activity)
        # activity keys are always YYYY-MM-DD
        for date_str, act_data in self.data["activity"].items():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                target_k = get_key(date_obj, period)
                # If this day belongs to one of our target weeks/days
                if target_k in period_keys: # simplistic check
                    grouped_duration[target_k] += act_data.get("duration", 0)
            except: continue
            
        # Calc Metric
        for k in period_keys:
            t_count = grouped_tickets[k]
            dur_sec = grouped_duration[k]
            val = 0.0
            
            if metric == "volume":
                val = t_count
            elif metric == "cph":
                hours = dur_sec / 3600
                if hours > 0.1: val = round(t_count / hours, 1)
                else: val = 0.0
            elif metric == "aht":
                # Average Handle Time (Minutes)
                if t_count > 0: val = round((dur_sec / 60) / t_count, 1)
                else: val = 0.0
                
            data_points.append((key_labels[k], val))
            
        return data_points
