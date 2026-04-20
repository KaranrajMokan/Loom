"""
Database module for Loom Tracker.
All SQLite operations for looms, operators, styles, and daily tracking.
"""
import sqlite3
from datetime import date
import sys
import os


DB_PATH = "loom_tracker.db"


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_connection():
    conn = sqlite3.connect(resource_path(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS looms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loom_number TEXT UNIQUE NOT NULL,
            location TEXT DEFAULT '',
            status TEXT DEFAULT 'Active',
            current_length REAL DEFAULT 0.0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spouse_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            date_joined TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS dhothi_styles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            style_code TEXT UNIQUE NOT NULL,
            style_name TEXT NOT NULL,
            style_category TEXT DEFAULT D,
            price REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS daily_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_date TEXT NOT NULL,
            shift TEXT NOT NULL CHECK(shift IN ('Day','Night')),
            loom_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            style_id INTEGER NOT NULL,
            length_produced REAL DEFAULT 0.0,
            loom_length_before REAL DEFAULT 0.0,
            loom_length_after REAL DEFAULT 0.0,
            comment TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (loom_id) REFERENCES looms(id),
            FOREIGN KEY (operator_id) REFERENCES operators(id),
            FOREIGN KEY (style_id) REFERENCES dhothi_styles(id)
        );
        CREATE TABLE IF NOT EXISTS loom_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loom_id INTEGER NOT NULL,
            reset_date TEXT NOT NULL,
            length_at_reset REAL DEFAULT 0.0,
            was_skipped INTEGER DEFAULT 0,
            comment TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (loom_id) REFERENCES looms(id)
        );
        CREATE TABLE IF NOT EXISTS operator_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leave_date TEXT NOT NULL,
            shift TEXT NOT NULL CHECK(shift IN ('Day','Night')),
            operator_id INTEGER NOT NULL,
            comment TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(leave_date, shift, operator_id), -- Prevent duplicate entries
            FOREIGN KEY (operator_id) REFERENCES operators(id)
        );
    """)
    conn.commit()

    # ── Schema migrations ──
    cursor = conn.execute("PRAGMA table_info(loom_resets)")
    cols = [row[1] for row in cursor.fetchall()]
    if "operator_id" not in cols:
        conn.execute("ALTER TABLE loom_resets ADD COLUMN operator_id INTEGER REFERENCES operators(id)")
        conn.commit()
    if "remaining_length" not in cols:
        conn.execute("ALTER TABLE loom_resets ADD COLUMN remaining_length REAL DEFAULT 0.0")
        conn.commit()

    conn.close()


# ── Loom CRUD ──
def add_loom(loom_number, location="", notes=""):
    conn = get_connection()
    conn.execute("INSERT INTO looms (loom_number, location, notes) VALUES (?,?,?)",
                 (loom_number, location, notes))
    conn.commit()
    conn.close()


def get_all_looms():
    conn = get_connection()
    rows = conn.execute("""
        SELECT l.*,
               CASE WHEN COALESCE(ds.style_category, 'D') = 'S' THEN 60.0 ELSE 80.0 END as cut_limit
        FROM looms l
        LEFT JOIN daily_tracking dt ON dt.id = (
            SELECT id FROM daily_tracking WHERE loom_id = l.id ORDER BY tracking_date DESC, id DESC LIMIT 1
        )
        LEFT JOIN dhothi_styles ds ON dt.style_id = ds.id
        ORDER BY l.location, l.loom_number
    """).fetchall()
    conn.close()
    return rows


def get_active_looms():
    conn = get_connection()
    rows = conn.execute("""
        SELECT l.*,
               COALESCE(ds.style_category, 'D') as current_style_category,
               CASE WHEN COALESCE(ds.style_category, 'D') = 'S' THEN 60.0 ELSE 80.0 END as cut_limit
        FROM looms l
        LEFT JOIN daily_tracking dt ON dt.id = (
            SELECT id FROM daily_tracking WHERE loom_id = l.id ORDER BY tracking_date DESC, id DESC LIMIT 1
        )
        LEFT JOIN dhothi_styles ds ON dt.style_id = ds.id
        WHERE l.status='Active' ORDER BY l.loom_number
    """).fetchall()
    conn.close()
    return rows


def update_loom(loom_id, loom_number, location, status, notes):
    conn = get_connection()
    conn.execute("UPDATE looms SET loom_number=?, location=?, status=?, notes=? WHERE id=?",
                 (loom_number, location, status, notes, loom_id))
    conn.commit()
    conn.close()


def update_loom_length(loom_id, new_length):
    conn = get_connection()
    conn.execute("UPDATE looms SET current_length=? WHERE id=?", (new_length, loom_id))
    conn.commit()
    conn.close()


def reset_loom_length(loom_id, length_at_reset, was_skipped=False, comment="", remaining_length=0.0, operator_id=None):
    """Reset loom length. remaining_length is how much dhothi stays in the loom after cut."""
    conn = get_connection()
    conn.execute("""INSERT INTO loom_resets (loom_id, reset_date, length_at_reset, was_skipped, comment, operator_id, remaining_length)
                    VALUES (?,?,?,?,?,?,?)""",
                 (loom_id, date.today().isoformat(), length_at_reset, int(was_skipped), comment, operator_id, remaining_length))
    if not was_skipped:
        conn.execute("UPDATE looms SET current_length=? WHERE id=?", (remaining_length, loom_id))
    conn.commit()
    conn.close()


# ── Operator CRUD ──
def add_operator(name, spouse_name="", phone="", address="", date_joined=""):
    conn = get_connection()
    conn.execute("INSERT INTO operators (name, spouse_name, phone, address, date_joined) VALUES (?,?,?,?,?)",
                 (name, spouse_name, phone, address, date_joined))
    conn.commit()
    conn.close()


def get_all_operators():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM operators ORDER BY name").fetchall()
    conn.close()
    return rows


def get_active_operators():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM operators WHERE is_active=1 ORDER BY name").fetchall()
    conn.close()
    return rows


def update_operator(op_id, name, spouse_name, phone, address, date_joined, is_active):
    conn = get_connection()
    conn.execute("""UPDATE operators SET name=?, spouse_name=?, phone=?, address=?,
                    date_joined=?, is_active=? WHERE id=?""",
                 (name, spouse_name, phone, address, date_joined, is_active, op_id))
    conn.commit()
    conn.close()


# ── Style CRUD ──
def add_style(style_code, style_name, price=0.0, category="D"):
    conn = get_connection()
    conn.execute("INSERT INTO dhothi_styles (style_code, style_name, price, style_category) VALUES (?,?,?,?)",
                 (style_code, style_name, price, category))
    conn.commit()
    conn.close()


def get_all_styles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM dhothi_styles ORDER BY style_code").fetchall()
    conn.close()
    return rows


def get_active_styles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM dhothi_styles WHERE is_active=1 ORDER BY style_code").fetchall()
    conn.close()
    return rows


def update_style(style_id, style_code, style_name, price, category, is_active):
    conn = get_connection()
    conn.execute("UPDATE dhothi_styles SET style_code=?, style_name=?, price=?, style_category=?, is_active=? WHERE id=?",
                 (style_code, style_name, price, category, is_active, style_id))
    conn.commit()
    conn.close()


# ── Daily Tracking ──
def get_existing_entry(tracking_date, shift, loom_id):
    """Check if an entry already exists for this loom+shift+date. Returns joined row with names."""
    conn = get_connection()
    row = conn.execute("""SELECT dt.*, o.name AS operator_name,
                                 s.style_code, s.style_name
                          FROM daily_tracking dt
                          LEFT JOIN operators o ON dt.operator_id = o.id
                          LEFT JOIN dhothi_styles s ON dt.style_id = s.id
                          WHERE dt.tracking_date=? AND dt.shift=? AND dt.loom_id=?""",
                       (tracking_date, shift, loom_id)).fetchone()
    conn.close()
    return row


def add_tracking_entry(tracking_date, shift, loom_id, operator_id, style_id,
                       length_produced, loom_length_before, loom_length_after, comment=""):
    conn = get_connection()
    # Check if entry already exists for this loom+shift+date
    existing = conn.execute("""SELECT id, length_produced FROM daily_tracking
                               WHERE tracking_date=? AND shift=? AND loom_id=?""",
                            (tracking_date, shift, loom_id)).fetchone()
    if existing:
        # Undo old length from loom, apply new length
        old_produced = existing["length_produced"]
        new_before = loom_length_before  # current_length already includes old entry
        # Recalculate: undo old addition, apply new
        corrected_before = loom_length_before - old_produced
        corrected_after = corrected_before + length_produced
        conn.execute("""UPDATE daily_tracking
                        SET operator_id=?, style_id=?, length_produced=?,
                            loom_length_before=?, loom_length_after=?, comment=?,
                            created_at=datetime('now','localtime')
                        WHERE id=?""",
                     (operator_id, style_id, length_produced,
                      corrected_before, corrected_after, comment, existing["id"]))
        conn.execute("UPDATE looms SET current_length=? WHERE id=?", (corrected_after, loom_id))
    else:
        conn.execute("""INSERT INTO daily_tracking
            (tracking_date, shift, loom_id, operator_id, style_id,
             length_produced, loom_length_before, loom_length_after, comment)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (tracking_date, shift, loom_id, operator_id, style_id,
             length_produced, loom_length_before, loom_length_after, comment))
        conn.execute("UPDATE looms SET current_length=? WHERE id=?", (loom_length_after, loom_id))
    conn.commit()
    conn.close()


def get_tracking_for_date(tracking_date, shift=None):
    conn = get_connection()
    query = """SELECT dt.*, l.loom_number, o.name as operator_name,
                      ds.style_code, ds.style_name
               FROM daily_tracking dt
               JOIN looms l ON dt.loom_id = l.id
               JOIN operators o ON dt.operator_id = o.id
               JOIN dhothi_styles ds ON dt.style_id = ds.id
               WHERE dt.tracking_date = ?"""
    params = [tracking_date]
    if shift:
        query += " AND dt.shift = ?"
        params.append(shift)
    query += " ORDER BY l.loom_number"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_tracking_range(start_date, end_date):
    conn = get_connection()
    rows = conn.execute("""SELECT dt.*, l.loom_number, o.name as operator_name,
                                  ds.style_code, ds.style_name
                           FROM daily_tracking dt
                           JOIN looms l ON dt.loom_id = l.id
                           JOIN operators o ON dt.operator_id = o.id
                           JOIN dhothi_styles ds ON dt.style_id = ds.id
                           WHERE dt.tracking_date BETWEEN ? AND ?
                           ORDER BY dt.tracking_date DESC, dt.shift, l.loom_number""",
                        (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_looms_over_limit():
    conn = get_connection()
    rows = conn.execute("""
        SELECT l.*,
               COALESCE(ds.style_category, 'D') as current_style_category,
               CASE WHEN COALESCE(ds.style_category, 'D') = 'S' THEN 60.0 ELSE 80.0 END as cut_limit
        FROM looms l
        LEFT JOIN daily_tracking dt ON dt.id = (
            SELECT id FROM daily_tracking WHERE loom_id = l.id ORDER BY tracking_date DESC, id DESC LIMIT 1
        )
        LEFT JOIN dhothi_styles ds ON dt.style_id = ds.id
        WHERE l.status='Active'
          AND l.current_length >= CASE WHEN COALESCE(ds.style_category, 'D') = 'S' THEN 60.0 ELSE 80.0 END
        ORDER BY l.loom_number
    """).fetchall()
    conn.close()
    return rows


def delete_tracking_entry(entry_id):
    conn = get_connection()
    conn.execute("DELETE FROM daily_tracking WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


def get_last_entry_for_loom(loom_id):
    """Get the most recent tracking entry for a loom (any shift), with operator name."""
    conn = get_connection()
    row = conn.execute("""SELECT dt.*, o.name as operator_name,
                                 ds.style_code, ds.style_name
                          FROM daily_tracking dt
                          JOIN operators o ON dt.operator_id = o.id
                          JOIN dhothi_styles ds ON dt.style_id = ds.id
                          WHERE dt.loom_id = ?
                          ORDER BY dt.tracking_date DESC, dt.id DESC
                          LIMIT 1""", (loom_id,)).fetchone()
    conn.close()
    return row


def get_last_entry_for_loom_shift(loom_id, shift):
    """Get the most recent tracking entry for a specific loom and shift."""
    conn = get_connection()
    row = conn.execute("""SELECT dt.*, o.name as operator_name,
                                 ds.style_code, ds.style_name
                          FROM daily_tracking dt
                          JOIN operators o ON dt.operator_id = o.id
                          JOIN dhothi_styles ds ON dt.style_id = ds.id
                          WHERE dt.loom_id = ? AND dt.shift = ?
                          ORDER BY dt.tracking_date DESC, dt.id DESC
                          LIMIT 1""", (loom_id, shift)).fetchone()
    conn.close()
    return row


def get_tracking_filtered(start_date=None, end_date=None, loom_ids=None,
                          operator_ids=None, style_ids=None, shifts=None):
    """Get tracking entries with multi-select optional filters."""
    conn = get_connection()
    query = """SELECT dt.*, l.loom_number, o.name as operator_name,
                      ds.style_code, ds.style_name, ds.price as style_price,
                      (dt.length_produced * ds.price) as wages, comment
               FROM daily_tracking dt
               JOIN looms l ON dt.loom_id = l.id
               JOIN operators o ON dt.operator_id = o.id
               JOIN dhothi_styles ds ON dt.style_id = ds.id
               WHERE 1=1"""
    params = []
    if start_date:
        query += " AND dt.tracking_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND dt.tracking_date <= ?"
        params.append(end_date)
    if loom_ids is not None:
        if not loom_ids: return []
        placeholders = ",".join("?" * len(loom_ids))
        query += f" AND dt.loom_id IN ({placeholders})"
        params.extend(loom_ids)
    if operator_ids is not None:
        if not operator_ids: return []
        placeholders = ",".join("?" * len(operator_ids))
        query += f" AND dt.operator_id IN ({placeholders})"
        params.extend(operator_ids)
    if style_ids is not None:
        if not style_ids: return []
        placeholders = ",".join("?" * len(style_ids))
        query += f" AND dt.style_id IN ({placeholders})"
        params.extend(style_ids)
    if shifts is not None:
        if not shifts: return []
        placeholders = ",".join("?" * len(shifts))
        query += f" AND dt.shift IN ({placeholders})"
        params.extend(shifts)
    query += " ORDER BY dt.tracking_date DESC, dt.shift, l.loom_number"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_loom_resets_filtered(start_date=None, end_date=None, loom_ids=None, style_ids=None):
    """Get loom reset/cut history with optional filters, including operator name and dhothi style."""
    conn = get_connection()
    query = """SELECT lr.*, l.loom_number,
                      COALESCE(o.name, '—') as operator_name,
                      COALESCE(ds.style_code, '—') as style_code,
                      COALESCE(ds.style_name, '—') as style_name,
                      dt.shift
               FROM loom_resets lr
               JOIN looms l ON lr.loom_id = l.id
               LEFT JOIN operators o ON lr.operator_id = o.id
               LEFT JOIN daily_tracking dt ON dt.id = (
                   SELECT id FROM daily_tracking
                   WHERE loom_id = lr.loom_id AND tracking_date <= lr.reset_date
                   ORDER BY tracking_date DESC, id DESC LIMIT 1
               )
               LEFT JOIN dhothi_styles ds ON dt.style_id = ds.id
               WHERE 1=1"""
    params = []
    if start_date:
        query += " AND lr.reset_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND lr.reset_date <= ?"
        params.append(end_date)
    if loom_ids is not None:
        if not loom_ids: return []
        placeholders = ",".join("?" * len(loom_ids))
        query += f" AND lr.loom_id IN ({placeholders})"
        params.extend(loom_ids)
    if style_ids is not None:
        if not style_ids: return []
        placeholders = ",".join("?" * len(style_ids))
        query += f" AND ds.id IN ({placeholders})"
        params.extend(style_ids)
    query += " ORDER BY lr.reset_date DESC, lr.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_remaining_looms_filtered(loom_ids=None, style_ids=None, locations=None):
    """Fetch current length in looms, with optional filters for loom, style, and location."""
    conn = get_connection()
    query = """SELECT l.loom_number, l.location, l.current_length,
                      COALESCE(ds.style_code, '—') as style_code,
                      COALESCE(ds.style_name, '—') as style_name,
                      CASE WHEN COALESCE(ds.style_category, 'D') = 'S' THEN 60.0 ELSE 80.0 END as cut_limit
               FROM looms l
               LEFT JOIN daily_tracking dt ON dt.id = (
                   SELECT id FROM daily_tracking
                   WHERE loom_id = l.id
                   ORDER BY tracking_date DESC, id DESC LIMIT 1
               )
               LEFT JOIN dhothi_styles ds ON dt.style_id = ds.id
               WHERE l.status = 'Active'"""

    params = []
    if loom_ids is not None:
        if not loom_ids: return []
        placeholders = ",".join("?" * len(loom_ids))
        query += f" AND l.id IN ({placeholders})"
        params.extend(loom_ids)
    if style_ids is not None:
        if not style_ids: return []
        placeholders = ",".join("?" * len(style_ids))
        query += f" AND ds.id IN ({placeholders})"
        params.extend(style_ids)
    if locations is not None:
        if not locations: return []
        placeholders = ",".join("?" * len(locations))
        query += f" AND l.location IN ({placeholders})"
        params.extend(locations)

    query += " ORDER BY l.loom_number"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def has_data():
    """Check if any looms exist (i.e. DB has been populated)."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM looms").fetchone()[0]
    conn.close()
    return count > 0


# ------------------------------------------------------------------
# ── Operator Leaves ──
# ------------------------------------------------------------------
def add_operator_leave(leave_date, shift, operator_id, comment=""):
    """Adds a new leave record. Returns True on success, False on duplicate."""
    conn = get_connection()
    try:
        conn.execute("""INSERT INTO operator_leaves (leave_date, shift, operator_id, comment)
                        VALUES (?,?,?,?)""", (leave_date, shift, operator_id, comment))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Duplicate entry
    finally:
        conn.close()


def get_leaves_for_date(the_date):
    """Returns all operators on leave for a specific date (joined with names)."""
    conn = get_connection()
    rows = conn.execute("""SELECT ol.*, o.name as operator_name
                           FROM operator_leaves ol
                           JOIN operators o ON ol.operator_id = o.id
                           WHERE ol.leave_date = ?
                           ORDER BY ol.shift, o.name""", (the_date,)).fetchall()
    conn.close()
    return rows


def get_leave_dates_for_month(year, month):
    """Returns a distinct set of dates that have leave records in a given month."""
    conn = get_connection()
    # Format pattern for SQLite like '2026-04-%'
    pattern = f"{year}-{month:02d}-%"
    rows = conn.execute("""SELECT DISTINCT leave_date FROM operator_leaves
                           WHERE leave_date LIKE ?""", (pattern,)).fetchall()
    conn.close()
    return [r['leave_date'] for r in rows]


def delete_leave_entry(leave_id):
    """Removes a specific leave entry."""
    conn = get_connection()
    conn.execute("DELETE FROM operator_leaves WHERE id=?", (leave_id,))
    conn.commit()
    conn.close()


def get_salary_report(start_date, end_date, operator_ids=None):
    """Get salary breakdown per operator per style per shift, with optional multi-select operator filter."""
    conn = get_connection()
    query = """
        SELECT o.name as operator_name,
               dt.tracking_date,
               ds.style_code,
               ds.style_name,
               ds.price as rate,
               dt.shift,
               SUM(dt.length_produced) as total_meters
        FROM daily_tracking dt
        JOIN operators o ON dt.operator_id = o.id
        JOIN dhothi_styles ds ON dt.style_id = ds.id
        WHERE dt.tracking_date >= ? AND dt.tracking_date <= ?
    """
    params = [start_date, end_date]
    
    if operator_ids is not None:
        if not operator_ids: return [] # Return empty if no operators selected
        placeholders = ",".join("?" * len(operator_ids))
        query += f" AND dt.operator_id IN ({placeholders})"
        params.extend(operator_ids)
        
    query += """
        GROUP BY dt.tracking_date, o.name, ds.style_code, dt.shift
        ORDER BY dt.tracking_date, o.name, ds.style_code, dt.shift
    """
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_leave_counts(start_date, end_date):
    """Count total leaves taken by each operator in the given date range."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT o.name as operator_name, COUNT(*) as leave_count
        FROM operator_leaves ol
        JOIN operators o ON ol.operator_id = o.id
        WHERE ol.leave_date >= ? AND ol.leave_date <= ?
        GROUP BY o.name
    """, (start_date, end_date)).fetchall()
    conn.close()
    # Returns a dictionary: {"Operator Name": 2, "Another Name": 1}
    return {r["operator_name"]: r["leave_count"] for r in rows}


def insert_base_data():
    """Populate DB with looms, operators, and styles"""
    if has_data():
        return  # Don't duplicate

    base_looms = [
        ("103", "1"),
        ("104", "1"),
        ("105", "1"),
        ("106", "1"),
        ("107", "1"),
        ("108", "1"),
        ("109", "1"),
        ("110", "1"),
        ("111", "1"),
        ("112", "1"),
        ("113", "1"),
        ("114", "1"),
        ("115", "1"),
        ("116", "1"),
        ("117", "1"),
        ("118", "1"),
        ("119", "1"),
        ("120", "1"),
        ("85", "2"),
        ("86", "2"),
        ("87", "2"),
        ("88", "2"),
        ("89", "2"),
        ("90", "2"),
        ("91", "2"),
        ("92", "2"),
        ("93", "2"),
        ("94", "2"),
        ("95", "2"),
        ("96", "2"),
        ("97", "2"),
        ("98", "2"),
        ("99", "2"),
        ("100", "2"),
        ("101", "2"),
        ("102", "2"),
        ("69", "4"),
        ("70", "4"),
        ("71", "4"),
        ("72", "4"),
        ("73", "4"),
        ("74", "4"),
        ("75", "4"),
        ("76", "4"),
        ("77", "4"),
        ("78", "4"),
        ("79", "4"),
        ("80", "4"),
        ("81", "4"),
        ("82", "4"),
        ("83", "4"),
        ("84", "4"),
        ("53", "5"),
        ("54", "5"),
        ("55", "5"),
        ("56", "5"),
        ("57", "5"),
        ("58", "5"),
        ("59", "5"),
        ("60", "5"),
        ("61", "5"),
        ("62", "5"),
        ("63", "5"),
        ("64", "5"),
        ("65", "5"),
        ("66", "5"),
        ("67", "5"),
        ("68", "5"),
        ("37", "6"),
        ("38", "6"),
        ("39", "6"),
        ("40", "6"),
        ("41", "6"),
        ("42", "6"),
        ("43", "6"),
        ("44", "6"),
        ("45", "6"),
        ("46", "6"),
        ("47", "6"),
        ("48", "6"),
        ("49", "6"),
        ("50", "6"),
        ("51", "6"),
        ("52", "6"),
        ("21", "7"),
        ("22", "7"),
        ("23", "7"),
        ("24", "7"),
        ("25", "7"),
        ("26", "7"),
        ("27", "7"),
        ("28", "7"),
        ("29", "7"),
        ("30", "7"),
        ("31", "7"),
        ("32", "7"),
        ("33", "7"),
        ("34", "7"),
        ("35", "7"),
        ("36", "7"),
        ("121", "8"),
        ("122", "8"),
        ("123", "8"),
        ("124", "8"),
        ("125", "8"),
        ("126", "8"),
        ("127", "8"),
        ("128", "8"),
        ("129", "8"),
        ("130", "8"),
        ("131", "8"),
        ("132", "8"),
        ("133", "8"),
        ("134", "8"),
        ("135", "8"),
        ("136", "8")
    ]
    for num, loc in base_looms:
        add_loom(num, loc)

    # Base operators
    base_operators = [
        ("Raman", "Lakshmi", "9876543210", "12 Weaver St", "2023-01-15"),
        ("Selvam", "Meena", "9876543211", "34 Mill Rd", "2023-03-20"),
        ("Murugan", "Kavitha", "9876543212", "56 Loom Lane", "2023-06-01"),
        ("Kannan", "Priya", "9876543213", "78 Thread Ave", "2024-01-10"),
    ]
    for name, spouse, phone, addr, joined in base_operators:
        add_operator(name, spouse, phone, addr, joined)

    # Base dhothi styles
    base_styles = [
        ("120-e-gold", "120 E Gold", 5.35),
        ("120-e-silver", "120 E Silver", 5.35),
        ("150-e-gold", "150 E Gold", 5.35),
        ("150-e-silver", "150 E Silver", 5.35),
        ("180-e-gold", "180 E Gold", 5.35),
        ("180-e-silver", "180 E Silver", 5.35),
        ("180-e-line-gold", "180 E Line Gold", 5.85),
        ("180-e-line-silver", "180 E Line Silver", 5.85),
        ("180-e-tissue-gold", "180 E Tissue Gold", 5.35),
        ("240-e-gold", "240 E Gold", 5.50),
        ("240-e-silver", "240 E Silver", 5.50),
        ("168-e-tvk", "168 E TVK", 5.60),
        ("144-e-fancy", "144 E Fancy", 5.60),
        ("120-a-gold", "120 A Gold", 5.35),
        ("180-e-black", "180 E Black", 5.50),
    ]
    for code, name, price in base_styles:
        add_style(code, name, price)
