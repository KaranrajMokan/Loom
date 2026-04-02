"""
Loom Tracker — Desktop application for tracking loom machine operations.
Built with Tkinter + SQLite. Runs fully offline.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import calendar as cal_mod
import csv
import db


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
LOOM_LIMIT = 80.0
IS_MAC = __import__("sys").platform == "darwin"


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
            btn = tk.Label(row, text=label, font=(FONT, 11),
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
                         fieldbackground=CARD_BG, font=(FONT, 10),
                         borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                         background="#f1f5f9", foreground=TEXT_DARK,
                         font=(FONT, 10, "bold"), relief="flat", borderwidth=0)
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
                         font=(FONT, 11), focuscolor="")

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
        tk.Label(date_frame, text=f"📅  {date.today().strftime('%A, %d %B %Y')}",
                 font=(FONT, 10), bg="#e2e8f0", fg=TEXT_LIGHT).pack()
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
            btn = tk.Button(parent, text=text, font=(FONT, 10, "bold"),
                            highlightbackground=color, fg=TEXT_DARK,
                            padx=16, pady=8, cursor="hand2",
                            command=command, width=width)
        else:
            btn = tk.Button(parent, text=text, font=(FONT, 10, "bold"), bg=color,
                            fg="#ffffff", bd=0, padx=16, pady=8, cursor="hand2",
                            activebackground=color, command=command, width=width)
        return btn

    def _make_label_entry(self, parent, label_text, row, default="", width=30, numeric_only=False):
        tk.Label(parent, text=label_text, font=(FONT, 10, "bold"), bg=CARD_BG,
                 fg=TEXT_LIGHT).grid(row=row, column=0, sticky="w", padx=12, pady=7)
        entry = tk.Entry(parent, font=(FONT, 10), width=width, bd=0, relief="flat",
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
        tk.Label(parent, text=label_text, font=(FONT, 10), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=row, column=0, sticky="w", padx=10, pady=6)
        combo = ttk.Combobox(parent, values=values, width=width, state="readonly",
                             font=(FONT, 10))
        combo.grid(row=row, column=1, sticky="w", padx=10, pady=6)
        return combo

    def _make_date_selector(self, parent, initial_date=None, on_change=None):
        """Create a Year/Month/Day combobox date selector. Returns a dict with get_date() and set_date() methods."""
        if initial_date is None:
            initial_date = date.today()
        frame = tk.Frame(parent, bg=CARD_BG)
        today = date.today()
        years = [str(y) for y in range(today.year - 2, today.year + 2)]
        months = [f"{m:02d}" for m in range(1, 13)]

        y_var = tk.StringVar(value=str(initial_date.year))
        m_var = tk.StringVar(value=f"{initial_date.month:02d}")
        d_var = tk.StringVar(value=f"{initial_date.day:02d}")

        y_cb = ttk.Combobox(frame, textvariable=y_var, values=years, width=5, state="readonly", font=(FONT, 10))
        y_cb.pack(side="left", padx=1)
        tk.Label(frame, text="-", bg=CARD_BG, fg=TEXT_DARK, font=(FONT, 10)).pack(side="left")
        m_cb = ttk.Combobox(frame, textvariable=m_var, values=months, width=3, state="readonly", font=(FONT, 10))
        m_cb.pack(side="left", padx=1)
        tk.Label(frame, text="-", bg=CARD_BG, fg=TEXT_DARK, font=(FONT, 10)).pack(side="left")
        d_cb = ttk.Combobox(frame, textvariable=d_var, values=[], width=3, state="readonly", font=(FONT, 10))
        d_cb.pack(side="left", padx=1)

        def _update_days(*_):
            try:
                yr = int(y_var.get())
                mo = int(m_var.get())
            except ValueError:
                return
            max_d = cal_mod.monthrange(yr, mo)[1]
            d_cb["values"] = [f"{d:02d}" for d in range(1, max_d + 1)]
            if int(d_var.get()) > max_d:
                d_var.set(f"{max_d:02d}")
            if on_change:
                on_change()

        # Initialise days list first (without triggering on_change)
        try:
            yr = int(y_var.get())
            mo = int(m_var.get())
        except ValueError:
            yr, mo = today.year, today.month
        max_d = cal_mod.monthrange(yr, mo)[1]
        d_cb["values"] = [f"{d:02d}" for d in range(1, max_d + 1)]

        # Now attach traces (so on_change only fires on user interaction)
        y_var.trace_add("write", _update_days)
        m_var.trace_add("write", _update_days)
        d_var.trace_add("write", lambda *_: on_change() if on_change else None)

        def get_date():
            try:
                return date(int(y_var.get()), int(m_var.get()), int(d_var.get()))
            except (ValueError, TypeError):
                return date.today()

        def set_date(d):
            y_var.set(str(d.year))
            m_var.set(f"{d.month:02d}")
            d_var.set(f"{d.day:02d}")

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
        warnings = db.get_looms_over_limit(LOOM_LIMIT)

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
            tk.Label(warn_hdr, text="⚠️  Looms Over 80m — Action Required",
                     font=(FONT, 13, "bold"), bg="#fef2f2", fg=DANGER).pack(anchor="w", padx=15, pady=12)
            for loom in warnings:
                row_f = tk.Frame(warn_card, bg="#fff7ed")
                row_f.pack(fill="x", padx=15, pady=3)
                tk.Label(row_f, text=f"  🏭 Loom {loom['loom_number']}  —  {loom['current_length']:.1f}m in machine",
                         font=(FONT, 11), bg="#fff7ed", fg=DANGER).pack(side="left", padx=5, pady=8)
                self._make_button(row_f, "✂ Cut at 80m", lambda l=loom: self._cut_at_80(l),
                                  color=SUCCESS, width=12).pack(side="right", padx=5, pady=4)
                self._make_button(row_f, "✂ Custom Cut", lambda l=loom: self._custom_cut(l),
                                  color=PRIMARY, width=12).pack(side="right", padx=2, pady=4)
                self._make_button(row_f, "⏭ Skip", lambda l=loom: self._skip_reset(l),
                                  color=WARNING_CLR, width=8).pack(side="right", padx=2, pady=4)
        else:
            ok_card = self._make_card(self.content)
            ok_inner = tk.Frame(ok_card, bg="#f0fdf4")
            ok_inner.pack(fill="x")
            tk.Frame(ok_inner, bg=SUCCESS, width=4).pack(side="left", fill="y")
            tk.Label(ok_inner, text="✅  All looms are under 80m. No action required.",
                     font=(FONT, 12), bg="#f0fdf4", fg=SUCCESS).pack(padx=15, pady=20)

        # ── Today's entries ──
        entry_card = self._make_card(self.content)
        tk.Label(entry_card, text="📝  Today's Entries", font=(FONT, 13, "bold"),
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
                            e["operator_name"], e["style_code"],
                            f"{e['length_produced']:.1f}", f"{e['loom_length_after']:.1f}"), tags=(tag,))
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(fill="x", padx=15, pady=(8, 14))
        else:
            tk.Label(entry_card, text="No entries yet today. Go to Daily Entry to start.",
                     font=(FONT, 10), bg=CARD_BG, fg=TEXT_LIGHT).pack(padx=15, pady=18)

    def _build_cut_section(self, parent, title, bg_color, items):
        """Build a styled info section with title and key-value rows."""
        section = tk.Frame(parent, bg=bg_color, highlightthickness=1, highlightbackground=DIVIDER)
        section.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(section, text=title, font=(FONT, 10, "bold"), bg=bg_color,
                 fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        tk.Frame(section, bg=DIVIDER, height=1).pack(fill="x", padx=14)
        grid = tk.Frame(section, bg=bg_color)
        grid.pack(fill="x", padx=14, pady=(6, 10))
        grid.columnconfigure(1, weight=1)
        for i, (label, val, color) in enumerate(items):
            tk.Label(grid, text=label, font=(FONT, 10), bg=bg_color,
                     fg=TEXT_DARK, anchor="w").grid(row=i, column=0, padx=(0, 10), pady=3, sticky="w")
            tk.Label(grid, text=val, font=(FONT, 11, "bold"), bg=bg_color,
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

    def _cut_at_80(self, loom):
        """Cut at exactly 80m — remaining = current_length - 80."""
        total = loom["current_length"]
        cut_length = 80.0
        remaining = round(total - cut_length, 1)
        if remaining < 0:
            remaining = 0.0
            cut_length = total
        last = db.get_last_entry_for_loom(loom["id"])

        win = tk.Toplevel(self.root)
        win.title("Cut at 80m")
        win.geometry("500x580")
        win.configure(bg=BG)
        win.grab_set()

        # Header bar
        header = tk.Frame(win, bg=PRIMARY, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"✂  Cut at 80m — Loom {loom['loom_number']}",
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

        # Comment field
        comment_card = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        comment_card.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(comment_card, text="💬 Comment (optional):", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        comment_entry = tk.Entry(comment_card, font=(FONT, 10), width=40, bd=0, relief="flat",
                                 bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                 highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                 highlightbackground=ENTRY_BORDER)
        comment_entry.pack(anchor="w", padx=14, pady=(0, 10))

        # Confirm button
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))
        def do_cut():
            cmt = comment_entry.get().strip()
            full_comment = f"Cut at 80m" + (f" — {cmt}" if cmt else "")
            op_id = last["operator_id"] if last else None
            db.reset_loom_length(loom["id"], total, was_skipped=False,
                                 comment=full_comment, remaining_length=remaining, operator_id=op_id)
            win.destroy()
            self.show_dashboard()
        self._make_button(btn_frame, "✂  Confirm Cut at 80m", do_cut, color=SUCCESS).pack(fill="x", ipady=6)

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
                 font=(FONT, 14, "bold"), bg="#7c3aed", fg="#ffffff").pack(side="left", padx=20, pady=12)

        body = tk.Frame(win, bg=BG)
        body.pack(fill="both", expand=True)

        # Total display
        total_frame = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        total_frame.pack(fill="x", padx=24, pady=(16, 8))
        tf_inner = tk.Frame(total_frame, bg=CARD_BG)
        tf_inner.pack(fill="x", padx=14, pady=10)
        tk.Label(tf_inner, text="📏 Total length in machine:", font=(FONT, 11),
                 bg=CARD_BG, fg=TEXT_DARK).pack(side="left")
        tk.Label(tf_inner, text=f"{total:.1f}m", font=(FONT, 14, "bold"),
                 bg=CARD_BG, fg=DANGER).pack(side="right")

        # Input section
        input_card = tk.Frame(body, bg=CARD_BG, highlightthickness=1, highlightbackground=ENTRY_FOCUS)
        input_card.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(input_card, text="🧵 Enter remaining length in loom after cut (m):",
                 font=(FONT, 11, "bold"), bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=14, pady=(12, 4))
        vcmd = (win.register(self._validate_numeric), "%P")
        remaining_entry = tk.Entry(input_card, font=(FONT, 14), width=12, bd=0, relief="flat",
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
        tk.Label(comment_card, text="💬 Comment (optional):", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(10, 4))
        custom_comment_entry = tk.Entry(comment_card, font=(FONT, 10), width=40, bd=0, relief="flat",
                                        bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                        highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                        highlightbackground=ENTRY_BORDER)
        custom_comment_entry.pack(anchor="w", padx=14, pady=(0, 10))

        # Validation + button area
        validation_label = tk.Label(body, text="", font=(FONT, 10, "bold"), bg=BG, fg=DANGER)
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

    def _skip_reset(self, loom):
        win = tk.Toplevel(self.root)
        win.title("Skip Reset")
        win.geometry("400x200")
        win.configure(bg=CARD_BG)
        win.grab_set()
        tk.Label(win, text=f"Skip reset for Loom {loom['loom_number']}?",
                 font=(FONT, 13, "bold"), bg=CARD_BG, fg=TEXT_DARK).pack(pady=(20, 5))
        tk.Label(win, text=f"Current length: {loom['current_length']:.1f}m",
                 font=(FONT, 11), bg=CARD_BG, fg=DANGER).pack()
        tk.Label(win, text="Comment (optional):", font=(FONT, 10),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=20, pady=(10, 2))
        comment_entry = tk.Entry(win, font=(FONT, 10), width=40, bd=0, relief="flat",
                                 bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                 highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                 highlightbackground=ENTRY_BORDER)
        comment_entry.pack(padx=20)

        def do_skip():
            last = db.get_last_entry_for_loom(loom["id"])
            op_id = last["operator_id"] if last else None
            db.reset_loom_length(loom["id"], loom["current_length"],
                                was_skipped=True, comment=comment_entry.get(), operator_id=op_id)
            win.destroy()
            self.show_dashboard()
        self._make_button(win, "Confirm Skip", do_skip, color=WARNING_CLR).pack(pady=15)

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
            tk.Label(scroll_frame, text="⚠️ No looms found. Add looms first.", font=(FONT, 13),
                     bg=BG, fg=DANGER).pack(pady=30)
            return
        if not operators:
            tk.Label(scroll_frame, text="⚠️ No operators found. Add operators first.", font=(FONT, 13),
                     bg=BG, fg=DANGER).pack(pady=30)
            return
        if not styles:
            tk.Label(scroll_frame, text="⚠️ No styles found. Add dhothi styles first.", font=(FONT, 13),
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
        tk.Label(shift_inner, text="☀️  Shift:", font=(FONT, 11, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, padx=15, pady=14, sticky="w")
        shift_var = tk.StringVar(value="Day")
        for i, s in enumerate(["Day", "Night"]):
            tk.Radiobutton(shift_inner, text=s, variable=shift_var, value=s,
                           font=(FONT, 11), bg=CARD_BG, fg=TEXT_DARK,
                           activebackground=CARD_BG, activeforeground=TEXT_DARK,
                           selectcolor=CARD_BG).grid(row=0, column=i+1, padx=10, pady=14)

        tk.Label(shift_inner, text="📅 Date:", font=(FONT, 11, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=3, padx=(20, 5), pady=14)
        op_names = [o["name"] for o in operators]
        style_codes = [f"{s['style_code']} - {s['style_name']}" for s in styles]
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
                is_over = loom["current_length"] >= LOOM_LIMIT
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
                         font=(FONT, 11, "bold"), bg=hdr_bg, fg=length_color).pack(side="right", padx=15, pady=10)
                if is_over:
                    tk.Label(hdr, text="⚠️ OVER 80m", font=(FONT, 10, "bold"),
                             bg=hdr_bg, fg=DANGER).pack(side="right", padx=5)

                # Entry fields with clear labels
                fields = tk.Frame(card, bg=CARD_BG)
                fields.pack(fill="x", padx=15, pady=10)

                tk.Label(fields, text="👷 Operator:", font=(FONT, 10, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, padx=(0, 5), pady=6, sticky="w")
                op_combo = ttk.Combobox(fields, values=op_names, width=18, state="readonly", font=(FONT, 10))
                op_combo.grid(row=0, column=1, padx=5, pady=6)

                tk.Label(fields, text="🎨 Dhothi Style:", font=(FONT, 10, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=2, padx=(15, 5), pady=6, sticky="w")
                st_combo = ttk.Combobox(fields, values=style_codes, width=22, state="readonly", font=(FONT, 10))
                st_combo.grid(row=0, column=3, padx=5, pady=6)

                tk.Label(fields, text="📏 Length Produced (m):", font=(FONT, 10, "bold"),
                         bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(0, 5), pady=6, sticky="w")
                vcmd = (fields.register(self._validate_numeric), "%P")
                len_entry = tk.Entry(fields, font=(FONT, 10), width=10, bd=0, relief="flat",
                                     bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG,
                                     validate="key", validatecommand=vcmd,
                                     highlightthickness=1, highlightcolor=ENTRY_FOCUS,
                                     highlightbackground=ENTRY_BORDER)
                len_entry.grid(row=1, column=1, padx=5, pady=6, sticky="w")

                tk.Label(fields, text="💬 Comment (optional):", font=(FONT, 10),
                         bg=CARD_BG, fg=TEXT_LIGHT).grid(row=1, column=2, padx=(15, 5), pady=6, sticky="w")
                comment_entry = tk.Entry(fields, font=(FONT, 10), width=22, bd=0, relief="flat",
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
            key = f"{s['style_code']} - {s['style_name']}"
            st_map[key] = s["id"]
        return op_map, st_map

    def _validate_and_save_row(self, row, shift, op_map, st_map, entry_date=None):
        """Validate and save a single loom entry row. Returns (success, warning_tuple_or_None)."""
        length_str = row["len_entry"].get().strip()
        if not length_str:
            return None, None  # skip empty
        op_name = row["op_combo"].get()
        st_key = row["st_combo"].get()
        if not op_name or not st_key:
            messagebox.showwarning("Missing Data",
                f"Loom {row['loom']['loom_number']}: Select operator and style.")
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

        db.add_tracking_entry(the_date, shift, loom["id"], op_map[op_name],
                              st_map[st_key], length_produced, before, after, comment)
        warning = None
        if after >= LOOM_LIMIT:
            warning = (loom["loom_number"], after)
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
            messagebox.showwarning("⚠️ Over 80m",
                f"Loom {warning[0]} is at {warning[1]:.1f}m (over 80m).\nGo to Dashboard to reset or skip.")
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
            msg = "⚠️ Looms over 80m:\n"
            for num, length in warnings_list:
                msg += f"  • Loom {num}: {length:.1f}m\n"
            msg += "\nGo to Dashboard to reset or skip."
            messagebox.showwarning("⚠️ Over 80m", msg)
        self.show_daily_entry()

    # ══════════════════════════════════════════════════
    # MANAGE LOOMS
    # ══════════════════════════════════════════════════
    def show_looms(self):
        self._clear_content()
        self._set_active_nav("🏭  Looms")
        self._make_header("Manage Looms")

        # Add / Edit loom form
        card = self._make_card(self.content)
        form_title = tk.Label(card, text="➕ Add New Loom", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_num = self._make_label_entry(card, "Loom Number *", 1)
        e_loc = self._make_label_entry(card, "Location", 2)
        e_notes = self._make_label_entry(card, "Notes", 3)

        tk.Label(card, text="Status", font=(FONT, 10), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        status_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 10))
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
        tk.Label(list_card, text="All Looms  (click a row to edit)", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))
        cols = ("ID", "Loom #", "Location", "Status", "Current Length (m)", "Notes")
        tree = ttk.Treeview(list_card, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        tree.column("Notes", width=160)
        all_looms = db.get_all_looms()
        for idx, loom in enumerate(all_looms):
            if loom["current_length"] >= LOOM_LIMIT:
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
        form_title = tk.Label(card, text="➕ Add New Operator", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_name = self._make_label_entry(card, "Name *", 1)
        e_spouse = self._make_label_entry(card, "Spouse Name", 2)
        e_phone = self._make_label_entry(card, "Phone", 3)
        e_addr = self._make_label_entry(card, "Address", 4)
        e_joined = self._make_label_entry(card, "Date Joined", 5, default=date.today().isoformat())

        tk.Label(card, text="Status", font=(FONT, 10), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=6, column=0, sticky="w", padx=10, pady=6)
        active_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 10))
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
        tk.Label(list_card, text="All Operators  (click a row to edit)", font=(FONT, 13, "bold"),
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
        form_title = tk.Label(card, text="➕ Add New Style", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK)
        form_title.grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        e_code = self._make_label_entry(card, "Style Code *", 1)
        e_sname = self._make_label_entry(card, "Style Name *", 2)
        e_price = self._make_label_entry(card, "Price (₹/m)", 3, default="0", numeric_only=True)

        tk.Label(card, text="Status", font=(FONT, 10), bg=CARD_BG,
                 fg=TEXT_DARK).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        active_combo = ttk.Combobox(card, values=["Active", "Inactive"], width=27,
                                     state="readonly", font=(FONT, 10))
        active_combo.grid(row=4, column=1, sticky="w", padx=10, pady=6)
        active_combo.set("Active")

        editing_id = [None]

        def clear_form():
            editing_id[0] = None
            form_title.config(text="➕ Add New Style")
            e_code.delete(0, "end"); e_sname.delete(0, "end")
            e_price.delete(0, "end"); e_price.insert(0, "0")
            active_combo.set("Active")
            add_btn.config(text="➕ Add Style")

        def add_or_update():
            code = e_code.get().strip()
            sname = e_sname.get().strip()
            if not code or not sname:
                messagebox.showwarning("Required", "Style code and name are required.")
                return
            try:
                price = float(e_price.get().strip() or "0")
                if editing_id[0]:
                    is_active = 1 if active_combo.get() == "Active" else 0
                    db.update_style(editing_id[0], code, sname, price, is_active)
                else:
                    db.add_style(code, sname, price)
                self.show_styles()
            except ValueError:
                messagebox.showerror("Invalid", "Price must be a number.")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=5, column=1, padx=10, pady=12, sticky="w")
        add_btn = self._make_button(btn_frame, "➕ Add Style", add_or_update, color=SUCCESS)
        add_btn.pack(side="left", padx=(0, 8))
        self._make_button(btn_frame, "🗑 Clear", clear_form, color=WARNING_CLR, width=8).pack(side="left")

        list_card = self._make_card(self.content)
        tk.Label(list_card, text="All Dhothi Styles  (click a row to edit)", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).pack(anchor="w", padx=15, pady=(12, 5))
        cols = ("ID", "Code", "Name", "Price (₹/m)", "Status")
        tree = ttk.Treeview(list_card, columns=cols, show="headings", height=10)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        for idx, s in enumerate(db.get_all_styles()):
            active = "Active" if s["is_active"] else "Inactive"
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", "end", values=(s["id"], s["style_code"],
                        s["style_name"], f"₹{s['price']:.2f}", active), tags=(tag,))
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
            e_price.delete(0, "end")
            # Strip ₹ prefix from price value
            price_str = vals[3].replace("₹", "").strip()
            e_price.insert(0, price_str)
            active_combo.set(vals[4])
            add_btn.config(text="💾 Update Style")

        tree.bind("<<TreeviewSelect>>", on_row_click)


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

        tabs = [("📊  Production", "production"), ("💰  Salary", "salary"), ("✂  Loom Cuts", "cuts")]
        for label, key in tabs:
            frame = tk.Frame(tab_bar, bg=TAB_INACTIVE_BG, cursor="hand2")
            frame.pack(side="left", padx=(0, 1))
            lbl = tk.Label(frame, text=label, font=(FONT, 11, "bold"),
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
        tk.Label(card, text="🔎  Filter Production", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=6, padx=15, pady=(12, 5), sticky="w")

        tk.Label(card, text="📅 From:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        e_from = self._make_date_selector(card)
        e_from.grid(row=1, column=1, padx=5, pady=8)
        tk.Label(card, text="📅 To:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        e_to = self._make_date_selector(card)
        e_to.grid(row=1, column=3, padx=5, pady=8)
        tk.Label(card, text="Shift:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=4, padx=(15, 5), pady=8, sticky="w")
        shift_combo = ttk.Combobox(card, values=["All", "Day", "Night"], width=8, state="readonly", font=(FONT, 10))
        shift_combo.grid(row=1, column=5, padx=5, pady=8)
        shift_combo.set("All")

        loom_opts = ["All"] + [l["loom_number"] for l in looms]
        tk.Label(card, text="🏭 Loom:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=0, padx=(15, 5), pady=8, sticky="w")
        loom_combo = ttk.Combobox(card, values=loom_opts, width=10, state="readonly", font=(FONT, 10))
        loom_combo.grid(row=2, column=1, padx=5, pady=8)
        loom_combo.set("All")

        op_opts = ["All"] + [o["name"] for o in operators]
        tk.Label(card, text="👷 Operator:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=2, padx=(15, 5), pady=8, sticky="w")
        op_combo = ttk.Combobox(card, values=op_opts, width=12, state="readonly", font=(FONT, 10))
        op_combo.grid(row=2, column=3, padx=5, pady=8)
        op_combo.set("All")

        style_opts = ["All"] + [s["style_code"] for s in styles]
        tk.Label(card, text="🎨 Style:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=4, padx=(15, 5), pady=8, sticky="w")
        style_combo = ttk.Combobox(card, values=style_opts, width=10, state="readonly", font=(FONT, 10))
        style_combo.grid(row=2, column=5, padx=5, pady=8)
        style_combo.set("All")

        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=6, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)
        summary_var = tk.StringVar(value="")
        tk.Label(results_card, textvariable=summary_var, font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack(anchor="w", padx=15, pady=(0, 5))

        def search():
            for w in results_inner.winfo_children():
                w.destroy()
            start_d = e_from.get_date().isoformat()
            end_d = e_to.get_date().isoformat()
            sel_shift = shift_combo.get() if shift_combo.get() != "All" else None
            sel_loom_id = None
            if loom_combo.get() != "All":
                for l in looms:
                    if l["loom_number"] == loom_combo.get():
                        sel_loom_id = l["id"]; break
            sel_op_id = None
            if op_combo.get() != "All":
                for o in operators:
                    if o["name"] == op_combo.get():
                        sel_op_id = o["id"]; break
            sel_style_id = None
            if style_combo.get() != "All":
                for s in styles:
                    if s["style_code"] == style_combo.get():
                        sel_style_id = s["id"]; break

            rows = db.get_tracking_filtered(start_d, end_d, sel_loom_id, sel_op_id, sel_style_id, sel_shift)
            if not rows:
                tk.Label(results_inner, text="No entries found.", font=(FONT, 11), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                summary_var.set("0 entries found")
                self._report_rows = []
                return
            total_produced = sum(r["length_produced"] for r in rows)
            total_wages = sum(r["wages"] for r in rows)
            summary_var.set(f"📊  {len(rows)} entries  |  Total: {total_produced:.1f}m  |  💰 ₹{total_wages:.2f}")

            cols = ("Date", "Shift", "Loom", "Operator", "Style", "Produced (m)", "Rate (₹/m)", "Wages (₹)", "Comment")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=15)
            scroll = ttk.Scrollbar(results_inner, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=90, anchor="center")
            tree.column("Comment", width=120); tree.column("Operator", width=110)
            for idx, e in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                tree.insert("", "end", values=(e["tracking_date"], e["shift"], e["loom_number"],
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
            
            path = filedialog.asksaveasfilename(defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"loom_report_{date.today().isoformat()}.pdf")
            if not path:
                return
            
            try:
                from fpdf import FPDF
            except ImportError:
                messagebox.showerror("Dependency Missing", "Please install fpdf2 using: pip install fpdf2")
                return

            # Initialize PDF (Landscape for more columns)

            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, f"Loom Production Report - {date.today().isoformat()}", ln=True, align='C')
            pdf.ln(10)
            
            # Table Headers
            pdf.set_font("DejaVu", "B", 10)
            headers = ["Date", "Shift", "Loom", "Operator", "Style", "Meters", "Rate (₹)", "Wages (₹)"]
            widths = [30, 20, 20, 45, 35, 25, 25, 30]
            
            for i in range(len(headers)):
                pdf.cell(widths[i], 10, headers[i], border=1, align='C')
            pdf.ln()
            
            # Table Content
            pdf.set_font("Helvetica", "", 10)
            for e in self._report_rows:
                pdf.cell(widths[0], 10, str(e["tracking_date"]), border=1)
                pdf.cell(widths[1], 10, str(e["shift"]), border=1)
                pdf.cell(widths[2], 10, str(e["loom_number"]), border=1)
                pdf.cell(widths[3], 10, str(e["operator_name"]), border=1)
                pdf.cell(widths[4], 10, str(e["style_code"]), border=1)
                pdf.cell(widths[5], 10, f"{e['length_produced']:.1f}", border=1)
                pdf.cell(widths[6], 10, f"{e['style_price']:.2f}", border=1)
                pdf.cell(widths[7], 10, f"{e['wages']:.2f}", border=1)
                pdf.ln()
                
            pdf.output(path)
            messagebox.showinfo("Exported", f"PDF report saved to:\n{path}")

        self._make_button(btn_frame, "📥 Export CSV", export_csv, color=SUCCESS, width=12).pack(side="left", padx=5)
        self._make_button(btn_frame, "📄 Export PDF", export_pdf, color="#e11d48", width=12).pack(side="left", padx=5)

        def clear_filters():
            e_from.set_date(date.today()); e_to.set_date(date.today())
            shift_combo.set("All"); loom_combo.set("All")
            op_combo.set("All"); style_combo.set("All")
            search()
        self._make_button(btn_frame, "🗑 Clear", clear_filters, color=WARNING_CLR, width=10).pack(side="left", padx=5)
        search()

    # ── Salary Report ──
    def _build_salary_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)

        # Filter card
        card = self._make_card(scroll_frame)
        tk.Label(card, text="💰  Salary Report", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        tk.Label(card, text="📅 From:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        e_from = self._make_date_selector(card)
        e_from.grid(row=1, column=1, padx=5, pady=8)
        tk.Label(card, text="📅 To:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        e_to = self._make_date_selector(card)
        e_to.grid(row=1, column=3, padx=5, pady=8)
        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=2, column=0, columnspan=4, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)

        def search_salary():
            for w in results_inner.winfo_children():
                w.destroy()
            start_d = e_from.get_date().isoformat()
            end_d = e_to.get_date().isoformat()
            rows = db.get_salary_report(start_d, end_d)
            if not rows:
                tk.Label(results_inner, text="No salary data found for this period.",
                         font=(FONT, 11), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                return

            # Aggregate by operator (summary) and keep detail rows
            ops = {}
            for r in rows:
                name = r["operator_name"]
                if name not in ops:
                    ops[name] = {"day_shifts": 0, "night_shifts": 0, "total_meters": 0.0, "total_wages": 0.0, "styles": {}}
                if r["shift"] == "Day":
                    ops[name]["day_shifts"] += r["shift_count"]
                else:
                    ops[name]["night_shifts"] += r["shift_count"]
                ops[name]["total_meters"] += r["total_meters"]
                ops[name]["total_wages"] += r["total_wages"]
                # Per-style breakdown
                scode = r["style_code"]
                if scode not in ops[name]["styles"]:
                    ops[name]["styles"][scode] = {"name": r["style_name"], "rate": r["rate"],
                                                   "meters": 0.0, "wages": 0.0}
                ops[name]["styles"][scode]["meters"] += r["total_meters"]
                ops[name]["styles"][scode]["wages"] += r["total_wages"]

            grand_meters = sum(d["total_meters"] for d in ops.values())
            grand_wages = sum(d["total_wages"] for d in ops.values())
            grand_shifts = sum(d["day_shifts"] + d["night_shifts"] for d in ops.values())

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
                tk.Label(sf, text=val, font=(FONT, 14, "bold"), bg="#f8fafc", fg=clr).pack(anchor="w", padx=12, pady=(0, 8))

            # Salary table with style detail (operator → style rows)
            cols = ("Operator", "Style", "Rate (₹/m)", "Shift", "Meters", "Wages (₹)")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=18)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=110, anchor="center")
            tree.column("Operator", width=140, anchor="w")
            tree.column("Style", width=130, anchor="w")
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.tag_configure("op_total", background="#eef2ff", font=(FONT, 10, "bold"))
            row_idx = 0
            for name in sorted(ops):
                d = ops[name]
                # Style detail rows
                for scode in sorted(d["styles"]):
                    sd = d["styles"][scode]
                    tag = "even" if row_idx % 2 == 0 else "odd"
                    tree.insert("", "end", values=(
                        name if scode == sorted(d["styles"])[0] else "",
                        f"{scode} ({sd['name']})", f"₹{sd['rate']:.2f}", "",
                        f"{sd['meters']:.1f}", f"₹{sd['wages']:.2f}"), tags=(tag,))
                    row_idx += 1
                # Operator total row
                total_shifts = d["day_shifts"] + d["night_shifts"]
                avg_rate = d["total_wages"] / d["total_meters"] if d["total_meters"] > 0 else 0
                tree.insert("", "end", values=(
                    f"  ▸ {name} TOTAL", "", f"Avg ₹{avg_rate:.2f}",
                    f"D:{d['day_shifts']} N:{d['night_shifts']} = {total_shifts}",
                    f"{d['total_meters']:.1f}", f"₹{d['total_wages']:.2f}"), tags=("op_total",))
                row_idx += 1
            tree.pack(fill="both", expand=True)

        self._make_button(btn_frame, "🔍 Generate", search_salary, color=PRIMARY, width=12).pack(side="left", padx=(0, 8))
        search_salary()

    # ── Loom Cuts Report ──
    def _build_cuts_report(self, parent):
        canvas, scroll_frame = self._make_scrollable(parent)
        looms = db.get_active_looms()
        loom_opts = ["All"] + [l["loom_number"] for l in looms]

        card = self._make_card(scroll_frame)
        tk.Label(card, text="✂  Loom Cuts History", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT_DARK).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 5), sticky="w")
        tk.Label(card, text="📅 From:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=0, padx=(15, 5), pady=8, sticky="w")
        cuts_from = self._make_date_selector(card)
        cuts_from.grid(row=1, column=1, padx=5, pady=8)
        tk.Label(card, text="📅 To:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=1, column=2, padx=(15, 5), pady=8, sticky="w")
        cuts_to = self._make_date_selector(card)
        cuts_to.grid(row=1, column=3, padx=5, pady=8)
        tk.Label(card, text="🏭 Loom:", font=(FONT, 10, "bold"), bg=CARD_BG, fg=TEXT_DARK).grid(row=2, column=0, padx=(15, 5), pady=8, sticky="w")
        cuts_loom_combo = ttk.Combobox(card, values=loom_opts, width=10, state="readonly", font=(FONT, 10))
        cuts_loom_combo.grid(row=2, column=1, padx=5, pady=8)
        cuts_loom_combo.set("All")
        btn_frame = tk.Frame(card, bg=CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=4, padx=15, pady=(5, 12), sticky="w")

        results_card = self._make_card(scroll_frame)
        results_inner = tk.Frame(results_card, bg=CARD_BG)
        results_inner.pack(fill="both", padx=15, pady=10)
        cuts_summary_var = tk.StringVar(value="")
        tk.Label(results_card, textvariable=cuts_summary_var, font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=PRIMARY).pack(anchor="w", padx=15, pady=(0, 5))

        def search_cuts():
            for w in results_inner.winfo_children():
                w.destroy()
            start_d = cuts_from.get_date().isoformat()
            end_d = cuts_to.get_date().isoformat()
            sel_loom_id = None
            if cuts_loom_combo.get() != "All":
                for l in looms:
                    if l["loom_number"] == cuts_loom_combo.get():
                        sel_loom_id = l["id"]; break
            rows = db.get_loom_resets_filtered(start_d, end_d, sel_loom_id)
            if not rows:
                tk.Label(results_inner, text="No cuts found.", font=(FONT, 11), bg=CARD_BG, fg=TEXT_LIGHT).pack(pady=20)
                cuts_summary_var.set("0 cuts found")
                return
            cuts_summary_var.set(f"✂  {len(rows)} cuts found")
            cols = ("Date", "Loom", "Operator", "Dhothi Cut (m)", "Loom Total (m)", "Remaining (m)", "Skipped?", "Comment", "Recorded At")
            tree = ttk.Treeview(results_inner, columns=cols, show="headings", height=12)
            scroll = ttk.Scrollbar(results_inner, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=95, anchor="center")
            tree.column("Comment", width=180, anchor="w")
            tree.column("Operator", width=110)
            for idx, r in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                skipped = "Yes" if r["was_skipped"] else "No"
                total_len = r["length_at_reset"]
                remaining = r["remaining_length"] if r["remaining_length"] else 0.0
                cut_len = round(total_len - remaining, 1) if not r["was_skipped"] else 0.0
                tree.insert("", "end", values=(
                    r["reset_date"], r["loom_number"], r["operator_name"],
                    f"{cut_len:.1f}" if not r["was_skipped"] else "—",
                    f"{total_len:.1f}", f"{remaining:.1f}",
                    skipped, r["comment"], r["created_at"]
                ), tags=(tag,))
            tree.tag_configure("even", background="#ffffff")
            tree.tag_configure("odd", background="#f8fafc")
            tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

        self._make_button(btn_frame, "🔍 Search Cuts", search_cuts, color=PRIMARY, width=12).pack(side="left", padx=(0, 8))
        search_cuts()


# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = LoomTrackerApp(root)
    root.mainloop()
