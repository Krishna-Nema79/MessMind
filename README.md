# 🍲 MessMind - Daily Mess Meal Logging Portal

> A simple, easy-to-use web portal for mess in-charges, caretakers, and kitchen staff to record daily meals, track portions served, and review past records.

---

## 📌 Overview

**MessMind** helps college and hostel mess staff keep clear, organized records of daily meals without complicated technical tools. 

Staff can quickly:
1. **Record meals cooked and served** for Breakfast, Lunch, Snacks, and Dinner.
2. **Track leftover food** through simple, automatic arithmetic (`meals prepared − meals served`).
3. **Save ongoing meals** before dining concludes and fill in the served count later.
4. **Search and filter past records** by date range, meal session, or menu item.
5. **Download past records** as a clean CSV spreadsheet for office reporting.

No machine learning, no complex predictions, and no technical setup required.

---

## 🖥️ Portal Sections

The portal is organized into three simple sections:

| Section | What it does |
|:---|:---|
| **📊 Summary** (`/` or `/summary`) | Shows overall totals for **Meals prepared**, **Meals served**, and **Meals left over**, along with a simple comparison chart and recent activity. |
| **➕ Add a Meal Record** (`/entry` or `/add`) | A clean form to enter the date, meal session (Breakfast, Lunch, Snacks, Dinner), menu dishes, cooked count, and served count. |
| **📋 Past Records** (`/records`) | A searchable, filterable list of all previous meal records with options to view, edit, delete, or download as a CSV spreadsheet. |

---

## 🚀 How to Run the Portal (Quick Start)

### Option A: One-Click Startup (Windows)
Double-click the **`start_app.bat`** file in the project folder.  
It will automatically activate the Python environment and open the portal in your default web browser at:
👉 **`http://127.0.0.1:5000`**

---

### Option B: From the Terminal / Command Prompt

1. Open your terminal in this project folder:
   ```bash
   cd "c:\Users\LOQ\Desktop\IDT 3rd sem"
   ```

2. Activate the virtual environment:
   ```bash
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1

   # Windows Command Prompt:
   .\venv\Scripts\activate.bat
   ```

3. (Optional) Initialize the database:
   ```bash
   python database/init_db.py
   ```

4. Start the portal:
   ```bash
   python run.py
   ```

5. Open your web browser and go to:  
   👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

To run the built-in test suite:
```bash
python -m pytest -v
```

All tests run in-memory and verify:
- Leftover calculations (`prepared − served`)
- Ongoing meal handling (saving without served count)
- Form validation (negative counts blocked, served > prepared blocked, required fields)
- Duplicate session prevention
- Record editing and safe deletion
- CSV export and summary data

---

## 📁 Project Structure

```text
IDT 3rd sem/
├── app/
│   ├── models/
│   │   └── mess_record.py       # Mess record database model
│   ├── routes/
│   │   ├── main_routes.py       # Summary, Add Record, Past Records, Edit, Delete
│   │   └── api_routes.py        # Summary chart data & CSV export
│   ├── static/
│   │   ├── css/style.css        # Simple, legible responsive styling
│   │   └── js/                  # Chart and form helper scripts
│   └── templates/
│       ├── base.html            # Main layout with clean navigation
│       ├── dashboard.html       # Summary page
│       ├── entry.html           # Add a meal record form
│       ├── edit_entry.html      # Edit meal record form
│       ├── records.html         # Past records table and filters
│       └── error.html           # Friendly error pages
├── database/
│   ├── food_waste.db            # Local SQLite database storing meal records
│   ├── init_db.py               # Setup script
│   ├── schema.sql               # Database schema definition
│   └── seed_data.py             # Sample records generator for testing
├── tests/
│   ├── test_db.py               # Database model & calculation tests
│   └── test_routes.py           # Route, validation, and workflow tests
├── requirements.txt             # Lightweight Python dependencies
├── run.py                       # Application entry point
├── start_app.bat                # Windows 1-click launcher
└── README.md                    # This guide
```

---

## 🔒 Notes on Data Safety

- Existing historical mess records are safely preserved in `database/food_waste.db`.
- Obsolete AI prediction fields and tables are retired and no longer used.
- Deleting a record requires manual confirmation to prevent accidental loss.
