# 🧵 Loom Tracker

A desktop application for tracking loom machine operations and production management. Built with **Tkinter** and **SQLite**, runs fully offline with no external dependencies.

---

## ✨ Features

- **📊 Dashboard** — Overview of production metrics and key stats
- **📝 Daily Entry** — Log daily loom production and operator assignments
- **📓 Loom Ledger** — Complete history of each loom's operations
- **🏭 Looms Management** — Add, edit, and track loom machines
- **👷 Operators Management** — Manage operator profiles and assignments
- **🎨 Dhothi Styles** — Configure and manage textile styles and pricing
- **📋 Reports** — Generate production reports and analytics
- **💾 Data Export** — Export records to CSV for use in Excel
- **🔒 Offline-First** — All data stored locally in SQLite database

---

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the repository:**
   ```bash
   cd loom
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

The app will launch with sample data pre-populated for demonstration purposes.

---

## 📋 Requirements

```
fpdf2      # PDF generation for reports
python3-tk # Tkinter GUI framework (included with Python on most systems)
```

---

## 📂 Project Structure

```
loom/
├── main.py                 # Main application entry point & GUI
├── db.py                   # Database module & schema
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── sample.py              # Example/reference code
```

---

## 🗄️ Database Schema

The application uses SQLite with the following tables:

- **looms** — Loom machine records (ID, number, location, status, current length)
- **operators** — Operator profiles (name, spouse name, contact, date joined)
- **dhothi_styles** — Textile style configurations (code, name, price)
- **daily_tracking** — Daily production logs (date, shift, loom, operator, length produced)
- **loom_resets** — Loom reset history (reset date, length at reset, operator)

---

## 💻 Usage

### Starting Production
1. Open the app and navigate to **Daily Entry**
2. Select a date, shift, loom, operator, and dhothi style
3. Enter the length produced and any comments
4. Save the entry

### Viewing Reports
1. Go to **Reports** section
2. Select date range and filters
3. Generate reports or export to CSV

### Managing Looms
1. Navigate to **Looms** section
2. Add new looms or update existing ones
3. Track current length and status

---

## 🎨 UI Design

- **Modern Color Palette** — Clean, professional dark sidebar with light content area
- **Responsive Layout** — Adapts to different screen sizes (minimum 1000x650)
- **Platform Support** — Optimized fonts for macOS and Windows

---

## 🔧 Configuration

The app uses these constants (in `main.py`):
- `LOOM_LIMIT` — Maximum loom length threshold (default: 80.0)
- `BG`, `SIDEBAR_BG`, `PRIMARY` — Color customization available

---

## 💡 Tips

- The database file `loom_tracker.db` is created automatically on first run
- All timestamps are stored in local timezone
- Use the CSV export feature to analyze data in spreadsheet applications
- Data persists between sessions

---

## 📝 License

This project is provided as-is for internal use.

---

## 🤝 Support

For issues or feature requests, please contact the development team.
