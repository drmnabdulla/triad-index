TRL / MRL / CRL Readiness Assessment — Desktop GUI
====================================================

This is a standalone Python desktop application (Tkinter) implementing the
same gate-based scoring engine documented in the TRIAD Index book.

REQUIREMENTS
------------
- Python 3.9+
- Tkinter (included with most Python installs; on Linux you may need
  `sudo apt install python3-tk`)

Optional, for extra features (the app runs fine without them — it detects
what's available and disables the related buttons):
- matplotlib + numpy   -> radar chart / heatmap / timeline visualizations
- pandas + openpyxl    -> Excel (.xlsx) export
- reportlab            -> PDF report export

Install the optional extras with:
    pip install matplotlib numpy pandas openpyxl reportlab

RUN
---
    python3 trl_readiness_gui.py

WHAT IT DOES
------------
- Walk through the 10 readiness categories (Technology, Product Development,
  Manufacturing Research, Manufacturing Scale-up, Product Definition/Design,
  Competitive Landscape, Team, Go-To-Market, Supply Chain, Finance).
- Live TRL / MRL / CRL scoring using the same gate logic as the web calculator.
- Dashboard tab with maturity heatmap, simulated progress timeline, and
  stage benchmarks.
- Recommendations tab: critical-gap ranking and a generated roadmap.
- Save/load assessments as JSON, export to CSV, Excel, or PDF.
- Local SQLite-backed project manager for multiple assessments.

This tool and the accompanying web version share one scoring engine so an
assessment done in either place is directly comparable.
