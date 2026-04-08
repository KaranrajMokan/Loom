"""
Loom Tracker — Desktop application for tracking loom machine operations.
Built with Tkinter + SQLite. Runs fully offline.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import calendar as cal_mod
import csv

from fpdf import XPos, YPos
import db
import sys
import os


# ── Modern colour palette & constants ──
BG = "#f0f4f8"
SIDEBAR_BG = "#0f172a"
SIDEBAR_FG = "#94a3b8"
SIDEBAR_ACTIVE = "#1e3a5f"
SIDEBAR_ACCENT = "#3b82f6"
CARD_BG = "#ffffff"
PRIMARY = "#3b82f6"
PRIMARY_HOVER = "#2563eb"
SUCCESS = "#10b981"
WARNING_CLR = "#f59e0b"
DANGER = "#ef4444"
TEXT_DARK = "#1e293b"
TEXT_LIGHT = "#64748b"
TEXT_MUTED = "#94a3b8"
ENTRY_BG = "#f8fafc"
ENTRY_FG = "#1e293b"
ENTRY_BORDER = "#cbd5e1"
ENTRY_FOCUS = "#3b82f6"
DIVIDER = "#e2e8f0"
FONT = "Helvetica Neue" if __import__("sys").platform == "darwin" else "Segoe UI"
FONT_MONO = "SF Mono" if __import__("sys").platform == "darwin" else "Consolas"
IS_MAC = __import__("sys").platform == "darwin"


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MultiSelectDropdown(tk.Menubutton):
    def __init__(self, parent, choices, **kwargs):
        super().__init__(parent, indicatoron=True, borderwidth=1, relief="solid", 
                         bg=ENTRY_BG, fg=ENTRY_FG, activebackground=CARD_BG, **kwargs)
        self.menu = tk.Menu(self, tearoff=False, bg=CARD_BG, fg=TEXT_DARK)
        self.configure(menu=self.menu)
        
        self.choices = choices
        self.vars = {}
        
        # "Select All" toggle
        self.all_var = tk.BooleanVar(value=True)
        self.menu.add_checkbutton(label="✓ Select All", variable=self.all_var, command=self._toggle_all)
        self.menu.add_separator()
        
        # Add individual choices
        for choice in choices:
            var = tk.BooleanVar(value=True)
            self.vars[choice] = var
            self.menu.add_checkbutton(label=choice, variable=var, command=self._check_state)
            
        self._update_text()

    def _toggle_all(self):
        state = self.all_var.get()
        for var in self.vars.values():
            var.set(state)
        self._update_text()
        
    def _check_state(self):
        all_checked = all(var.get() for var in self.vars.values())
        self.all_var.set(all_checked)
        self._update_text()
        
    def _update_text(self):
        selected = self.get_selected()
        if len(selected) == len(self.choices):
            self.configure(text="All Selected")
        elif len(selected) == 0:
            self.configure(text="None Selected")
        elif len(selected) == 1:
            self.configure(text=selected[0])
        else:
            self.configure(text=f"{len(selected)} Selected")

    def get_selected(self):
        return [choice for choice, var in self.vars.items() if var.get()]

    def select_all(self):
        """Programmatically check all boxes and update the text."""
        self.all_var.set(True)
        for var in self.vars.values():
            var.set(True)
        self._update_text()


class LoomTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧵 Loom Tracker")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)

        db.init_db()
        db.insert_sample_data()   # populate with demo data on first run

        # ── ttk Styling ──
        self._setup_styles()

        # ── Sidebar ──
        self.sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand header
        brand = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        brand.pack(fill="x", pady=(28, 8))
        tk.Label(brand, text="🧵", font=(FONT, 22), bg=SIDEBAR_BG, fg="#ffffff").pack(side="left", padx=(24, 8))
        brand_text = tk.Frame(brand, bg=SIDEBAR_BG)
        brand_text.pack(side="left")
        tk.Label(brand_text, text="Loom Tracker", font=(FONT, 15, "bold"),
                 bg=SIDEBAR_BG, fg="#ffffff").pack(anchor="w")
        tk.Label(brand_text, text="Production Manager", font=(FONT, 8),
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w")

        tk.Frame(self.sidebar, bg="#1e293b", height=1).pack(fill="x", padx=20, pady=(16, 12))

        # Navigation section label
        tk.Label(self.sidebar, text="  MENU", font=(FONT, 9, "bold"), bg=SIDEBAR_BG,
                 fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=20, pady=(4, 6))

        self.nav_buttons = {}
        self._nav_indicators = {}
        nav_items = [
            ("📊  Dashboard", self.show_dashboard),
            ("📝  Daily Entry", self.show_daily_entry),
            ("🌴  Leaves", self.show_leaves),
            ("✂️  Cutting", self.show_cutting),
            ("📓  Loom Ledger", self.show_loom_ledger),
            ("🏭  Looms", self.show_looms),
            ("👷  Operators", self.show_operators),
            ("🎨  Dhothi Styles", self.show_styles),
            ("📋  Reports", self.show_reports),
        ]
        for label, cmd in nav_items:
            row = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
            row.pack(fill="x", padx=12, pady=2)
            indicator = tk.Frame(row, bg=SIDEBAR_BG, width=3)
            indicator.pack(side="left", fill="y", padx=(0, 0))
            btn = tk.Label(row, text=label, font=(FONT, 13),
                           bg=SIDEBAR_BG, fg=SIDEBAR_FG, anchor="w",
                           padx=16, pady=10, cursor="hand2")
            btn.pack(fill="x", expand=True)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn, r=row: (
                b.config(bg=SIDEBAR_ACTIVE, fg="#ffffff"),
                r.config(bg=SIDEBAR_ACTIVE)) if b != self._active_nav else None)
            btn.bind("<Leave>", lambda e, b=btn, r=row: (
                b.config(bg=SIDEBAR_BG, fg=SIDEBAR_FG),
                r.config(bg=SIDEBAR_BG)) if b != self._active_nav else None)
            self.nav_buttons[label] = btn
            self._nav_indicators[label] = (indicator, row)
        self._active_nav = None

        # Footer
        footer = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        footer.pack(side="bottom", fill="x", pady=16, padx=20)
        tk.Frame(footer, bg="#1e293b", height=1).pack(fill="x", pady=(0, 10))
        tk.Label(footer, text="💾 loom_tracker.db", font=(FONT, 9),
                 bg=SIDEBAR_BG, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(footer, text="v2.0 — Offline Mode", font=(FONT, 8),
                 bg=SIDEBAR_BG, fg="#475569").pack(anchor="w", pady=(2, 0))

        # ── Content area ──
        self.content = tk.Frame(root, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self.show_dashboard()

    def _setup_styles(self):
        """Configure ttk styles for a modern look."""
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview
        style.configure("Treeview",
                         background=CARD_BG, foreground=TEXT_DARK, rowheight=32,
                         fieldbackground=CARD_BG, font=(FONT, 12),
                         borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                         background="#f1f5f9", foreground=TEXT_DARK,
                         font=(FONT, 12, "bold"), relief="flat", borderwidth=0)
        style.map("Treeview.Heading", background=[("active", "#e2e8f0")])
        style.map("Treeview", background=[("selected", "#dbeafe")],
                   foreground=[("selected", TEXT_DARK)])

        # Combobox
        style.configure("TCombobox", fieldbackground=ENTRY_BG, background=CARD_BG,
                         foreground=ENTRY_FG, arrowsize=14, borderwidth=1,
                         relief="solid", padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)],
                   selectbackground=[("readonly", ENTRY_BG)],
                   selectforeground=[("readonly", ENTRY_FG)])

        # Scrollbar
        style.configure("TScrollbar", background="#e2e8f0", troughcolor="#f8fafc",
                         borderwidth=0, arrowsize=14)
        style.map("TScrollbar", background=[("active", "#cbd5e1")])

        # Radiobutton
        style.configure("TRadiobutton", background=CARD_BG, foreground=TEXT_DARK,
                         font=(FONT, 13), focuscolor="")

    # ── Helpers ──
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _set_active_nav(self, label):
        for lbl, btn in self.nav_buttons.items():
            indicator, row = self._nav_indicators[lbl]
            if lbl == label:
                btn.config(bg=SIDEBAR_ACTIVE, fg="#ffffff")
                row.config(bg=SIDEBAR_ACTIVE)
                indicator.config(bg=SIDEBAR_ACCENT)
            else:
                btn.config(bg=SIDEBAR_BG, fg=SIDEBAR_FG)
                row.config(bg=SIDEBAR_BG)
                indicator.config(bg=SIDEBAR_BG)
        self._active_nav = self.nav_buttons.get(label)

    def _make_header(self, title):
        hdr = tk.Frame(self.content, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(24, 12))
        tk.Label(hdr, text=title, font=(FONT, 22, "bold"), bg=BG, fg=TEXT_DARK).pack(side="left")
        date_frame = tk.Frame(hdr, bg="#e2e8f0", padx=12, pady=5)
        date_frame.pack(side="right")
        tk.Label(date_frame, text=f" {date.today().strftime('%A, %d %B %Y')}",
                 font=(FONT, 12), bg="#e2e8f0", fg=TEXT_LIGHT).pack()
        return hdr

    def _make_card(self, parent, **pack_kw):
        # Outer wrapper for subtle shadow effect
        wrapper = tk.Frame(parent, bg=DIVIDER, bd=0)
        wrapper.pack(fill="x", padx=30, pady=8, **pack_kw)
        card = tk.Frame(wrapper, bg=CARD_BG, bd=0, padx=1, pady=1)
        card.pack(fill="both", expand=True, padx=1, pady=1)
        return card

    def _make_button(self, parent, text, command, color=PRIMARY, width=14):
        if IS_MAC:
            btn = tk.Button(parent, text=text, font=(FONT, 12, "bold"),
                            highlightbackground=color, fg=TEXT_DARK,
                            padx=16, pady=8, cursor="hand2",
                            command=command, width=width)
        else:
            btn = tk.Button(parent, text=text, font=(FONT, 12, "bold"), bg=color,
                            fg="#ffffff", bd=0, padx=16, pady=8, cursor="hand2",
                            activebackground=color, command=command, width=width)
        return btn

    def _make_label_entry(self, parent, label_text, row, default="", width=30, numeric_only=False):
        tk.Label(parent, text=label_text, font=(FONT, 12, "bold"), bg=CARD_BG,
                 fg=TEXT_LIGHT).grid(row=row, column=0, sticky="w", padx=12, pady=7)
        entry = tk.Entry(parent, font=(FONT, 12), width=width, bd=0, relief="flat",
                         bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                         highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                         highlightbackground=ENTRY_BORDER)
        if numeric_only:
            vcmd = (parent.register(self._validate_numeric), "%P")
            entry.config(validate="key", validatecommand=vcmd)
        entry.grid(row=row, column=1, sticky="w", padx=12, pady=7)
        if default:
            entry.insert(0, default)
        return entry

    @staticmethod
    def _validate_numeric(value):
        """Allow empty, digits, and one decimal point."""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            # Allow intermediate states like "3." while typing
            if value.count(".") == 1 and value.replace(".", "").isdigit():
                return True
            return False

    def _make_combo(self, parent, label_text, row, values, width=27):
        tk.Label(parent, text=label_text, font=(FONT, 12), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=row, column=0, sticky="w", padx=10, pady=6)
        combo = ttk.Combobox(parent, values=values, width=width, state="readonly",
                             font=(FONT, 12))
        combo.grid(row=row, column=1, sticky="w", padx=10, pady=6)
        return combo

    def _make_date_selector(self, parent, initial_date=None, on_change=None):
        """Create a custom, freeze-proof calendar selector."""
        if initial_date is None:
            initial_date = date.today()

        # Container frame
        frame = tk.Frame(parent, bg=CARD_BG)
        frame.current_date = initial_date  # Store the actual date object

        # String variable for the UI
        date_str_var = tk.StringVar(value=initial_date.strftime("%d-%m-%Y"))

        # Read-only entry to display the date beautifully
        entry = tk.Entry(frame, textvariable=date_str_var, width=12, justify="center",
                         font=(FONT, 11), state="readonly", 
                         readonlybackground=ENTRY_BG, fg=TEXT_DARK,
                         highlightthickness=1, highlightbackground=ENTRY_BORDER)
        entry.pack(side="left", padx=(0, 5))

        def open_calendar():
            try:
                from tkcalendar import Calendar
            except ImportError:
                return

            # Create a custom popup window
            popup = tk.Toplevel(frame)
            popup.title("Select Date")
            popup.configure(bg=CARD_BG)

            # Position it right below the entry box
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height() + 2
            popup.geometry(f"+{x}+{y}")

            # Remove window borders for a clean dropdown look
            popup.overrideredirect(True)

            # Safely grab focus
            popup.grab_set()
            popup.focus()

            # Create the main, stable Calendar widget
            cal = Calendar(popup, selectmode='day',
                           year=frame.current_date.year,
                           month=frame.current_date.month,
                           day=frame.current_date.day,
                           background=PRIMARY, foreground='white',
                           headersbackground='#e2e8f0', headersforeground=TEXT_DARK,
                           selectbackground=PRIMARY, selectforeground='white',
                           normalbackground=ENTRY_BG, normalforeground=TEXT_DARK,
                           weekendbackground=ENTRY_BG, weekendforeground=TEXT_DARK,
                           othermonthbackground='#f1f5f9', othermonthforeground='#a0aec0',
                           font=(FONT, 10), borderwidth=1)
            cal.pack(padx=2, pady=2)

            def set_date_and_close(event=None):
                selected = cal.selection_get()
                frame.current_date = selected
                date_str_var.set(selected.strftime("%d-%m-%Y"))

                # Safely release the app freeze
                popup.grab_release()
                popup.destroy()

                if on_change:
                    on_change()

            def close_popup(event=None):
                # Cancel and release if they click the cancel button or press Escape
                popup.grab_release()
                popup.destroy()

            # Bind selection
            cal.bind("<<CalendarSelected>>", set_date_and_close)
            popup.bind("<Escape>", close_popup)

            # Add a small cancel button at the bottom just in case
            btn_frame = tk.Frame(popup, bg=CARD_BG)
            btn_frame.pack(fill="x", pady=(0, 4))
            tk.Button(btn_frame, text="❌ Cancel", command=close_popup, font=(FONT, 9),
                      bg=CARD_BG, fg=DANGER, bd=0, cursor="hand2").pack(side="right", padx=10)

        # Calendar Icon Button
        btn = tk.Button(frame, text="📅", command=open_calendar, cursor="hand2",
                        bd=0, bg=CARD_BG, font=(FONT, 12))
        btn.pack(side="left")

        # --- Maintain API Compatibility ---
        def get_date():
            return frame.current_date

        def set_date(d):
            frame.current_date = d
            date_str_var.set(d.strftime("%d-%m-%Y"))

        frame.get_date = get_date
        frame.set_date = set_date

        return frame

    # ══════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════
    def show_dashboard(self):
        self._clear_content()
        self._set_active_nav("📊  Dashboard")
        self._make_header("Dashboard")

        # Stats row
        stats_frame = tk.Frame(self.content, bg=BG)
        stats_frame.pack(fill="x", padx=30, pady=5)

        looms = db.get_active_looms()
        operators = db.get_active_operators()
        styles = db.get_active_styles()
        today_entries = db.get_tracking_for_date(date.today().isoformat())
        warnings = db.get_looms_over_limit()

        stats = [
            ("Active Looms", len(looms), PRIMARY, "🏭"),
            ("Operators", len(operators), SUCCESS, "👷"),
            ("Styles", len(styles), "#8b5cf6", "🎨"),
            ("Today's Entries", len(today_entries), "#0891b2", "📝"),
        ]
        for i, (label, value, color, icon) in enumerate(stats):
            # Card with colored left accent bar
            outer = tk.Frame(stats_frame, bg=DIVIDER)
            outer.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            inner = tk.Frame(outer, bg=CARD_BG)
            inner.pack(fill="both", expand=True, padx=1, pady=1)
            accent = tk.Frame(inner, bg=color, width=4)
            accent.pack(side="left", fill="y")
            body = tk.Frame(inner, bg=CARD_BG)
            body.pack(side="left", fill="both", expand=True, padx=16, pady=14)
            tk.Label(body, text=f"{icon}  {label}", font=(FONT, 9),
                     bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w")
            tk.Label(body, text=str(value), font=(FONT, 30, "bold"),
                     bg=CARD_BG, fg=color).pack(anchor="w", pady=(4, 0))

        # ── Warning card ──
        if warnings:
            warn_card = self._make_card(self.content)
            warn_hdr = tk.Frame(warn_card, bg="#fef2f2")
            warn_hdr.pack(fill="x")
            tk.Frame(warn_hdr, bg=DANGER, width=4).pack(side="left", fill="y")
            tk.Label(warn_hdr, text="⚠️  Looms Over Limit — Action Required",
                     font=(FONT, 15, "bold"), bg="#fef2f2", fg=DANGER).pack(anchor="w", padx=15, pady=12)
            for loom in warnings:
                limit = loom['cut_limit']
                row_f = tk.Frame(warn_card, bg="#fff7ed")
                row_f.pack(fill="x", padx=15, pady=3)
                tk.Label(row_f, text=f"  🏭 Loom {loom['loom_number']}  —  {loom['current_length']:.1f}m in machine (Limit: {int(limit)}m)",
                         font=(FONT, 13), bg="#fff7ed", fg=DANGER).pack(side="left", padx=5, pady=8)
                self._make_button(row_f, f"✂ Cut at {int(limit)}m", lambda l=loom: self._cut_at_limit(l),
                                  color=SUCCESS, width=12).pack(side="right", padx=5, pady=4)
                self._make_button(row_f, "✂ Custom Cut", lambda l=loom: self._custom_cut(l),
                                  color=PRIMARY, width=12).pack(side="right", padx=2, pady=4)
        else:
            ok_card = self._make_card(self.content)
            ok_inner = tk.Frame(ok_card, bg="#f0fdf4")
            ok_inner.pack(fill="x")
            tk.Frame(ok_inner, bg=SUCCESS, width=4).pack(side="left", fill="y")
            tk.Label(ok_inner, text="✅  All looms are under 80m. No action required.",
                     font=(FONT, 12), bg="#f0fdf4", fg=SUCCESS).pack(padx=15, pady=20)

        # ── Today's entries ──
        entry_card = self._make_card(self.content)
        tk.Label(entry_card, text="📝  Today's Entries", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(14, 5))
        tk.Frame(entry_card, bg=DIVIDER, height=1).pack(fill="x", padx=15)
        if today_entries:
            cols = ("Shift", "Loom", "Operator", "Style", "Produced (m)", "Loom After (m)")
            tree = ttk.Treeview(entry_card, columns=cols, show="headings", height=6)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=100, anchor="center")
            for idx, e in enumerate(today_entries):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", "end", values=(e["shift"], e["loom_number"],
                            e["operator_name"], e["style_name"],
                            f"{e['length_produced']:.1f}", f"{e['loom_length_after']:.1f}"), tags=(tag,))
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(fill="x", padx=15, pady=(8, 14))
        else:
            tk.Label(entry_card, text="No entries yet today. Go to Daily Entry to start.",
                     font=(FONT, 12), bg=CARD_BG, fg=TEXT_LIGHT).pack(padx=15, pady=18)

    def _build_cut_section(self, parent, title, bg_color, items):
        """Build a styled info section with title and key-value rows."""
        section = tk.Frame(parent, bg=bg_color, highlightthickness=1, highlightbackground=DIVIDER)
        section.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(section, text=title, font=(FONT, 12, "bold"), bg=bg_color,
                 fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        tk.Frame(section, bg=DIVIDER, height=1).pack(fill="x", padx=14)
        grid = tk.Frame(section, bg=bg_color)
        grid.pack(fill="x", padx=14, pady=(6, 10))
        grid.columnconfigure(1, weight=1)
        for i, (label, val, color) in enumerate(items):
            tk.Label(grid, text=label, font=(FONT, 12), bg=bg_color,
                     fg=TEXT_DARK, anchor="w").grid(row=i, column=0, padx=(0, 10), pady=3, sticky="w")
            tk.Label(grid, text=val, font=(FONT, 13, "bold"), bg=bg_color,
                     fg=color, anchor="e").grid(row=i, column=1, padx=(10, 0), pady=3, sticky="e")
        return section

    def _get_operator_breakdown(self, loom_id, total, cut_length, remaining):
        """Calculate last operator's batch breakdown. Returns (last_entry, old_batch, new_batch) or None."""
        last = db.get_last_entry_for_loom(loom_id)
        if not last:
            return None
        produced = last["length_produced"]
        loom_before = last["loom_length_before"]
        # Old batch = how much of operator's production went into the cut dhothi
        old_batch = round(cut_length - loom_before, 1)
        if old_batch < 0:
            old_batch = 0.0
        if old_batch > produced:
            old_batch = produced
        # New batch = what stays in the loom from this operator's run
        new_batch = round(produced - old_batch, 1)
        return last, old_batch, new_batch

    def _cut_at_limit(self, loom):
        """Cut at dynamic limit (60m or 80m)."""
        total = loom["current_length"]
        cut_length = loom["cut_limit"] if loom["cut_limit"] else 80.0  # Default to 80 if missing
        remaining = round(total - cut_length, 1)
        if remaining < 0:
            remaining = 0.0
            cut_length = total
        last = db.get_last_entry_for_loom(loom["id"])

        win = tk.Toplevel(self.root)
        win.title(f"Cut at {int(cut_length)}m")
        win.geometry("500x580")
        win.configure(bg=BG)
        win.grab_set()

        header = tk.Frame(win, bg=PRIMARY, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"✂  Cut at {int(cut_length)}m — Loom {loom['loom_number']}",
                 font=(FONT, 14, "bold"), bg=PRIMARY, fg="#ffffff").pack(side="left", padx=20, pady=12)

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        # Cut Summary Section
        self._build_cut_section(body, "CUT SUMMARY", CARD_BG, [
            ("📏 Total length in machine", f"{total:.1f}m", TEXT_DARK),
            ("✂  Dhothi cut length", f"{cut_length:.1f}m", DANGER),
            ("🧵 Remaining in loom", f"{remaining:.1f}m", SUCCESS),
        ])

        # Operator Breakdown Section
        breakdown = self._get_operator_breakdown(loom["id"], total, cut_length, remaining)
        if breakdown:
            last, old_batch, new_batch = breakdown
            op_name = last["operator_name"]
            produced = last["length_produced"]
            loom_before = last["loom_length_before"]
            self._build_cut_section(body, f"👷 LAST OPERATOR: {op_name.upper()}", "#f0fdf4", [
                ("Total produced", f"{produced:.1f}m", TEXT_DARK),
                ("Loom before entry", f"{loom_before:.1f}m", TEXT_LIGHT),
                ("In old batch (cut)", f"{old_batch:.1f}m", WARNING_CLR),
                ("In new batch (stays)", f"{new_batch:.1f}m", PRIMARY),
            ])

        comment_card = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        comment_card.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(comment_card, text="💬 Comment (optional):", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        comment_entry = tk.Entry(comment_card, font=(FONT, 10), width=40, bd=0, relief="flat", bg=ENTRY_BG, fg=ENTRY_FG)
        comment_entry.pack(anchor="w", padx=14, pady=(0, 10))

        # Confirm button
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))
        def do_cut():
            cmt = comment_entry.get().strip()
            full_comment = f"Cut at {int(cut_length)}m" + (f" — {cmt}" if cmt else "")
            op_id = last["operator_id"] if last else None
            db.reset_loom_length(loom["id"], total, was_skipped=False,
                                 comment=full_comment, remaining_length=remaining, operator_id=op_id)
            win.destroy()
            self.show_dashboard()
        self._make_button(btn_frame, f"✂  Confirm Cut at {int(cut_length)}m", do_cut, color=SUCCESS).pack(fill="x", ipady=6)

    def _custom_cut(self, loom):
        """Custom cut — operator enters how much dhothi is LEFT in the loom."""
        total = loom["current_length"]
        last = db.get_last_entry_for_loom(loom["id"])

        win = tk.Toplevel(self.root)
        win.title("Custom Cut")
        win.geometry("500x700")
        win.configure(bg=BG)
        win.grab_set()

        # Header bar
        header = tk.Frame(win, bg="#7c3aed", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"✂  Custom Cut — Loom {loom['loom_number']}",
                 font=(FONT, 16, "bold"), bg="#7c3aed", fg="#ffffff").pack(side="left", padx=20, pady=12)

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        # Total display
        total_frame = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        total_frame.pack(fill="x", padx=24, pady=(16, 8))
        tf_inner = tk.Frame(total_frame, bg=CARD_BG)
        tf_inner.pack(fill="x", padx=14, pady=10)
        tk.Label(tf_inner, text="📏 Total length in machine:", font=(FONT, 13),
                 bg=CARD_BG, fg=TEXT_DARK).pack(side="left")
        tk.Label(tf_inner, text=f"{total:.1f}m", font=(FONT, 16, "bold"),
                 bg=CARD_BG, fg=DANGER).pack(side="right")

        # Input section
        input_card = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=ENTRY_FOCUS)
        input_card.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(input_card, text="🧵 Enter remaining length in loom after cut (m):",
                 font=(FONT, 13, "bold"), bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=14, pady=(12, 4))
        vcmd = (win.register(self._validate_numeric), "%P")
        remaining_entry = tk.Entry(input_card, font=(FONT, 16), width=12, bd=0, relief="flat",
                                   bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                   validate="key", validatecommand=vcmd,
                                   highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                   highlightbackground=ENTRY_BORDER)
        remaining_entry.pack(anchor="w", padx=14, pady=(0, 12))

        # Dynamic results container — cleared and rebuilt on each keystroke
        results_container = tk.Frame(body, bg=BG)
        results_container.pack(fill="x")

        # Comment field
        comment_card = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        comment_card.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(comment_card, text="💬 Comment (optional):", font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        custom_comment_entry = tk.Entry(comment_card, font=(FONT, 12), width=40, bd=0, relief="flat",
                                        bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                        highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                        highlightbackground=ENTRY_BORDER)
        custom_comment_entry.pack(anchor="w", padx=14, pady=(0, 10))

        # Validation + button area
        validation_label = tk.Label(body, text="", font=(FONT, 12, "bold"), bg=BG, fg=DANGER)
        validation_label.pack(padx=24, anchor="w", pady=(4, 0))

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=(6, 16))
        confirm_btn = self._make_button(btn_frame, "✂  Confirm Custom Cut", lambda: None, color=SUCCESS)
        confirm_btn.pack(fill="x", ipady=6)
        confirm_btn.config(state="disabled")

        def update_calc(*_):
            # Clear old result widgets
            for w in results_container.winfo_children():
                w.destroy()

            raw = remaining_entry.get().strip()
            if not raw:
                validation_label.config(text="⬆  Enter a value to see the calculation", fg=TEXT_LIGHT)
                confirm_btn.config(state="disabled")
                return
            try:
                remaining = float(raw)
            except ValueError:
                validation_label.config(text="❌ Invalid number", fg=DANGER)
                confirm_btn.config(state="disabled")
                return

            cut_length = round(total - remaining, 1)

            # Validation
            errors = []
            if remaining < 0:
                errors.append("❌ Remaining length cannot be negative")
            if remaining >= total:
                errors.append(f"❌ Remaining ({remaining:.1f}m) must be less than total ({total:.1f}m)")
            if errors:
                validation_label.config(text="\n".join(errors), fg=DANGER)
                confirm_btn.config(state="disabled")
                return

            # Cut Summary
            self._build_cut_section(results_container, "CUT SUMMARY", CARD_BG, [
                ("📏 Total in machine", f"{total:.1f}m", TEXT_DARK),
                ("✂  Dhothi cut length", f"{cut_length:.1f}m", DANGER),
                ("🧵 Remaining in loom", f"{remaining:.1f}m", SUCCESS),
            ])

            # Operator Breakdown
            if last:
                produced = last["length_produced"]
                loom_before = last["loom_length_before"]
                op_name = last["operator_name"]
                old_batch = round(cut_length - loom_before, 1)
                if old_batch < 0:
                    old_batch = 0.0
                if old_batch > produced:
                    old_batch = produced
                new_batch = round(produced - old_batch, 1)

                self._build_cut_section(results_container, f"👷 LAST OPERATOR: {op_name.upper()}", "#f0fdf4", [
                    ("Total produced", f"{produced:.1f}m", TEXT_DARK),
                    ("Loom before entry", f"{loom_before:.1f}m", TEXT_LIGHT),
                    ("In old batch (cut)", f"{old_batch:.1f}m", WARNING_CLR),
                    ("In new batch (stays)", f"{new_batch:.1f}m", PRIMARY),
                ])

            validation_label.config(
                text=f"✅  {total:.1f} − {remaining:.1f} = {cut_length:.1f}m cut  •  Values correct",
                fg=SUCCESS)
            confirm_btn.config(state="normal")

        remaining_entry.bind("<KeyRelease>", update_calc)

        def do_custom_cut():
            remaining = float(remaining_entry.get().strip())
            cut_length = round(total - remaining, 1)
            cmt = custom_comment_entry.get().strip()
            full_comment = f"Custom cut: {cut_length:.1f}m removed, {remaining:.1f}m left"
            if cmt:
                full_comment += f" — {cmt}"
            op_id = last["operator_id"] if last else None
            db.reset_loom_length(loom["id"], total, was_skipped=False,
                                 comment=full_comment, remaining_length=remaining, operator_id=op_id)
            win.destroy()
            self.show_dashboard()

        confirm_btn.config(command=do_custom_cut)

    # ══════════════════════════════════════════════════
    # DAILY ENTRY
    # ══════════════════════════════════════════════════
    def _make_scrollable(self, parent):
        """Create a scrollable area. Returns (canvas, scroll_frame). Unbinds mousewheel on destroy."""
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=25)
        scrollbar.pack(side="right", fill="y")
        # Keep scroll_frame width in sync with canvas so fill="x" works on children
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        def _on_mousewheel(e):
            if canvas.winfo_exists():
                if IS_MAC:
                    canvas.yview_scroll(int(-1 * e.delta), "units")
                else:
                    canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        if IS_MAC:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        else:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Unbind when canvas is destroyed to prevent TclError
        canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return canvas, scroll_frame

    def show_daily_entry(self):
        self._clear_content()
        self._set_active_nav("📝  Daily Entry")
        self._make_header("Daily Shift Entry")

        # Scrollable area
        canvas, scroll_frame = self._make_scrollable(self.content)

        looms = db.get_active_looms()
        operators = db.get_active_operators()
        styles = db.get_active_styles()

        if not looms:
            tk.Label(scroll_frame, text="⚠️ No looms found. Add looms first.", font=(FONT, 15),
                     bg=BG, fg=DANGER).pack(pady=30)
            return
        if not operators:
            tk.Label(scroll_frame, text="⚠️ No operators found. Add operators first.", font=(FONT, 15),
                     bg=BG, fg=DANGER).pack(pady=30)
            return
        if not styles:
            tk.Label(scroll_frame, text="⚠️ No styles found. Add dhothi styles first.", font=(FONT, 15),
                     bg=BG, fg=DANGER).pack(pady=30)
            return

        # Shift selector card
        shift_card = tk.Frame(scroll_frame, bg=CARD_BG, bd=0, highlightthickness=1,
                              highlightbackground=DIVIDER)
        shift_card.pack(fill="x", pady=8)
        # Accent top bar
        tk.Frame(shift_card, bg=PRIMARY, height=3).pack(fill="x")
        shift_inner = tk.Frame(shift_card, bg=CARD_BG)
        shift_inner.pack(fill="x", padx=5)
        tk.Label(shift_inner, text="Shift:", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, padx=15, pady=14, sticky="w")
        shift_var = tk.StringVar(value="Night")
        for i, s in enumerate(["Night", "Day"]):
            tk.Radiobutton(shift_inner, text=s, variable=shift_var, value=s,
                           font=(FONT, 13), bg=CARD_BG, fg=TEXT_DARK,
                           activebackground=CARD_BG, activeforeground=TEXT_DARK,
                           selectcolor=CARD_BG).grid(row=0, column=i+1, padx=10, pady=14)

        tk.Label(shift_inner, text="Date:", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=3, padx=(20, 5), pady=14)
        op_names = [o["name"] for o in operators]
        style_codes = [s['style_name'] for s in styles]
        self._entry_rows = []

        # Container for loom cards (rebuilt on shift change)
        looms_container = tk.Frame(scroll_frame, bg=BG)
        looms_container.pack(fill="x")

        def build_loom_cards():
            """Build loom entry cards with prefill from last entry."""
            for w in looms_container.winfo_children():
                w.destroy()
            self._entry_rows = []
            current_shift = shift_var.get()
            today = self._date_entry.get_date().isoformat()

            for loom in looms:
                card = tk.Frame(looms_container, bg=CARD_BG, bd=0, highlightthickness=1,
                                highlightbackground=DIVIDER)
                card.pack(fill="x", pady=6)

                # Check if entry already exists for today
                existing = db.get_existing_entry(today, current_shift, loom["id"])

                # Colored accent bar at top of card
                limit = loom["cut_limit"] if loom["cut_limit"] else 80.0
                is_over = loom["current_length"] >= limit
                accent_color = DANGER if is_over else (WARNING_CLR if existing else PRIMARY)
                tk.Frame(card, bg=accent_color, height=3).pack(fill="x")

                # Loom header with status
                hdr_bg = "#fef2f2" if is_over else ("#fffbeb" if existing else "#f0fdf4")
                hdr = tk.Frame(card, bg=hdr_bg)
                hdr.pack(fill="x")
                loom_title = f"  🏭 Loom {loom['loom_number']}"
                if existing:
                    loom_title += "  ✏️"
                tk.Label(hdr, text=loom_title,
                         font=(FONT, 12, "bold"), bg=hdr_bg, fg=TEXT_DARK).pack(side="left", padx=10, pady=10)
                if existing:
                    tk.Label(hdr, text="Already entered — editing will override",
                             font=(FONT, 9), bg=hdr_bg, fg=WARNING_CLR).pack(side="left", padx=5, pady=10)
                length_color = DANGER if is_over else SUCCESS
                tk.Label(hdr, text=f"📏 In Machine: {loom['current_length']:.1f}m",
                         font=(FONT, 13, "bold"), bg=hdr_bg, fg=length_color).pack(side="right", padx=15, pady=10)
                if is_over:
                    tk.Label(hdr, text=f"⚠️ OVER {int(limit)}m", font=(FONT, 10, "bold"),
                             bg=hdr_bg, fg=DANGER).pack(side="right", padx=5)

                # Entry fields with clear labels
                fields = tk.Frame(card, bg=CARD_BG)
                fields.pack(fill="x", padx=15, pady=10)

                tk.Label(fields, text="👷 Operator:", font=(FONT, 12, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, padx=(0, 5), pady=6, sticky="w")
                op_combo = ttk.Combobox(fields, values=op_names, width=18, state="readonly", font=(FONT, 12))
                op_combo.grid(row=0, column=1, padx=5, pady=6)

                tk.Label(fields, text="🎨 Dhothi Style:", font=(FONT, 12, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=2, padx=(15, 5), pady=6, sticky="w")
                st_combo = ttk.Combobox(fields, values=style_codes, width=22, state="readonly", font=(FONT, 12))
                st_combo.grid(row=0, column=3, padx=5, pady=6)

                tk.Label(fields, text="📏 Length Produced (m):", font=(FONT, 12, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(0, 5), pady=6, sticky="w")
                vcmd = (fields.register(self._validate_numeric), "%P")
                len_entry = tk.Entry(fields, font=(FONT, 12), width=10, bd=0, relief="flat",
                                     bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                     validate="key", validatecommand=vcmd,
                                     highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                     highlightbackground=ENTRY_BORDER)
                len_entry.grid(row=1, column=1, padx=5, pady=6, sticky="w")

                tk.Label(fields, text="💬 Comment (optional):", font=(FONT, 12),
                         bg=CARD_BG, fg=TEXT_LIGHT).grid(row=1, column=2, padx=(15, 5), pady=6, sticky="w")
                comment_entry = tk.Entry(fields, font=(FONT, 12), width=22, bd=0, relief="flat",
                                         bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                         highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                         highlightbackground=ENTRY_BORDER)
                comment_entry.grid(row=1, column=3, padx=5, pady=6)

                # Prefill operator and style only (never prefill length/comment)
                last = db.get_last_entry_for_loom_shift(loom["id"], current_shift)
                if existing:
                    # Use existing entry's operator/style for edit mode
                    if existing["operator_name"] in op_names:
                        op_combo.set(existing["operator_name"])
                    style_key = f"{existing['style_code']} - {existing['style_name']}"
                    if style_key in style_codes:
                        st_combo.set(style_key)
                elif last:
                    # Use last entry's operator/style for new entries
                    if last["operator_name"] in op_names:
                        op_combo.set(last["operator_name"])
                    style_key = f"{last['style_code']} - {last['style_name']}"
                    if style_key in style_codes:
                        st_combo.set(style_key)

                # Per-loom save button
                btn_row = tk.Frame(card, bg=CARD_BG)
                btn_row.pack(fill="x", padx=15, pady=(0, 8))
                row_data = {
                    "loom": loom,
                    "op_combo": op_combo,
                    "st_combo": st_combo,
                    "len_entry": len_entry,
                    "comment_entry": comment_entry,
                }
                self._entry_rows.append(row_data)
                save_label = "💾 Update" if existing else "💾 Save"
                self._make_button(btn_row, save_label,
                                  lambda r=row_data: self._save_single_entry(r, shift_var.get()),
                                  color=SUCCESS, width=10).pack(side="right")

        # Create date selector (after build_loom_cards is defined so on_change can reference it)
        self._date_entry = date_entry = self._make_date_selector(
            shift_inner, on_change=lambda: build_loom_cards())
        date_entry.grid(row=0, column=4, padx=5, pady=14)

        # Rebuild cards when shift changes
        shift_var.trace_add("write", lambda *_: build_loom_cards())
        build_loom_cards()

        # Submit all button
        btn_frame = tk.Frame(scroll_frame, bg=BG)
        btn_frame.pack(fill="x", pady=15)
        self._make_button(btn_frame, "💾  Save All Entries", lambda: self._save_daily_entries(shift_var.get()),
                          color=PRIMARY, width=25).pack()

    def _get_entry_maps(self):
        operators = db.get_active_operators()
        styles = db.get_active_styles()
        op_map = {o["name"]: o["id"] for o in operators}
        st_map = {}
        for s in styles:
            key = s['style_name']
            st_map[key] = {"id": s["id"], "category": s["style_category"] or "D"}
        return op_map, st_map

    def _validate_and_save_row(self, row, shift, op_map, st_map, entry_date=None):
        """Validate and save a single loom entry row. Returns (success, warning_tuple_or_None)."""
        length_str = row["len_entry"].get().strip()
        if not length_str:
            return None, None  # skip empty
        op_name = row["op_combo"].get()
        st_key = row["st_combo"].get()
        if not op_name or not st_key:
            messagebox.showwarning("Missing Data", f"Loom {row['loom']['loom_number']}: Select operator and style.")
            return False, None
        try:
            length_produced = float(length_str)
        except ValueError:
            messagebox.showerror("Invalid", f"Loom {row['loom']['loom_number']}: Length must be a number.")
            return False, None

        loom = row["loom"]
        before = loom["current_length"]
        after = before + length_produced
        comment = row["comment_entry"].get().strip()
        the_date = entry_date or date.today().isoformat()

        # Fetch the specific limit for the style they just selected
        style_info = st_map[st_key]
        style_id = style_info["id"]
        cut_limit = 60.0 if style_info["category"] == "S" else 80.0

        db.add_tracking_entry(the_date, shift, loom["id"], op_map[op_name],
                              style_id, length_produced, before, after, comment)
        warning = None
        if after >= cut_limit:
            warning = (loom["loom_number"], after, cut_limit) # Pass the limit into the warning
        return True, warning

    def _save_single_entry(self, row, shift):
        """Save/update a single loom entry."""
        op_map, st_map = self._get_entry_maps()
        entry_date = self._date_entry.get_date().isoformat()
        result, warning = self._validate_and_save_row(row, shift, op_map, st_map, entry_date)
        if result is None:
            messagebox.showinfo("No Data", f"Loom {row['loom']['loom_number']}: Enter length produced.")
            return
        if result is False:
            return
        if warning:
            messagebox.showwarning("⚠️ Over Cut Limit",
                f"Loom {warning[0]} is at {warning[1]:.1f}m (Limit is {int(warning[2])}m).\nGo to Dashboard to cut")
        self.show_daily_entry()

    def _save_daily_entries(self, shift):
        op_map, st_map = self._get_entry_maps()
        entry_date = self._date_entry.get_date().isoformat()
        saved = 0
        warnings_list = []

        for row in self._entry_rows:
            result, warning = self._validate_and_save_row(row, shift, op_map, st_map, entry_date)
            if result is False:
                return  # validation error — stop
            if result is True:
                saved += 1
                if warning:
                    warnings_list.append(warning)

        if saved == 0:
            messagebox.showinfo("No Data", "No entries to save. Enter length produced for at least one loom.")
            return

        if warnings_list:
            msg = "⚠️ Looms over their cut limit:\n"
            for num, length, limit in warnings_list:
                msg += f"  • Loom {num}: {length:.1f}m (Limit: {int(limit)}m)\n"
            msg += "\nGo to Dashboard to reset."
            messagebox.showwarning("⚠️ Over Cut Limit", msg)
        self.show_daily_entry()


    # ══════════════════════════════════════════════════
    # LEAVES MANAGEMENT (CALENDAR & ENTRY)
    # ══════════════════════════════════════════════════
    def show_leaves(self):
        self._clear_content()
        self._set_active_nav("🌴  Leaves")
        self._make_header("Operator Leave Management")

        try:
            from tkcalendar import Calendar
        except ImportError:
            tk.Label(self.content, text="Error: Missing library.\nPlease install tkcalendar: pip install tkcalendar", 
                     font=(FONT, 12, "bold"), fg=DANGER, bg=BG).pack(pady=50)
            return

        canvas, scroll_frame = self._make_scrollable(self.content)
        operators = db.get_active_operators()
        op_map = {o["name"]: o["id"] for o in operators}
        op_opts = list(op_map.keys())

        # ── TOP SECTION: Add Leave Form ──
        form_frame = tk.Frame(scroll_frame, bg=BG)
        # Using anchor="w" ensures the form hugs the left side and doesn't stretch 100% wide
        form_frame.pack(side="top", anchor="w", padx=15, pady=(10, 0))

        # We manually build the card wrapper here to avoid the default fill="x" behavior
        card_wrapper = tk.Frame(form_frame, bg=DIVIDER, bd=0)
        card_wrapper.pack(anchor="w", padx=15, pady=8)
        card = tk.Frame(card_wrapper, bg=CARD_BG, bd=0)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Label(card, text="➕  Add New Leave Entry", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))

        grid_f = tk.Frame(card, bg=CARD_BG)
        grid_f.pack(anchor="w", padx=15, pady=(0, 10))

        # Row 0: Core Inputs
        tk.Label(grid_f, text="Date *", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, sticky="w", pady=6)
        l_date_sel = self._make_date_selector(grid_f)
        l_date_sel.grid(row=0, column=1, padx=(10, 20), pady=6, sticky="w")

        tk.Label(grid_f, text="☀️ Shift *", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=2, sticky="w", pady=6)
        l_shift_combo = ttk.Combobox(grid_f, values=["Day", "Night"], width=12, state="readonly", font=(FONT, 10))
        l_shift_combo.grid(row=0, column=3, padx=(10, 20), pady=6, sticky="w")
        l_shift_combo.set("Day")

        tk.Label(grid_f, text="👷 Operator *", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=4, sticky="w", pady=6)
        l_op_combo = ttk.Combobox(grid_f, values=op_opts, width=18, state="readonly", font=(FONT, 10))
        l_op_combo.grid(row=0, column=5, padx=10, pady=6, sticky="w")

        # Row 1: Optional Comment & Buttons
        tk.Label(grid_f, text="💬 Comment:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, sticky="w", pady=6)
        e_comment = tk.Entry(grid_f, font=(FONT, 10), width=36, bd=0, relief="flat", bg=ENTRY_BG, fg=ENTRY_FG, 
                             highlightthickness=1, highlightcolor=ENTRY_FOCUS, highlightbackground=ENTRY_BORDER)
        e_comment.grid(row=1, column=1, columnspan=3, padx=(10, 20), pady=6, sticky="w")

        def clear_form():
            l_date_sel.set_date(date.today())
            l_shift_combo.set("Day")
            l_op_combo.set("")
            e_comment.delete(0, "end")

        def add_leave():
            the_date = l_date_sel.get_date().isoformat()
            shift = l_shift_combo.get()
            op_name = l_op_combo.get()

            if not op_name:
                messagebox.showwarning("Missing Info", "Please select an operator.")
                return

            if db.add_operator_leave(the_date, shift, op_map[op_name], e_comment.get().strip()):
                messagebox.showinfo("Success", f"Leave added for {op_name} on {the_date}.")
                clear_form()
                self.show_leaves()
            else:
                messagebox.showerror("Error", f"A leave entry already exists for {op_name}\non {the_date} ({shift} shift).")

        btn_frame = tk.Frame(grid_f, bg=CARD_BG)
        btn_frame.grid(row=1, column=4, columnspan=2, pady=6, sticky="e")
        self._make_button(btn_frame, "➕ Add Leave", add_leave, color=SUCCESS).pack(side="left", padx=5)
        self._make_button(btn_frame, "🗑 Clear", clear_form, color=WARNING_CLR, width=8).pack(side="left")


        # ── BOTTOM SECTION: Split Layout ──
        bottom_frame = tk.Frame(scroll_frame, bg=BG)
        # Using pady=(70, 20) pushes the calendar and summary further down the screen, away from the form
        bottom_frame.pack(side="top", fill="both", expand=True, padx=15, pady=(70, 20))

        # Bottom Left: Calendar
        cal_frame = tk.Frame(bottom_frame, bg=BG)
        cal_frame.pack(side="left", fill="both", expand=True, padx=(15, 10))

        # Bottom Right: Visible Leaves Summary
        list_frame = tk.Frame(bottom_frame, bg=BG)
        list_frame.pack(side="right", fill="both", expand=True, padx=(10, 15))

        # ── BOTTOM LEFT: Calendar Card ──
        cal_card = self._make_card(cal_frame)

        tk.Label(cal_card, text="Leave Calendar", font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=10)

        today = date.today()
        cal = Calendar(cal_card, selectmode='day',
                       year=today.year, month=today.month, day=today.day,
                       background=PRIMARY, foreground='white',
                       headersbackground='#e2e8f0', headersforeground=TEXT_DARK,
                       selectbackground=PRIMARY, selectforeground='white',
                       normalbackground=ENTRY_BG, normalforeground=TEXT_DARK,
                       weekendbackground=ENTRY_BG, weekendforeground=TEXT_DARK,
                       othermonthbackground='#f1f5f9', othermonthforeground='#a0aec0',
                       font=(FONT, 10), borderwidth=0)
        cal.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        def mark_leave_dates(event=None):
            cal.alevent_dates = {} # Clear existing marks
            c_year, c_month = cal.get_displayed_month()
            leave_dates_str = db.get_leave_dates_for_month(c_year, c_month)

            for d_str in leave_dates_str:
                d_obj = date.fromisoformat(d_str)
                cal.calevent_create(d_obj, '🌴 On Leave', 'leave_marker')

            # Tag configuration for the marker
            cal.tag_config('leave_marker', background=DIVIDER, foreground='white')

        cal.bind("<<CalendarMonthChanged>>", mark_leave_dates)
        mark_leave_dates()

        legend_frame = tk.Frame(cal_card, bg=CARD_BG)
        legend_frame.pack(fill="x", padx=15, pady=(0, 15))


        # ── BOTTOM RIGHT: List of People on Leave ──
        summary_card = self._make_card(list_frame)

        sel_hdr_var = tk.StringVar(value=f"Showing Leaves for: {date.today().strftime('%d %B %Y')}")
        tk.Label(summary_card, textvariable=sel_hdr_var, font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(10, 5))

        tk.Frame(summary_card, bg=DIVIDER, height=1).pack(fill="x", padx=15, pady=(0, 10))

        list_container = tk.Frame(summary_card, bg=CARD_BG)
        list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        def update_leave_list(event=None):
            for w in list_container.winfo_children():
                w.destroy()

            try:
                sel_date_obj = cal.selection_get()
                sel_date_str = sel_date_obj.isoformat()
            except Exception:
                return

            sel_hdr_var.set(f"Showing Leaves for: {sel_date_obj.strftime('%d %B %Y')}")

            leaves = db.get_leaves_for_date(sel_date_str)

            if not leaves:
                tk.Label(list_container, text="🎉 No operators scheduled on leave.", 
                         font=(FONT, 11), bg=CARD_BG, fg=SUCCESS).pack(pady=20)
                return

            for idx, l in enumerate(leaves):
                row_bg = CARD_BG if idx % 2 == 0 else "#f8fafc"

                l_card = tk.Frame(list_container, bg=row_bg, highlightthickness=1, highlightbackground=DIVIDER)
                l_card.pack(fill="x", pady=4)

                tk.Frame(l_card, bg=WARNING_CLR, width=4).pack(side="left", fill="y")

                inner_f = tk.Frame(l_card, bg=row_bg)
                inner_f.pack(fill="x", padx=12, pady=10)

                f_details = tk.Frame(inner_f, bg=row_bg)
                f_details.pack(side="left")

                tk.Label(f_details, text=l['operator_name'], font=(FONT, 11, "bold"), 
                         bg=row_bg, fg=TEXT_DARK).pack(anchor="w")

                details_text = f"Shift: {l['shift']}"
                if l['comment']: details_text += f"  |  💬 {l['comment']}"

                tk.Label(f_details, text=details_text, font=(FONT, 9), 
                         bg=row_bg, fg=TEXT_LIGHT).pack(anchor="w", pady=(2,0))

                def delete_l(lid=l['id'], op_n=l['operator_name']):
                    if messagebox.askyesno("Confirm Delete", f"Remove leave entry for {op_n}?"):
                        db.delete_leave_entry(lid)
                        self.show_leaves() 

                self._make_button(inner_f, "❌", delete_l, color=DANGER, width=2).pack(side="right")

        cal.bind("<<CalendarSelected>>", update_leave_list)
        update_leave_list()


    # ══════════════════════════════════════════════════
    # CUTTING PAGE
    # ══════════════════════════════════════════════════
    def show_cutting(self):
        self._clear_content()
        self._set_active_nav("✂️  Cutting")
        self._make_header("✂️ Custom Loom Cutting")

        canvas, scroll_frame = self._make_scrollable(self.content)

        looms = db.get_active_looms()
        if not looms:
            tk.Label(scroll_frame, text="⚠️ No active looms found.", font=(FONT, 13), bg=BG, fg=DANGER).pack(pady=30)
            return

        loom_opts = [l["loom_number"] for l in looms]

        # Top Control Card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="🏭 Select Loom to Cut:", font=(FONT, 11, "bold"), 
                 bg=CARD_BG, fg=TEXT_DARK).pack(side="left", padx=(15, 5), pady=12)

        loom_combo = ttk.Combobox(card, values=loom_opts, width=15, state="readonly", font=(FONT, 11))
        loom_combo.pack(side="left", padx=5, pady=12)

        # Container for the interactive cutting form
        form_container = tk.Frame(scroll_frame, bg=BG)
        form_container.pack(fill="both", expand=True, pady=10)

        # Dynamically build the form when a loom is selected
        def on_loom_selected(event=None):
            # Clear previous form if switching looms
            for w in form_container.winfo_children():
                w.destroy()

            sel_num = loom_combo.get()
            if not sel_num: return

            loom = next((l for l in looms if str(l["loom_number"]) == sel_num), None)
            if not loom: return

            # NOTE: Fetch fresh from DB so we get the most up-to-date total,
            # especially if we just adjusted it in a previous step.
            fresh_loom_data = next((l for l in db.get_active_looms() if l["id"] == loom["id"]), loom)

            # NOTE: We store the total in a dictionary called `state`.
            # This allows nested functions (like the adjustment popup) to modify this exact variable in real-time.
            state = {"total": fresh_loom_data["current_length"]}
            last = db.get_last_entry_for_loom(loom["id"])

            # Total display card
            total_frame = tk.Frame(form_container, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
            total_frame.pack(fill="x", padx=30, pady=(0, 8))
            tf_inner = tk.Frame(total_frame, bg=CARD_BG)
            tf_inner.pack(fill="x", padx=14, pady=10)
            tk.Label(tf_inner, text="📏 Total length in machine:", font=(FONT, 11), bg=CARD_BG, fg=TEXT_DARK).pack(side="left")

            # NOTE: We use tk.StringVar() here. When we change this variable later,
            # Tkinter automatically instantly updates the Label on the screen.
            total_str_var = tk.StringVar(value=f"{state['total']:.1f}m")
            tk.Label(tf_inner, textvariable=total_str_var, font=(FONT, 14, "bold"), bg=CARD_BG, fg=DANGER).pack(side="left", padx=10)

            # --- NEW ADJUSTMENT FEATURE ---
            def open_adjust_popup():
                adj_win = tk.Toplevel(self.root)
                adj_win.title(f"Adjust Loom {loom['loom_number']}")
                adj_win.geometry("350x220")
                adj_win.configure(bg=CARD_BG)
                adj_win.grab_set()

                tk.Label(adj_win, text="✏️ Override Total Length", font=(FONT, 13, "bold"), bg=CARD_BG, fg=TEXT_DARK).pack(pady=(20, 5))
                tk.Label(adj_win, text="Enter the new exact length (m):", font=(FONT, 10), bg=CARD_BG, fg=TEXT_LIGHT).pack()

                vcmd_adj = (adj_win.register(self._validate_numeric), "%P")
                adj_entry = tk.Entry(adj_win, font=(FONT, 16, "bold"), width=10, justify="center", bd=1, relief="solid",
                                     bg=ENTRY_BG, fg=ENTRY_FG, validate="key", validatecommand=vcmd_adj)
                adj_entry.pack(pady=15)
                adj_entry.insert(0, str(state["total"]))

                def save_adj():
                    raw_val = adj_entry.get().strip()
                    if not raw_val: return
                    new_val = float(raw_val)

                    # 1. Update the actual Database
                    db.update_loom_length(loom["id"], new_val)

                    # 2. Update the live `state` dictionary and the UI instantly
                    state["total"] = new_val
                    total_str_var.set(f"{state['total']:.1f}m")

                    adj_win.destroy()
                    messagebox.showinfo("Adjusted", f"Loom {loom['loom_number']} length manually updated to {new_val:.1f}m")

                    # 3. Force the math calculation below to refresh if they already typed a remaining number
                    update_calc()

                self._make_button(adj_win, "💾 Save Adjustment", save_adj, color=WARNING_CLR).pack(ipady=4)

            # Add the button to the right side of the total frame
            self._make_button(tf_inner, "✏️ Adjust Length", open_adjust_popup, color=WARNING_CLR, width=14).pack(side="right")

            # Input section card
            input_card = tk.Frame(form_container, bg=CARD_BG, highlightthickness=1, highlightbackground=ENTRY_FOCUS)
            input_card.pack(fill="x", padx=30, pady=(0, 8))
            tk.Label(input_card, text="🧵 Enter remaining length in loom after cut (m):",
                     font=(FONT, 11, "bold"), bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=14, pady=(12, 4))
            vcmd = (self.root.register(self._validate_numeric), "%P")
            remaining_entry = tk.Entry(input_card, font=(FONT, 14), width=12, bd=0, relief="flat",
                                       bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                       validate="key", validatecommand=vcmd,
                                       highlightthickness=1, highlightcolor=ENTRY_FOCUS, highlightbackground=ENTRY_BORDER)
            remaining_entry.pack(anchor="w", padx=14, pady=(0, 12))

            # Dynamic results container
            results_container = tk.Frame(form_container, bg=BG)
            results_container.pack(fill="x", padx=6)

            # Comment field
            comment_card = tk.Frame(form_container, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
            comment_card.pack(fill="x", padx=30, pady=(0, 8))
            tk.Label(comment_card, text="💬 Comment (optional):", font=(FONT, 10, "bold"),
                     bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
            custom_comment_entry = tk.Entry(comment_card, font=(FONT, 10), width=40, bd=0, relief="flat",
                                            bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                            highlightthickness=1, highlightcolor=ENTRY_FOCUS, highlightbackground=ENTRY_BORDER)
            custom_comment_entry.pack(anchor="w", padx=14, pady=(0, 10))

            # Validation + button area
            validation_label = tk.Label(form_container, text="", font=(FONT, 10, "bold"), bg=BG, fg=DANGER)
            validation_label.pack(padx=30, anchor="w", pady=(4, 0))

            btn_frame = tk.Frame(form_container, bg=BG)
            btn_frame.pack(fill="x", padx=30, pady=(6, 16))
            confirm_btn = self._make_button(btn_frame, "✂  Confirm Cut", lambda: None, color=SUCCESS, width=20)
            confirm_btn.pack(fill="x", ipady=6)
            confirm_btn.config(state="disabled")

            def update_calc(*_):
                for w in results_container.winfo_children(): w.destroy()

                raw = remaining_entry.get().strip()
                if not raw:
                    validation_label.config(text="⬆  Enter a value to see the calculation", fg=TEXT_LIGHT)
                    confirm_btn.config(state="disabled")
                    return
                try:
                    remaining = float(raw)
                except ValueError:
                    validation_label.config(text="❌ Invalid number", fg=DANGER)
                    confirm_btn.config(state="disabled")
                    return

                # NOTE: We use state["total"] here so the math always uses the adjusted live number!
                cut_length = round(state["total"] - remaining, 1)

                errors = []
                if remaining < 0:
                    errors.append("❌ Remaining length cannot be negative")
                if remaining >= state["total"]:
                    errors.append(f"❌ Remaining ({remaining:.1f}m) must be strictly less than total ({state['total']:.1f}m)")
                if errors:
                    validation_label.config(text="\n".join(errors), fg=DANGER)
                    confirm_btn.config(state="disabled")
                    return

                # Build summary blocks dynamically
                self._build_cut_section(results_container, "CUT SUMMARY", CARD_BG, [
                    ("📏 Total in machine", f"{state['total']:.1f}m", TEXT_DARK),
                    ("✂  Dhothi cut length", f"{cut_length:.1f}m", DANGER),
                    ("🧵 Remaining in loom", f"{remaining:.1f}m", SUCCESS),
                ])

                if last:
                    produced = last["length_produced"]
                    loom_before = last["loom_length_before"]
                    op_name = last["operator_name"]
                    old_batch = round(cut_length - loom_before, 1)
                    if old_batch < 0: old_batch = 0.0
                    if old_batch > produced: old_batch = produced
                    new_batch = round(produced - old_batch, 1)

                    self._build_cut_section(results_container, f"👷 LAST OPERATOR: {op_name.upper()}", "#f0fdf4", [
                        ("Total produced", f"{produced:.1f}m", TEXT_DARK),
                        ("Loom before entry", f"{loom_before:.1f}m", TEXT_LIGHT),
                        ("In old batch (cut)", f"{old_batch:.1f}m", WARNING_CLR),
                        ("In new batch (stays)", f"{new_batch:.1f}m", PRIMARY),
                    ])

                validation_label.config(text=f"✅  {state['total']:.1f} − {remaining:.1f} = {cut_length:.1f}m cut  •  Values correct", fg=SUCCESS)
                confirm_btn.config(state="normal")

            remaining_entry.bind("<KeyRelease>", update_calc)

            def do_custom_cut():
                remaining = float(remaining_entry.get().strip())
                # NOTE: Use state["total"] here as well
                cut_length = round(state["total"] - remaining, 1)
                cmt = custom_comment_entry.get().strip()
                full_comment = f"Custom cut: {cut_length:.1f}m removed, {remaining:.1f}m left"
                if cmt: full_comment += f" — {cmt}"

                op_id = last["operator_id"] if last else None

                # NOTE: Save the new cut to DB using the live state total
                db.reset_loom_length(loom["id"], state["total"], was_skipped=False,
                                     comment=full_comment, remaining_length=remaining, operator_id=op_id)

                messagebox.showinfo("Success", f"✂️ Successfully cut {cut_length:.1f}m from Loom {loom['loom_number']}!")
                self.show_cutting() # Reset the page to clear forms and refresh db data

            confirm_btn.config(command=do_custom_cut)

        # Trigger logic on loom selection
        loom_combo.bind("<<ComboboxSelected>>", on_loom_selected)

    # ══════════════════════════════════════════════════
    # LOOM LEDGER (BOOK VIEW)
    # ══════════════════════════════════════════════════
    def show_loom_ledger(self):
        self._clear_content()
        self._set_active_nav("📓  Loom Ledger")
        self._make_header("Loom Ledger (Physical Book View)")

        canvas, scroll_frame = self._make_scrollable(self.content)
        looms = db.get_active_looms()
        loom_opts = [f"{l['loom_number']}" for l in looms]

        # Top Control Card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="🏭 Select Loom to View Ledger:", font=(FONT, 11, "bold"), 
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, padx=(15, 5), pady=12, sticky="w")
        
        loom_combo = ttk.Combobox(card, values=loom_opts, width=15, state="readonly", font=(FONT, 11))
        loom_combo.grid(row=0, column=1, padx=5, pady=12)

        current_style_var = tk.StringVar(value="🎨 Current Style: —")
        tk.Label(card, textvariable=current_style_var, font=(FONT, 11, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=2, padx=(30, 5), pady=12, sticky="w")

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=0, column=3, padx=(20, 15), pady=12, sticky="w")

        def export_loom_ledger_pdf():
            if not hasattr(self, '_ledger_rows') or not self._ledger_rows:
                messagebox.showinfo("No Data", "Select a loom to generate the ledger first.")
                return

            loom_num = loom_combo.get()
            headers = ["Date", "Night Shift", "Day Shift", "Current Stock", "Cut Off", "Comment"]
            widths = [25, 45, 45, 30, 25, 100]  # Total width ~270 for Landscape A4

            title = f"Loom Ledger - Loom {loom_num}"
            filename = f"loom_{loom_num}_ledger"

            self._export_generic_pdf(title, headers, widths, self._ledger_rows, filename)

        self._make_button(btn_frame, "📄 Export PDF", export_loom_ledger_pdf, color="#e11d48", width=12).pack()

        # Container for the table
        results_inner = tk.Frame(scroll_frame, bg=BG)
        results_inner.pack(fill="both", expand=True, padx=30, pady=10)

        def load_ledger(*args):
            for w in results_inner.winfo_children(): w.destroy()
            sel_num = loom_combo.get()
            if not sel_num: return
            
            sel_loom_ids = [next((l["id"] for l in looms if str(l["loom_number"]) == sel_num), None)]

            # Fetch all history for this loom (using wide date range)
            entries = db.get_tracking_filtered("2000-01-01", "2100-01-01", sel_loom_ids, None, None, None)
            cuts = db.get_loom_resets_filtered("2000-01-01", "2100-01-01", sel_loom_ids)

            if entries:
                # get_tracking_filtered sorts DESC by date, so index 0 is the most recent style
                latest = entries[0]
                current_style_var.set(f"🎨 Current Style: {latest['style_name']}")
            else:
                current_style_var.set("🎨 Current Style: No Data")

            timeline = []
            
            # Process Daily Entries
            if entries:
                for e in entries:
                    timeline.append({
                        "type": "entry",
                        "date": e["tracking_date"],
                        "shift": e["shift"],
                        "prod": e["length_produced"],
                        "stock": e["loom_length_after"],
                        "operator": e["operator_name"],
                        "comment": e["comment"]
                    })
                    
            # Process Cuts
            if cuts:
                for c in cuts:
                    if not c["was_skipped"]:
                        cut_val = c["length_at_reset"] - (c["remaining_length"] if c["remaining_length"] else 0.0)
                        timeline.append({
                            "type": "cut",
                            "date": c["reset_date"],
                            "shift": "Cut", 
                            "cut_val": cut_val,
                            "stock": c["remaining_length"] if c["remaining_length"] else 0.0,
                            "operator": c["operator_name"]
                        })

            # Sort chronologically: By Date -> Day Shift -> Night Shift -> Cuts
            shift_order = {"Day": 0, "Night": 1, "Cut": 2}
            timeline.sort(key=lambda x: (x["date"], shift_order.get(x["shift"], 3)))

            # Build Treeview Table
            cols = ("Date", "Night Shift", "Day Shift", "Current Stock (m)", "Cut Off (m)", "Comment")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=20)
            
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=130, anchor="center")

            self._ledger_rows = []
            for idx, row in enumerate(timeline):
                tag = "even" if idx % 2 == 0 else "odd"
                day_val, night_val, cut_val = "", "", ""
                comment = ""

                if row["type"] == "entry":
                    val_str = f"{row['prod']:.1f} ({row['operator']})"
                    comment = row["comment"] if row["comment"] else ""
                    if row["shift"] == "Day":
                        day_val = val_str
                    else:
                        night_val = val_str
                elif row["type"] == "cut":
                    cut_val = f"{row['cut_val']:.1f}"

                row_values = (
                    row["date"],
                    night_val,
                    day_val,
                    f"{row['stock']:.1f}",
                    cut_val,
                    comment
                )
                tree.insert("", "end", values=row_values, tags=(tag,))
                self._ledger_rows.append(list(row_values))

            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(fill="both", expand=True)

        # Trigger data load whenever a loom is selected from dropdown
        loom_combo.bind("<<ComboboxSelected>>", load_ledger)


    # ══════════════════════════════════════════════════
    # MANAGE LOOMS
    # ══════════════════════════════════════════════════
    def show_looms(self):
        self._clear_content()
        self._set_active_nav("🏭  Looms")
        self._make_header("Manage Looms")

        # Add / Edit loom form
        card = self._make_card(self.content)
        form_title = tk.Label(card, text="➕ Add New Loom", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_num = self._make_label_entry(card, "Loom Number *", 1)
        e_loc = self._make_label_entry(card, "Location", 2)
        e_notes = self._make_label_entry(card, "Notes", 3)

        tk.Label(card, text="Status", font=(FONT, 12), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        status_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 12))
        status_combo.grid(row=4, column=1, sticky="w", padx=10, pady=6)
        status_combo.set("Active")

        editing_id = [None]  # mutable ref for tracking edit mode

        def clear_form():
            editing_id[0] = None
            form_title.config(text="➕ Add New Loom")
            e_num.delete(0, "end"); e_loc.delete(0, "end"); e_notes.delete(0, "end")
            status_combo.set("Active")
            add_btn.config(text="➕ Add Loom")

        def add_or_update():
            num = e_num.get().strip()
            if not num:
                messagebox.showwarning("Required", "Loom number is required.")
                return
            try:
                if editing_id[0]:
                    db.update_loom(editing_id[0], num, e_loc.get().strip(),
                                   status_combo.get(), e_notes.get().strip())
                else:
                    db.add_loom(num, e_loc.get().strip(), e_notes.get().strip())
                self.show_looms()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=5, column=1, padx=10, pady=12, sticky="w")
        add_btn = self._make_button(btn_frame, "➕ Add Loom", add_or_update, color=SUCCESS)
        add_btn.pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "🗑 Clear", clear_form, color=WARNING_CLR, width=8).pack(side="left")

        # Looms list
        list_card = self._make_card(self.content)
        tk.Label(list_card, text="All Looms  (click a row to edit)", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))
        cols = ("ID", "Loom #", "Location", "Status", "Current Length (m)", "Notes")
        tree = ttk.Treeview(list_card, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        tree.column("Notes", width=160)
        all_looms = db.get_all_looms()
        for idx, loom in enumerate(all_looms):
            limit = loom["cut_limit"] if loom["cut_limit"] else 80.0
            if loom["current_length"] >= limit:
                tag = "warning"
            else:
                tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", "end", values=(loom["id"], loom["loom_number"], loom["location"],
                        loom["status"], f"{loom['current_length']:.1f}", loom["notes"]), tags=(tag,))
        tree.tag_configure("warning", background="#fef2f2")
        tree.tag_configure("even", background="#ffffff")
        tree.tag_configure("odd", background="#f8fafc")
        tree.pack(fill="x", padx=15, pady=(0, 12))

        def on_row_click(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            editing_id[0] = int(vals[0])
            form_title.config(text=f"✏️ Edit Loom {vals[1]}")
            e_num.delete(0, "end"); e_num.insert(0, vals[1])
            e_loc.delete(0, "end"); e_loc.insert(0, vals[2])
            e_notes.delete(0, "end"); e_notes.insert(0, vals[5])
            status_combo.set(vals[3])
            add_btn.config(text="💾 Update Loom")

        tree.bind("<<TreeviewSelect>>", on_row_click)

    # ══════════════════════════════════════════════════
    # MANAGE OPERATORS
    # ══════════════════════════════════════════════════
    def show_operators(self):
        self._clear_content()
        self._set_active_nav("👷  Operators")
        self._make_header("Manage Operators")

        card = self._make_card(self.content)
        form_title = tk.Label(card, text="➕ Add New Operator", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_name = self._make_label_entry(card, "Name *", 1)
        e_spouse = self._make_label_entry(card, "Spouse Name", 2)
        e_phone = self._make_label_entry(card, "Phone", 3)
        e_addr = self._make_label_entry(card, "Address", 4)
        e_joined = self._make_label_entry(card, "Date Joined", 5, default=date.today().isoformat())

        tk.Label(card, text="Status", font=(FONT, 12), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=6, column=0, sticky="w", padx=10, pady=6)
        active_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 12))
        active_combo.grid(row=6, column=1, sticky="w", padx=10, pady=6)
        active_combo.set("Active")

        editing_id = [None]

        def clear_form():
            editing_id[0] = None
            form_title.config(text="➕ Add New Operator")
            for e in (e_name, e_spouse, e_phone, e_addr, e_joined):
                e.delete(0, "end")
            e_joined.insert(0, date.today().isoformat())
            active_combo.set("Active")
            add_btn.config(text="➕ Add Operator")

        def add_or_update():
            name = e_name.get().strip()
            if not name:
                messagebox.showwarning("Required", "Operator name is required.")
                return
            try:
                if editing_id[0]:
                    is_active = 1 if active_combo.get() == "Active" else 0
                    db.update_operator(editing_id[0], name, e_spouse.get().strip(),
                                       e_phone.get().strip(), e_addr.get().strip(),
                                       e_joined.get().strip(), is_active)
                else:
                    db.add_operator(name, e_spouse.get().strip(), e_phone.get().strip(),
                                    e_addr.get().strip(), e_joined.get().strip())
                self.show_operators()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=7, column=1, padx=10, pady=12, sticky="w")
        add_btn = self._make_button(btn_frame, "➕ Add Operator", add_or_update, color=SUCCESS)
        add_btn.pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "🗑 Clear", clear_form, color=WARNING_CLR, width=8).pack(side="left")

        list_card = self._make_card(self.content)
        tk.Label(list_card, text="All Operators  (click a row to edit)", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))
        cols = ("ID", "Name", "Spouse", "Phone", "Address", "Joined", "Status")
        tree = ttk.Treeview(list_card, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")
        tree.column("Name", width=140)
        tree.column("Address", width=150)
        for idx, op in enumerate(db.get_all_operators()):
            active = "Active" if op["is_active"] else "Inactive"
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", "end", values=(op["id"], op["name"], op["spouse_name"],
                        op["phone"], op["address"], op["date_joined"], active), tags=(tag,))
        tree.tag_configure("even", background="#ffffff")
        tree.tag_configure("odd", background="#f8fafc")
        tree.pack(fill="x", padx=15, pady=(0, 12))

        def on_row_click(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            editing_id[0] = int(vals[0])
            form_title.config(text=f"✏️ Edit Operator: {vals[1]}")
            e_name.delete(0, "end"); e_name.insert(0, vals[1])
            e_spouse.delete(0, "end"); e_spouse.insert(0, vals[2])
            e_phone.delete(0, "end"); e_phone.insert(0, vals[3])
            e_addr.delete(0, "end"); e_addr.insert(0, vals[4])
            e_joined.delete(0, "end"); e_joined.insert(0, vals[5])
            active_combo.set(vals[6])
            add_btn.config(text="💾 Update Operator")

        tree.bind("<<TreeviewSelect>>", on_row_click)

    # ══════════════════════════════════════════════════
    # MANAGE STYLES
    # ══════════════════════════════════════════════════
    def show_styles(self):
        self._clear_content()
        self._set_active_nav("🎨  Dhothi Styles")
        self._make_header("Manage Dhothi Styles")

        card = self._make_card(self.content)
        form_title = tk.Label(card, text="➕ Add New Style", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_code = self._make_label_entry(card, "Style Code *", 1)
        e_sname = self._make_label_entry(card, "Style Name *", 2)
        e_price = self._make_label_entry(card, "Price (₹/m)", 3, default="0", numeric_only=True)

        tk.Label(card, text="Category", font=(FONT, 12), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        cat_combo = ttk.Combobox(card, values=["S", "D"], width=27,
                                 state="readonly", font=(FONT, 12))
        cat_combo.grid(row=4, column=1, sticky="w", padx=10, pady=6)
        cat_combo.set("D")

        tk.Label(card, text="Status", font=(FONT, 12), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=5, column=0, sticky="w", padx=10, pady=6)
        active_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 12))
        active_combo.grid(row=5, column=1, sticky="w", padx=10, pady=6)
        active_combo.set("Active")

        editing_id = [None]

        def clear_form():
            editing_id[0] = None
            form_title.config(text="➕ Add New Style")
            e_code.delete(0, "end"); e_sname.delete(0, "end")
            e_price.delete(0, "end"); e_price.insert(0, "0")
            cat_combo.set("D")
            active_combo.set("Active")
            add_btn.config(text="➕ Add Style")

        def add_or_update():
            code = e_code.get().strip()
            sname = e_sname.get().strip()
            category = cat_combo.get()
            if not code or not sname:
                messagebox.showwarning("Required", "Style code and name are required.")
                return
            try:
                price = float(e_price.get().strip() or "0")
                if editing_id[0]:
                    is_active = 1 if active_combo.get() == "Active" else 0
                    db.update_style(editing_id[0], code, sname, price, category, is_active)
                else:
                    db.add_style(code, sname, price, category)
                self.show_styles()
            except ValueError:
                messagebox.showerror("Invalid", "Price must be a number.")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=6, column=1, padx=10, pady=12, sticky="w")
        add_btn = self._make_button(btn_frame, "➕ Add Style", add_or_update, color=SUCCESS)
        add_btn.pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "🗑 Clear", clear_form, color=WARNING_CLR, width=8).pack(side="left")

        list_card = self._make_card(self.content)
        tk.Label(list_card, text="All Dhothi Styles  (click a row to edit)", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))
        cols = ("ID", "Code", "Name", "Category", "Price (₹/m)", "Status")
        tree = ttk.Treeview(list_card, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        for idx, s in enumerate(db.get_all_styles()):
            active = "Active" if s["is_active"] else "Inactive"
            tag = "even" if idx % 2 == 0 else "odd"
            cat = s["style_category"] if s["style_category"] else "D"
            tree.insert("", "end", values=(s["id"], s["style_code"],
                        s["style_name"], cat, f"₹{s['price']:.2f}", active), tags=(tag,))
        tree.tag_configure("even", background="#ffffff")
        tree.tag_configure("odd", background="#f8fafc")
        tree.pack(fill="x", padx=15, pady=(0, 12))

        def on_row_click(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            editing_id[0] = int(vals[0])
            form_title.config(text=f"✏️ Edit Style: {vals[1]}")
            e_code.delete(0, "end"); e_code.insert(0, vals[1])
            e_sname.delete(0, "end"); e_sname.insert(0, vals[2])
            cat_combo.set(vals[3])
            e_price.delete(0, "end")
            # Strip ₹ prefix from price value
            price_str = vals[3].replace("₹", "").strip()
            e_price.insert(0, price_str)
            active_combo.set(vals[4])
            add_btn.config(text="💾 Update Style")

        tree.bind("<<TreeviewSelect>>", on_row_click)


    # ══════════════════════════════════════════════════
    # PDF EXPORT HELPER
    # ══════════════════════════════════════════════════    
    def _export_generic_pdf(self, title, headers, widths, data_rows, filename_prefix):
        """A reusable function to generate PDF tables from any data."""
        if not data_rows:
            messagebox.showinfo("No Data", "No data to export. Please search first.")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{filename_prefix}_{date.today().strftime('%d/%m/%Y')}.pdf")
        
        if not path:
            return
        
        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror("Dependency Missing", "Please install fpdf2 using: pip install fpdf2")
            return

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        
        # Load custom font (using try/except in case the file is missing)
        try:
            pdf.add_font("DejaVu", "B", resource_path("DejaVuSans-Bold.ttf"))
            custom_font = True
        except Exception:
            custom_font = False

        # Report Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"{title} - {date.today().strftime('%d/%m/%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        
        # Table Headers
        if custom_font:
            pdf.set_font("DejaVu", "B", 10)
        else:
            pdf.set_font("Helvetica", "B", 10)

        for i in range(len(headers)):
            pdf.cell(widths[i], 10, headers[i], border=1, align='C')
        pdf.ln()

        # Table Content
        # We keep the font as DejaVu here so the ₹ symbol doesn't crash the PDF
        for row in data_rows:
            for i, item in enumerate(row):
                pdf.cell(widths[i], 10, str(item), border=1)
            pdf.ln()

        try:
            pdf.output(path)
            messagebox.showinfo("Exported", f"PDF report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save PDF:\n{e}")

    # ══════════════════════════════════════════════════
    # REPORTS
    # ══════════════════════════════════════════════════
    def show_reports(self):
        self._clear_content()
        self._set_active_nav("📋  Reports")
        self._make_header("Reports & History")

        # ── Sub-tab navigation bar ──
        tab_bar = tk.Frame(self.content, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        tab_bar.pack(fill="x", padx=30, pady=(0, 4))

        # Container for report views (below the tab bar)
        view_container = tk.Frame(self.content, bg=BG)
        view_container.pack(fill="both", expand=True)

        tab_buttons = {}

        TAB_ACTIVE_BG = PRIMARY
        TAB_ACTIVE_FG = "#ffffff"
        TAB_INACTIVE_BG = "#e2e8f0"
        TAB_INACTIVE_FG = "#475569"

        def select_tab(tab_name):
            for w in view_container.winfo_children():
                w.destroy()
            for name, (frame, lbl) in tab_buttons.items():
                if name == tab_name:
                    frame.config(bg=TAB_ACTIVE_BG)
                    lbl.config(bg=TAB_ACTIVE_BG, fg=TAB_ACTIVE_FG)
                else:
                    frame.config(bg=TAB_INACTIVE_BG)
                    lbl.config(bg=TAB_INACTIVE_BG, fg=TAB_INACTIVE_FG)
            if tab_name == "production":
                self._build_production_report(view_container)
            elif tab_name == "salary":
                self._build_salary_report(view_container)
            elif tab_name == "cuts":
                self._build_cuts_report(view_container)
            elif tab_name == "remaining":
                self._build_remaining_report(view_container)

        tabs = [("📊  Production", "production"), ("💰  Salary", "salary"), ("✂  Loom Cuts", "cuts"), ("🧵  Remaining Loom", "remaining")]
        for label, key in tabs:
            frame = tk.Frame(tab_bar, bg=TAB_INACTIVE_BG, cursor="hand2")
            frame.pack(side="left", padx=(0, 1))
            lbl = tk.Label(frame, text=label, font=(FONT, 13, "bold"),
                           bg=TAB_INACTIVE_BG, fg=TAB_INACTIVE_FG,
                           padx=20, pady=10, cursor="hand2")
            lbl.pack()
            for widget in (frame, lbl):
                widget.bind("<Button-1>", lambda e, k=key: select_tab(k))
            tab_buttons[key] = (frame, lbl)

        # Start with Production tab
        select_tab("production")

    # ── Production Report ──
    def _build_production_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)
        looms = db.get_active_looms()
        operators = db.get_active_operators()
        styles = db.get_active_styles()

        # Filters card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="🔎  Filter Production", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=6, padx=15, pady=(12, 5), sticky="w")

        tk.Label(card, text="From:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        e_from = self._make_date_selector(card)
        e_from.grid(row=1, column=1, padx=5, pady=8)

        tk.Label(card, text="To:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        e_to = self._make_date_selector(card)
        e_to.grid(row=1, column=3, padx=5, pady=8)

        tk.Label(card, text="Shift:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=4, padx=(15, 5), pady=8, sticky="w")
        shift_combo = MultiSelectDropdown(card, choices=["Day", "Night"], width=12, font=(FONT, 12))
        shift_combo.grid(row=1, column=5, padx=5, pady=8)

        loom_opts = [l["loom_number"] for l in looms]
        tk.Label(card, text="🏭 Loom:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=0, padx=(15, 5), pady=8, sticky="w")
        loom_combo = MultiSelectDropdown(card, choices=loom_opts, width=12, font=(FONT, 12))
        loom_combo.grid(row=2, column=1, padx=5, pady=8)

        op_opts = [o["name"] for o in operators]
        tk.Label(card, text="👷 Operator:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=2, padx=(15, 5), pady=8, sticky="w")
        op_combo = MultiSelectDropdown(card, choices=op_opts, width=12, font=(FONT, 12))
        op_combo.grid(row=2, column=3, padx=5, pady=8)

        style_opts = [s["style_name"] for s in styles]
        tk.Label(card, text="🎨 Style:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=4, padx=(15, 5), pady=8, sticky="w")
        style_combo = MultiSelectDropdown(card, choices=style_opts, width=12, font=(FONT, 12))
        style_combo.grid(row=2, column=5, padx=5, pady=8)

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=6, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)
        summary_var = tk.StringVar(value="")
        tk.Label(results_card, textvariable=summary_var, font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack(anchor="w", padx=15, pady=(0, 5))

        def search():
            for w in results_inner.winfo_children():
                w.destroy()
            start_d = e_from.get_date().isoformat()
            end_d = e_to.get_date().isoformat()
            sel_shifts = shift_combo.get_selected()
            sel_looms = loom_combo.get_selected()
            sel_ops = op_combo.get_selected()
            sel_styles = style_combo.get_selected()

            sel_loom_ids = [l["id"] for l in looms if l["loom_number"] in sel_looms]
            sel_op_ids = [o["id"] for o in operators if o["name"] in sel_ops]
            sel_style_ids = [s["id"] for s in styles if s["style_name"] in sel_styles]

            rows = db.get_tracking_filtered(start_d, end_d, sel_loom_ids, sel_op_ids, sel_style_ids, sel_shifts)
            if not rows:
                tk.Label(results_inner, text="No entries found.", font=(FONT, 13), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                summary_var.set("0 entries found")
                self._report_rows = []
                return
            total_produced = sum(r["length_produced"] for r in rows)
            total_wages = sum(r["wages"] for r in rows)
            summary_var.set(f"📊  {len(rows)} entries  |  Total: {total_produced:.1f}m  |  💰 ₹{total_wages:.2f}")

            cols = ("Date", "Day", "Shift", "Loom", "Operator", "Style", "Produced (m)", "Rate (₹/m)", "Wages (₹)", "Comment")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=15)
            scroll = ttk.Scrollbar(results_inner, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=90, anchor="center")
            tree.column("Comment", width=120); tree.column("Operator", width=110)
            for idx, e in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                date_obj = datetime.strptime(e["tracking_date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%y")
                day_of_week = date_obj.strftime("%A")
                tree.insert("", "end", values=(formatted_date, day_of_week, e["shift"], e["loom_number"],
                            e["operator_name"], e["style_code"], f"{e['length_produced']:.1f}",
                            f"₹{e['style_price']:.2f}", f"₹{e['wages']:.2f}", e["comment"]), tags=(tag,))
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            self._report_rows = rows

        self._make_button(btn_frame, "🔍 Search", search, color=PRIMARY, width=10).pack(side="left", padx=(0, 8))

        def export_csv():
            if not hasattr(self, '_report_rows') or not self._report_rows:
                messagebox.showinfo("No Data", "Search first, then export.")
                return
            path = filedialog.asksaveasfilename(defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"loom_report_{date.today().isoformat()}.csv")
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Shift", "Loom", "Operator", "Style",
                                 "Produced (m)", "Rate (₹/m)", "Wages (₹)", "Comment"])
                for e in self._report_rows:
                    writer.writerow([e["tracking_date"], e["shift"], e["loom_number"],
                                     e["operator_name"], e["style_code"],
                                     f"{e['length_produced']:.1f}", f"{e['style_price']:.2f}",
                                     f"{e['wages']:.2f}", e["comment"]])
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")

        def export_pdf():
            if not hasattr(self, '_report_rows') or not self._report_rows:
                messagebox.showinfo("No Data", "Search first, then export.")
                return
            
            headers = ["Date", "Shift", "Loom", "Operator", "Style", "Meters", "Rate (₹)", "Wages (₹)"]
            widths = [30, 20, 20, 45, 35, 25, 25, 30]
            
            # Format the data into a simple list of lists
            data_rows = []
            for e in self._report_rows:
                data_rows.append([
                    e["tracking_date"], e["shift"], e["loom_number"],
                    e["operator_name"], e["style_code"], f"{e['length_produced']:.1f}",
                    f"₹{e['style_price']:.2f}", f"₹{e['wages']:.2f}"
                ])
                
            self._export_generic_pdf("Loom Production Report", headers, widths, data_rows, "production_report")

        self._make_button(btn_frame, "📥 Export CSV", export_csv, color=SUCCESS, width=12).pack(side="left", padx=5)
        self._make_button(btn_frame, "📄 Export PDF", export_pdf, color="#e11d48", width=12).pack(side="left", padx=5)

        def clear_filters():
            e_from.set_date(date.today())
            e_to.set_date(date.today())
            shift_combo.select_all()
            loom_combo.select_all()
            op_combo.select_all()
            style_combo.select_all()
            search()
        self._make_button(btn_frame, "🗑 Clear", clear_filters, color=WARNING_CLR, width=10).pack(side="left", padx=5)
        search()

    # ── Salary Report ──
    def _build_salary_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)

        # Fetch operators for filter
        operators = db.get_active_operators()
        op_opts = [o["name"] for o in operators]

        # Filter card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="💰  Salary Report", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=6, padx=15, pady=(12, 5), sticky="w")

        tk.Label(card, text="From:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        e_from = self._make_date_selector(card)
        e_from.grid(row=1, column=1, padx=5, pady=8)

        tk.Label(card, text="To:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        e_to = self._make_date_selector(card)
        e_to.grid(row=1, column=3, padx=5, pady=8)

        # Multi-select Operator Filter
        tk.Label(card, text="👷 Operator:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=4, padx=(15, 5), pady=8, sticky="w")
        op_combo = MultiSelectDropdown(card, choices=op_opts, width=15, font=(FONT, 12))
        op_combo.grid(row=1, column=5, padx=5, pady=8)

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=2, column=0, columnspan=6, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)

        # PDF Export Function
        def export_salary_pdf():
            if not hasattr(self, '_salary_rows') or not self._salary_rows:
                messagebox.showinfo("No Data", "Generate report first, then export.")
                return

            headers = ["Operator", "Style", "Rate", "Meters", "Wages"]
            widths = [50, 95, 35, 30, 35] # Total ~245mm
            
            # Using generic helper function defined earlier
            self._export_generic_pdf("Operator Salary Report", headers, widths, self._salary_rows, "salary_report")

        def search_salary():
            for w in results_inner.winfo_children():
                w.destroy()

            start_d = e_from.get_date().isoformat()
            end_d = e_to.get_date().isoformat()

            sel_ops = op_combo.get_selected()
            sel_op_ids = [o["id"] for o in operators if o["name"] in sel_ops]

            # Fetch standard tracking rows AND leave counts
            rows = db.get_salary_report(start_d, end_d, sel_op_ids)
            leave_counts = db.get_leave_counts(start_d, end_d)

            if not rows:
                tk.Label(results_inner, text="No salary data found for this period.",
                         font=(FONT, 13), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                self._salary_rows = []
                return

            # Aggregate by operator (summary) and keep detail rows
            ops = {}
            for r in rows:
                name = r["operator_name"]
                leaves_taken = leave_counts.get(name, 0)

                # --- APPLY RATE REDUCTION LOGIC ---
                rate = r["rate"]
                if leaves_taken > 1:
                    rate = rate - 0.50

                # Recalculate wages with potentially reduced rate
                total_wages = r["total_meters"] * rate

                if name not in ops:
                    ops[name] = {
                        "worked_shifts": set(), "total_meters": 0.0, 
                        "total_wages": 0.0, "styles": {}, "leaves": leaves_taken
                    }

                ops[name]["worked_shifts"].add((r["tracking_date"], r["shift"]))
                ops[name]["total_meters"] += r["total_meters"]
                ops[name]["total_wages"] += total_wages

                # Per-style breakdown
                scode = r["style_code"]
                if scode not in ops[name]["styles"]:
                    ops[name]["styles"][scode] = {
                        "name": r["style_name"], "rate": rate,
                        "meters": 0.0, "wages": 0.0
                    }
                ops[name]["styles"][scode]["meters"] += r["total_meters"]
                ops[name]["styles"][scode]["wages"] += total_wages

            grand_meters = sum(d["total_meters"] for d in ops.values())
            grand_wages = sum(d["total_wages"] for d in ops.values())
            grand_shifts = sum(len(d["worked_shifts"]) for d in ops.values())

            # Summary cards row
            summary_frame = tk.Frame(results_inner, bg=CARD_BG)
            summary_frame.pack(fill="x", pady=(0, 12))
            for lbl, val, clr in [
                ("👷 Operators", str(len(ops)), PRIMARY),
                ("📊 Total Shifts", str(grand_shifts), "#7c3aed"),
                ("📏 Total Meters", f"{grand_meters:.1f}m", SUCCESS),
                ("💰 Total Wages", f"₹{grand_wages:.2f}", DANGER),
            ]:
                sf = tk.Frame(summary_frame, bg="#f8fafc", highlightthickness=1, highlightbackground=DIVIDER)
                sf.pack(side="left", expand=True, fill="x", padx=4)
                tk.Label(sf, text=lbl, font=(FONT, 9), bg="#f8fafc", fg=TEXT_LIGHT).pack(anchor="w", padx=12, pady=(8, 0))
                tk.Label(sf, text=val, font=(FONT, 16, "bold"), bg="#f8fafc", fg=clr).pack(anchor="w", padx=12, pady=(0, 8))

            # Salary table with style detail (operator → style rows)
            cols = ("Operator", "Style", "Rate (₹/m)", "Shift Info", "Meters", "Wages (₹)")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=18)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=110, anchor="center")
            tree.column("Operator", width=140, anchor="w")
            tree.column("Style", width=130, anchor="w")
            tree.column("Shift Info", width=140, anchor="w") # Made wider for leave info

            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.tag_configure("op_total", background="#eef2ff", font=(FONT, 12, "bold"))
            tree.tag_configure("penalty", foreground=DANGER) # Red text if penalty applied

            row_idx = 0
            self._salary_rows = [] # Store rows for PDF Exporter

            for name in sorted(ops):
                d = ops[name]
                leaves = d["leaves"]
                penalty_applied = leaves > 1

                day_shifts = sum(1 for date, shift in d["worked_shifts"] if shift == "Day")
                night_shifts = sum(1 for date, shift in d["worked_shifts"] if shift == "Night")
                total_shifts = len(d["worked_shifts"])

                # Style detail rows
                for scode in sorted(d["styles"]):
                    sd = d["styles"][scode]
                    tag = "even" if row_idx % 2 == 0 else "odd"

                    rate_str = f"₹{sd['rate']:.2f}"
                    if penalty_applied: rate_str += " (-0.50)" # Indicate penalty in UI

                    row_vals = (
                        name if scode == sorted(d["styles"])[0] else "",
                        f"{scode} ({sd['name']})",
                        rate_str,
                        f"{sd['meters']:.1f}",
                        f"₹{sd['wages']:.2f}"
                    )

                    tree_tags = (tag, "penalty") if penalty_applied else (tag,)
                    tree.insert("", "end", values=row_vals, tags=tree_tags)
                    self._salary_rows.append(list(row_vals))
                    row_idx += 1

                # Operator total row
                avg_rate = d["total_wages"] / d["total_meters"] if d["total_meters"] > 0 else 0

                # Show leaves taken in the summary line
                shift_info = f"D:{day_shifts} N:{night_shifts} = {total_shifts}"
                if leaves > 0:
                    shift_info += f"  (Leaves: {leaves})"

                tot_vals = (
                    f"  ▸ {name} TOTAL",
                    shift_info,
                    f"Avg ₹{avg_rate:.2f}",
                    f"{d['total_meters']:.1f}",
                    f"₹{d['total_wages']:.2f}"
                )
                tree.insert("", "end", values=tot_vals, tags=("op_total",))
                self._salary_rows.append(list(tot_vals))
                row_idx += 1

            tree.pack(fill="both", expand=True)

        self._make_button(btn_frame, "🔍 Generate", search_salary, color=PRIMARY, width=12).pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "📄 Export PDF", export_salary_pdf, color="#e11d48", width=12).pack(side="left", padx=5)

        search_salary()


    # ── Loom Cuts Report ──
    def _build_cuts_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)
        looms = db.get_active_looms()
        loom_opts = [l["loom_number"] for l in looms]
        styles = db.get_active_styles()
        style_opts = [s["style_code"] for s in styles]

        card = self._make_card(scroll_frame)
        tk.Label(card, text="✂  Loom Cuts History", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        tk.Label(card, text="From:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        cuts_from = self._make_date_selector(card)
        cuts_from.grid(row=1, column=1, padx=5, pady=8)
        tk.Label(card, text="To:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        cuts_to = self._make_date_selector(card)
        cuts_to.grid(row=1, column=3, padx=5, pady=8)
        tk.Label(card, text="🏭 Loom:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=0, padx=(15, 5), pady=8, sticky="w")
        cuts_loom_combo = MultiSelectDropdown(card, choices=loom_opts, width=12, font=(FONT, 12))
        cuts_loom_combo.grid(row=2, column=1, padx=5, pady=8)
        tk.Label(card, text="🎨 Style:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=2, padx=(15, 5), pady=8, sticky="w")
        cuts_style_combo = MultiSelectDropdown(card, choices=style_opts, width=12, font=(FONT, 12))
        cuts_style_combo.grid(row=2, column=3, padx=5, pady=8)
        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=4, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)
        cuts_summary_var = tk.StringVar(value="")
        tk.Label(results_card, textvariable=cuts_summary_var, font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack(anchor="w", padx=15, pady=(0, 5))

        def search_cuts():
            for w in results_inner.winfo_children():
                w.destroy()
            start_d = cuts_from.get_date().isoformat()
            end_d = cuts_to.get_date().isoformat()
            sel_looms = cuts_loom_combo.get_selected()
            sel_styles = cuts_style_combo.get_selected()

            sel_loom_ids = [l["id"] for l in looms if l["loom_number"] in sel_looms]
            sel_style_ids = [s["id"] for s in styles if s["style_code"] in sel_styles]
            rows = db.get_loom_resets_filtered(start_d, end_d, sel_loom_ids, sel_style_ids)
            if not rows:
                tk.Label(results_inner, text="No cuts found.", font=(FONT, 13), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                cuts_summary_var.set("0 cuts found")
                return
            cols = ("Date", "Day", "Shift", "Loom", "Operator", "Style", "Dhothi Cut (m)", "Comment")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=12)
            scroll = ttk.Scrollbar(results_inner, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=95, anchor="center")
            tree.column("Comment", width=180, anchor="w")
            tree.column("Operator", width=110)
            total_cut_length = 0.0
            for idx, r in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                total_len = r["length_at_reset"]
                remaining = r["remaining_length"] if r["remaining_length"] else 0.0
                cut_len = round(total_len - remaining, 1) if not r["was_skipped"] else 0.0
                total_cut_length += cut_len
                date_obj = datetime.strptime(r["reset_date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%y")
                day_of_week = date_obj.strftime("%A")
                tree.insert("", "end", values=(
                    formatted_date, day_of_week, r["shift"], r["loom_number"], r["operator_name"], r["style_name"],
                    f"{cut_len:.1f}" if not r["was_skipped"] else "—", r["comment"]
                ), tags=(tag,))
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            cuts_summary_var.set(f"✂  {len(rows)} cuts found  |  Total: {total_cut_length:.1f}m ")
            self._cuts_rows = rows

        def export_cuts_pdf():
            if not hasattr(self, '_cuts_rows') or not self._cuts_rows:
                messagebox.showinfo("No Data", "Search first, then export.")
                return

            headers = ["Date", "Loom", "Operator", "Style", "Cut (m)", "Comment"]
            widths = [30, 20, 40, 60, 25, 90] # Total width should be <= ~270 for Landscape A4

            data_rows = []
            for r in self._cuts_rows:
                total_len = r["length_at_reset"]
                remaining = r["remaining_length"] if r["remaining_length"] else 0.0
                cut_len = round(total_len - remaining, 1) if not r["was_skipped"] else 0.0

                data_rows.append([
                    r["reset_date"], r["loom_number"], r["operator_name"], r["style_name"],
                    f"{cut_len:.1f}" if not r["was_skipped"] else "—", r["comment"]
                ])

            self._export_generic_pdf("Loom Cuts History", headers, widths, data_rows, "loom_cuts")

        self._make_button(btn_frame, "🔍 Search Cuts", search_cuts, color=PRIMARY, width=12).pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "📄 Export PDF", export_cuts_pdf, color="#e11d48", width=12).pack(side="left", padx=5)
        search_cuts()

    # ── Remaining Loom Report ──
    def _build_remaining_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)

        # Data for filters
        looms = db.get_active_looms()
        loom_opts = [l["loom_number"] for l in looms]
        styles = db.get_active_styles()
        style_opts = [s["style_code"] for s in styles]
        locations = sorted(list(set(l["location"] for l in looms if l["location"].strip())))

        # Filter Card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="🧵  Remaining Fabric in Looms", font=(FONT, 15, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=6, padx=15, pady=(12, 5), sticky="w")

        tk.Label(card, text="🏭 Loom:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        rem_loom_combo = MultiSelectDropdown(card, choices=loom_opts, width=12, font=(FONT, 12))
        rem_loom_combo.grid(row=1, column=1, padx=5, pady=8)

        tk.Label(card, text="🎨 Style:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        rem_style_combo = MultiSelectDropdown(card, choices=style_opts, width=12, font=(FONT, 12))
        rem_style_combo.grid(row=1, column=3, padx=5, pady=8)

        tk.Label(card, text="📍 Location:", font=(FONT, 12, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=4, padx=(15, 5), pady=8, sticky="w")
        rem_loc_combo = MultiSelectDropdown(card, choices=locations, width=12, font=(FONT, 12))
        rem_loc_combo.grid(row=1, column=5, padx=5, pady=8)

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=2, column=0, columnspan=6, padx=15, pady=(5, 12), sticky="w")

        # Results Card
        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)
        rem_summary_var = tk.StringVar(value="")
        tk.Label(results_card, textvariable=rem_summary_var, font=(FONT, 12, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack(anchor="w", padx=15, pady=(0, 5))

        def search_remaining():
            for w in results_inner.winfo_children():
                w.destroy()

            sel_looms = rem_loom_combo.get_selected()
            sel_styles = rem_style_combo.get_selected()
            sel_loom_ids = [l["id"] for l in looms if l["loom_number"] in sel_looms]
            sel_style_ids = [s["id"] for s in styles if s["style_code"] in sel_styles]
            sel_locs = rem_loc_combo.get_selected()

            rows = db.get_remaining_looms_filtered(sel_loom_ids, sel_style_ids, sel_locs)

            if not rows:
                tk.Label(results_inner, text="No active looms matched filters.", font=(FONT, 13), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                rem_summary_var.set("0 looms found")
                return

            cols = ("Loom Number", "Location", "Current Style", "Remaining in Machine (m)")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=15)
            scroll = ttk.Scrollbar(results_inner, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)

            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=150, anchor="center")
            tree.column("Location", width=180, anchor="w")

            total_remaining = 0.0
            for idx, r in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                style_display = f"{r['style_code']} ({r['style_name']})" if r['style_code'] != '—' else '—'
                total_remaining += r["current_length"]

                limit = r["cut_limit"] if r["cut_limit"] else 80.0
                if r["current_length"] >= limit:
                    tag = "warning"

                tree.insert("", "end", values=(
                    r["loom_number"], r["location"], style_display,
                    f"{r['current_length']:.1f}"
                ), tags=(tag,))

            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.tag_configure("warning", background="#fef2f2", foreground=DANGER)

            tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            rem_summary_var.set(f"🧵  {len(rows)} looms found  |  Total Fabric in Production: {total_remaining:.1f}m ")

        self._make_button(btn_frame, "🔍 Search", search_remaining, color=PRIMARY, width=12).pack(side="left", padx=(0, 8))
        search_remaining()


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = LoomTrackerApp(root)
    root.mainloop()
