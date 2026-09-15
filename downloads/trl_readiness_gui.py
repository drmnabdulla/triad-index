"""
TRL/MRL/CRL Assessment Tool - Version 4
Enhanced with dashboard, recommendations, advanced export, and project management.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple, List
import json
import math
import csv
import sqlite3
from pathlib import Path

# Optional charting libraries
try:
    import numpy as np
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

# Optional data analysis libraries
try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False

# Optional PDF reporting
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

# ============================================================================
# Data Models & Scoring Engine
# ============================================================================

@dataclass(frozen=True)
class NextStep:
    """Represents what is needed to reach the next readiness level."""
    target_level: int
    gaps: Dict[str, Tuple[int, int]]  # category -> (current_level, required_level)

    def to_multiline_text(self) -> str:
        if not self.gaps:
            return "All requirements are already met."
        lines = []
        for cat, (cur, req) in self.gaps.items():
            lines.append(f"- {cat}: current {cur} → required {req}")
        return "\n".join(lines)

class ReadinessScorer:
    """
    Spreadsheet-aligned scoring engine.
    The Excel workbook computes readiness as the highest level whose gate is satisfied.
    """

    # Spreadsheet-equivalent gate requirements
    TRL_RULES: Dict[int, Dict[str, int]] = {
        1: {"Technology": 1},
        2: {"Technology": 2},
        3: {"Technology": 3},
        4: {"Technology": 4},
        5: {"Technology": 5},
        6: {"Technology": 5, "Product Development": 2},
        7: {"Technology": 5, "Product Development": 3},
        8: {"Technology": 5, "Product Development": 4},
        9: {"Technology": 5, "Product Development": 5},
    }

    CRL_RULES: Dict[int, Dict[str, int]] = {
        1: {"Product Definition/Design": 1, "Competitive Landscape": 1, "Team": 1, "Go-To-Market": 1, "Supply Chain": 1, "Finance": 1},
        2: {"Product Definition/Design": 2, "Competitive Landscape": 2, "Team": 2, "Go-To-Market": 1, "Supply Chain": 1, "Finance": 1},
        3: {"Product Definition/Design": 3, "Competitive Landscape": 3, "Team": 2, "Go-To-Market": 2, "Supply Chain": 1, "Finance": 1},
        4: {"Product Definition/Design": 4, "Competitive Landscape": 4, "Team": 3, "Go-To-Market": 3, "Supply Chain": 2, "Finance": 2},
        5: {"Product Definition/Design": 5, "Competitive Landscape": 5, "Team": 3, "Go-To-Market": 4, "Supply Chain": 3, "Finance": 3},
        6: {"Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 4, "Go-To-Market": 5, "Supply Chain": 3, "Finance": 4},
        7: {"Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 4, "Go-To-Market": 6, "Supply Chain": 4, "Finance": 5},
        8: {"Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 5, "Go-To-Market": 6, "Supply Chain": 5, "Finance": 6},
        9: {"Product Definition/Design": 6, "Competitive Landscape": 5, "Team": 5, "Go-To-Market": 6, "Supply Chain": 6, "Finance": 7},
    }

    MRL_RULES: Dict[int, Dict[str, int]] = {
        1: {"Manufacturing Research": 1, "Technology": 1},
        2: {"Manufacturing Research": 2, "Technology": 2},
        3: {"Manufacturing Research": 3, "Technology": 3},
        4: {"Manufacturing Research": 4, "Technology": 4},
        5: {"Manufacturing Research": 5, "Technology": 5},
        6: {"Manufacturing Research": 5, "Manufacturing Scale-up": 2, "Technology": 5, "Product Development": 2},
        7: {"Manufacturing Research": 5, "Manufacturing Scale-up": 3, "Technology": 5, "Product Development": 3},
        8: {"Manufacturing Research": 5, "Manufacturing Scale-up": 4, "Technology": 5, "Product Development": 3},
        9: {"Manufacturing Research": 5, "Manufacturing Scale-up": 5, "Technology": 5, "Product Development": 4},
        10: {"Manufacturing Research": 5, "Manufacturing Scale-up": 6, "Technology": 5, "Product Development": 5},
    }

    @staticmethod
    def score_from_rules(selections: Dict[str, int], rules: Dict[int, Dict[str, int]]) -> int:
        best = 0
        for level in sorted(rules.keys()):
            req = rules[level]
            if all(selections.get(cat, 0) >= min_level for cat, min_level in req.items()):
                best = level
        return best

    @staticmethod
    def gaps_for_level(selections: Dict[str, int], rules: Dict[int, Dict[str, int]], level: int) -> Dict[str, Tuple[int, int]]:
        req = rules.get(level, {})
        gaps: Dict[str, Tuple[int, int]] = {}
        for cat, min_level in req.items():
            cur = selections.get(cat, 0)
            if cur < min_level:
                gaps[cat] = (cur, min_level)
        return gaps

    @classmethod
    def next_step(cls, selections: Dict[str, int], rules: Dict[int, Dict[str, int]], current_level: int) -> Optional[NextStep]:
        target = current_level + 1
        if target not in rules:
            return None
        return NextStep(target_level=target, gaps=cls.gaps_for_level(selections, rules, target))

# ============================================================================
# Project & Settings Management
# ============================================================================

class ProjectManager:
    """Manage multiple assessment projects."""
    def __init__(self, db_path="projects.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (id TEXT PRIMARY KEY,
                      project_data TEXT,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_project(self, project_id, project_data):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO projects
                     (id, project_data, created_at, updated_at)
                     VALUES (?, ?, ?, ?)''',
                  (project_id, json.dumps(project_data),
                   datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def load_project(self, project_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT project_data FROM projects WHERE id=?", (project_id,))
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None

    def list_projects(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, created_at, updated_at FROM projects ORDER BY updated_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

class SettingsManager:
    """Manage application settings and preferences."""
    DEFAULT_SETTINGS = {
        "ui": {
            "theme": "light",
            "font_size": 10,
            "show_tooltips": True,
            "auto_save": False,
            "save_interval": 300,
        },
        "scoring": {
            "default_level": 1,
            "strict_mode": False,
            "custom_weights": {"TRL": 0.4, "MRL": 0.3, "CRL": 0.3},
        },
        "export": {
            "default_format": "json",
            "include_comments": True,
            "include_charts": True,
            "compression": False,
        }
    }

    def __init__(self, config_file="settings.json"):
        self.config_file = config_file
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get(self, section, key):
        return self.settings.get(section, {}).get(key, self.DEFAULT_SETTINGS[section][key])

# ============================================================================
# UI Components
# ============================================================================

class ScrollableFrame(ttk.Frame):
    """Reusable scrollable frame."""
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vscroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vscroll.pack(side="right", fill="y")
        self._bind_mousewheel()

    def _on_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self):
        def _on_mousewheel(event):
            if hasattr(event, "delta") and event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

class ToolTip:
    """Create a tooltip for a widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#ffffe0", relief="solid", borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# ============================================================================
# Main Application
# ============================================================================

class TRLAssessmentAppV4:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Market Readiness Calculator - TRL/MRL/CRL Assessment Tool (V4)")
        self.root.geometry("1300x900")

        # Initialize managers
        self.scorer = ReadinessScorer()
        self.project_manager = ProjectManager()
        self.settings = SettingsManager()

        # Data storage
        self.current_project = {
            "id": f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "profile": {"company_name": "", "project_title": "", "project_description": ""},
            "categories": {},
            "scores": {"TRL": 0, "MRL": 0, "CRL": 0},
            "updated_at": None,
            "version": "v4-enhanced"
        }

        # UI: notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_menu()
        self._init_categories()
        self._create_all_tabs()

        # Initialize computed display
        self.update_scores()

    # ------------------------------------------------------------------------
    # Data & configuration
    # ------------------------------------------------------------------------
    def _init_categories(self):
        # Category definitions (same as original)
        self.categories: Dict[str, Dict] = {
            "Technology": {
                "levels": [
                    "Basic principles have been observed through scientific research",
                    "Applied research has begun and practical application(s) have been identified",
                    "Preliminary testing of technology components has begun, and technical feasibility has been established in a laboratory environment",
                    "Initial testing of integrated product/system has been completed in a laboratory environment",
                    "Laboratory scale integrated product/system demonstrates performance in the intended application(s)",
                ],
                "type": "TRL",
                "max_level": 5,
            },
            "Product Development": {
                "levels": [
                    "Product/system has not yet been validated at the pilot scale",
                    "Pilot scale product/system has been tested in the intended application(s)",
                    "Demonstration of a full scale product/system prototype has been completed in the intended application(s)",
                    "Actual product/system has been proven to work in its near-final form under a representative set of expected conditions and environments",
                    "Product/system is in final form and has been operated under the full range of operating conditions and environments",
                ],
                "type": "TRL",
                "max_level": 5,
            },
            "Product Definition/Design": {
                "levels": [
                    "Knowledge of potential applications is limited",
                    "Product ideas based on the new technology may exist, but are speculative and invalidated",
                    "One or more initial product hypotheses have been defined",
                    "Mapping product/system attributes against customer needs has highlighted a clear value proposition",
                    "Comprehensive customer value proposition model has been developed, including a detailed understanding of product/system design specifications, required certifications, and trade-offs",
                    "Product/system final design optimization has been completed, required certifications have been obtained, and product/system has incorporated detailed customer and product requirements",
                ],
                "type": "CRL",
                "max_level": 6,
            },
            "Competitive Landscape": {
                "levels": [
                    "Knowledge of market constraints is limited",
                    "Market research is derived primarily from secondary sources and basic understanding of competitive products/systems has been demonstrated",
                    "Comprehensive market research to prove the product/system commercial feasibility has been completed and intermediate understanding of competitive products/systems has been demonstrated",
                    "Competitive analysis to illustrate unique features and advantages of the product/system compared to competitive products/systems has been completed",
                    "Full and complete understanding of the competitive landscape, target application(s), competitive products/systems, and market has been achieved",
                ],
                "type": "CRL",
                "max_level": 5,
            },
            "Team": {
                "levels": [
                    "No team or company in place (single individual, no legal entity)",
                    "Solely technical or non-technical founder(s) running the company with no outside assistance",
                    "Solely technical or non-technical founder(s) running the company with assistance from outside advisors/mentors and/or incubator/accelerator",
                    "Balanced team with technical and business development/commercialization experience running the company with assistance from outside advisors/mentors",
                    "Balanced team with all capabilities onboard (e.g. sales, marketing, customer service, operations, etc.) running the company with assistance from outside advisors/mentors",
                ],
                "type": "CRL",
                "max_level": 5,
            },
            "Manufacturing Research": {
                "levels": [
                    "Work to identify manufacturing approach and cost model has not begun or is incomplete",
                    "Applied research to analyze properties and availability of materials for manufacturing is underway",
                    "Materials and processes have been evaluated for manufacturability using experiments or models to estimate yields and rates",
                    "Manufacturing risks, cost drivers, performance parameters, and investments required have been identified",
                    "Prototype components have been produced in a production relevant environment, and planning to address scale-up issues has begun",
                ],
                "type": "MRL",
                "max_level": 5,
            },
            "Manufacturing Scale-up": {
                "levels": [
                    "The full manufacturing approach has not yet been demonstrated in a production relevant environment",
                    "A preliminary manufacturing system design has been developed, and further design changes are required for a successful demonstration of the system",
                    "The manufacturing system has been demonstrated in a representative environment, and a detailed system design is nearing completion",
                    "A detailed manufacturing system design is complete and sufficiently stable to enter low rate production",
                    "The system has successfully achieved low rate production and is ready to enter full rate production with minimal design changes",
                    "Full rate production has been demonstrated to meet requirements for performance, quality, and reliability",
                ],
                "type": "MRL",
                "max_level": 6,
            },
            "Go-To-Market": {
                "levels": [
                    "Value proposition has not yet been developed",
                    "Initial business model and value proposition have been defined",
                    "Customers/partners have been interviewed to understand their pain points/needs, and business model and value proposition have been refined based on customer/partner feedback",
                    "Market and customer/partner needs and how those translate to product requirements have been defined, and initial relationships have been developed with key stakeholders across the value chain",
                    "Partnerships have been formed with key stakeholders across the value chain (e.g. suppliers, partners, service providers, and customers)",
                    "Supply agreements with suppliers and partners are in place",
                ],
                "type": "CRL",
                "max_level": 6,
            },
            "Supply Chain": {
                "levels": [
                    "Potential suppliers and customers have not yet been identified",
                    "Potential suppliers, partners, and customers have been identified and mapped in an initial value chain analysis",
                    "Relationships have been established with potential suppliers, partners, service providers, and customers and they have provided input on product and manufacturability requirements",
                    "Manufacturing process qualifications (e.g. QC/QA) have been defined and are in progress",
                    "Products/systems have been pilot manufactured and sold to initial customers",
                    "Full scale manufacturing and widespread deployment of product/system to customers and/or users has been achieved",
                ],
                "type": "CRL",
                "max_level": 6,
            },
            "Finance": {
                "levels": [
                    "Non-dilutive funding sources, such as grants, have been sought or obtained",
                    "Funding needs have been identified based on business model and financial plan",
                    "Potential sources of external financing have been identified",
                    "The company is being pitched to private investors with a business plan/presentation that includes revenue projections",
                    "Private investment has been raised",
                    "Purchase orders from customers have been received",
                    "Revenue is being collected via paid purchase orders",
                ],
                "type": "CRL",
                "max_level": 7,
            },
        }

        # Selection variables
        self.selection_vars: Dict[str, tk.IntVar] = {name: tk.IntVar(value=1) for name in self.categories.keys()}

    # ------------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Assessment", command=self.reset_assessment)
        file_menu.add_command(label="Open JSON...", command=self.load_from_json)
        file_menu.add_separator()
        file_menu.add_command(label="Save JSON...", command=self.export_to_json)
        file_menu.add_command(label="Export CSV...", command=self.export_to_csv)
        file_menu.add_command(label="Export Excel...", command=self.export_to_excel)
        file_menu.add_command(label="Export PDF...", command=self.export_to_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Compare Projects", command=self.open_comparison_tool)
        tools_menu.add_command(label="Generate Roadmap", command=self.generate_roadmap)
        tools_menu.add_command(label="Settings", command=self.open_settings)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        self.root.config(menu=menubar)

    # ------------------------------------------------------------------------
    # Tab creation
    # ------------------------------------------------------------------------
    def _create_all_tabs(self):
        self.create_welcome_tab()
        self.create_profile_tab()
        self.create_assessment_tabs()
        self.create_dashboard_tab()      # NEW
        self.create_recommendations_tab() # NEW
        self.create_summary_tab()
        self.create_help_tab()

    def create_welcome_tab(self):
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Welcome")
        ttk.Label(welcome_frame, text="Market Readiness Calculator", font=("Arial", 24, "bold")).pack(pady=15)
        ttk.Label(welcome_frame, text="TRL / MRL / CRL Assessment Tool (Version 4)", font=("Arial", 14)).pack(pady=5)
        sf = ScrollableFrame(welcome_frame)
        sf.pack(fill="both", expand=True, padx=20, pady=10)
        instructions = (
            "This tool assists emerging and growing companies in assessing the technical, manufacturing, and "
            "commercial maturity of a product or innovation.\n\n"
            "**New in Version 4:**\n"
            "• Dashboard with maturity heatmap and progress timeline\n"
            "• Prioritized recommendations and development roadmap\n"
            "• Excel and PDF export capabilities\n"
            "• Project comparison and benchmark analysis\n"
            "• Customizable settings and tooltips\n\n"
            "Workflow:\n"
            "- Complete the Project Profile\n"
            "- Select a level for each category\n"
            "- Review TRL / MRL / CRL and the blockers for the next level\n"
            "- Export results to JSON/CSV/Excel/PDF for tracking over time\n"
        )
        ttk.Label(sf.inner, text=instructions, wraplength=1050, justify="left", font=("Arial", 11)).pack(padx=10, pady=10, anchor="w")
        ttk.Button(welcome_frame, text="Start Assessment", command=lambda: self.notebook.select(1)).pack(pady=10)

    def create_profile_tab(self):
        profile_frame = ttk.Frame(self.notebook)
        self.notebook.add(profile_frame, text="Project Profile")
        ttk.Label(profile_frame, text="Company/Organization Name:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", padx=20, pady=10)
        self.company_var = tk.StringVar()
        ttk.Entry(profile_frame, textvariable=self.company_var, width=70).grid(row=0, column=1, padx=20, pady=10, sticky="w")
        ttk.Label(profile_frame, text="Project Title:", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", padx=20, pady=10)
        self.title_var = tk.StringVar()
        ttk.Entry(profile_frame, textvariable=self.title_var, width=70).grid(row=1, column=1, padx=20, pady=10, sticky="w")
        ttk.Label(profile_frame, text="Project Description:", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="nw", padx=20, pady=10)
        desc_container = ttk.Frame(profile_frame)
        desc_container.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        self.description_text = tk.Text(desc_container, width=70, height=10)
        self.description_text.pack()
        ttk.Button(profile_frame, text="Save Profile", command=self.save_profile).grid(row=3, column=1, pady=10, sticky="e")

    def create_assessment_tabs(self):
        for category_name, category_data in self.categories.items():
            category_frame = ttk.Frame(self.notebook)
            self.notebook.add(category_frame, text=category_name)
            ttk.Label(category_frame, text=category_name, font=("Arial", 16, "bold")).pack(pady=10)
            ttk.Label(category_frame, text=f"Axis: {category_data['type']}", font=("Arial", 11)).pack(pady=2)
            ttk.Label(category_frame, text="Select the option that best describes your current status:", font=("Arial", 11)).pack(pady=8)
            sf = ScrollableFrame(category_frame)
            sf.pack(fill="both", expand=True, padx=10, pady=10)
            var = self.selection_vars[category_name]
            for i, description in enumerate(category_data["levels"], start=1):
                level_frame = ttk.Frame(sf.inner)
                level_frame.pack(fill="x", padx=10, pady=6, anchor="w")
                ttk.Radiobutton(level_frame, variable=var, value=i, command=self.update_scores).pack(side="left")
                ttk.Label(level_frame, text=f"Level {i}: {description}", wraplength=1030, justify="left").pack(side="left", padx=10)

    def create_dashboard_tab(self):
        """NEW: Dashboard with visualizations."""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        sf = ScrollableFrame(dashboard_frame)
        sf.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Maturity Heatmap
        if HAS_MPL:
            heatmap_frame = ttk.LabelFrame(sf.inner, text="Category Maturity Heatmap")
            heatmap_frame.pack(fill="x", padx=5, pady=5)
            self.fig_heatmap = Figure(figsize=(10, 4))
            self.ax_heatmap = self.fig_heatmap.add_subplot(111)
            self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, heatmap_frame)
            self.canvas_heatmap.get_tk_widget().pack(fill="x", padx=10, pady=10)

        # 2. Progress Timeline (simulated)
        if HAS_MPL:
            timeline_frame = ttk.LabelFrame(sf.inner, text="Progress Timeline (Simulated)")
            timeline_frame.pack(fill="x", padx=5, pady=5)
            self.fig_timeline = Figure(figsize=(10, 3))
            self.ax_timeline = self.fig_timeline.add_subplot(111)
            self.canvas_timeline = FigureCanvasTkAgg(self.fig_timeline, timeline_frame)
            self.canvas_timeline.get_tk_widget().pack(fill="x", padx=10, pady=10)

        # 3. Benchmark Comparison
        benchmark_frame = ttk.LabelFrame(sf.inner, text="Industry Benchmark Comparison")
        benchmark_frame.pack(fill="x", padx=5, pady=5)
        self.benchmark_tree = ttk.Treeview(benchmark_frame, columns=("Stage", "TRL", "MRL", "CRL", "Your Gap"), show="headings", height=4)
        for col in ("Stage", "TRL", "MRL", "CRL", "Your Gap"):
            self.benchmark_tree.heading(col, text=col)
            self.benchmark_tree.column(col, width=120, anchor="center")
        self.benchmark_tree.pack(fill="x", padx=10, pady=10)

    def create_recommendations_tab(self):
        """NEW: Prioritized recommendations and roadmap."""
        rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(rec_frame, text="Recommendations")
        sf = ScrollableFrame(rec_frame)
        sf.pack(fill="both", expand=True)

        # Critical Gaps
        self.critical_gaps_frame = ttk.LabelFrame(sf.inner, text="🚨 Priority Action Items (Top 3)")
        self.critical_gaps_frame.pack(fill="x", padx=10, pady=10)
        self.critical_gaps_text = tk.Text(self.critical_gaps_frame, height=6, width=80, wrap="word", font=("Arial", 10))
        self.critical_gaps_text.pack(padx=10, pady=10)

        # Development Roadmap
        self.roadmap_frame = ttk.LabelFrame(sf.inner, text="📋 Development Roadmap")
        self.roadmap_frame.pack(fill="x", padx=10, pady=10)
        self.roadmap_text = tk.Text(self.roadmap_frame, height=8, width=80, wrap="word", font=("Arial", 10))
        self.roadmap_text.pack(padx=10, pady=10)

        # Resource Suggestions
        self.resources_frame = ttk.LabelFrame(sf.inner, text="🔗 Recommended Resources")
        self.resources_frame.pack(fill="x", padx=10, pady=10)
        self.resources_text = tk.Text(self.resources_frame, height=6, width=80, wrap="word", font=("Arial", 10))
        self.resources_text.pack(padx=10, pady=10)

    def create_summary_tab(self):
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Project Summary")
        ttk.Label(self.summary_frame, text="Market Readiness Assessment Results", font=("Arial", 20, "bold")).pack(pady=10)

        # Project info
        info_frame = ttk.LabelFrame(self.summary_frame, text="Project Information")
        info_frame.pack(fill="x", padx=20, pady=10)
        self.company_label = ttk.Label(info_frame, text="Company: ")
        self.company_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.project_label = ttk.Label(info_frame, text="Project: ")
        self.project_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.updated_label = ttk.Label(info_frame, text="Last updated: ")
        self.updated_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Scores
        scores_frame = ttk.LabelFrame(self.summary_frame, text="Readiness Levels")
        scores_frame.pack(fill="x", padx=20, pady=10)
        self.progress_vars: Dict[str, tk.IntVar] = {}
        self.score_labels: Dict[str, ttk.Label] = {}
        self._create_score_display(scores_frame, "TRL", max_value=9)
        self._create_score_display(scores_frame, "MRL", max_value=10)
        self._create_score_display(scores_frame, "CRL", max_value=9)

        # Next steps
        next_frame = ttk.LabelFrame(self.summary_frame, text="Next-Step Guidance (Blockers for Next Level)")
        next_frame.pack(fill="x", padx=20, pady=10)
        self.next_text_vars = {
            "TRL": tk.StringVar(value=""),
            "MRL": tk.StringVar(value=""),
            "CRL": tk.StringVar(value=""),
        }
        for i, axis in enumerate(["TRL", "MRL", "CRL"]):
            row = ttk.Frame(next_frame)
            row.pack(fill="x", padx=10, pady=6)
            ttk.Label(row, text=f"{axis} next step:", width=14, font=("Arial", 10, "bold")).pack(side="left", anchor="n")
            ttk.Label(row, textvariable=self.next_text_vars[axis], justify="left").pack(side="left", fill="x", expand=True)

        # Detailed selections
        details_frame = ttk.LabelFrame(self.summary_frame, text="Detailed Assessment")
        details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Category", "Selected Level", "Axis", "Description")
        self.results_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=9)
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Description":
                self.results_tree.column(col, width=720, anchor="w")
            else:
                self.results_tree.column(col, width=130, anchor="w")
        self.results_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Radar chart (optional)
        if HAS_MPL:
            chart_frame = ttk.LabelFrame(self.summary_frame, text="Category Maturity Profile (normalized)")
            chart_frame.pack(fill="both", expand=False, padx=20, pady=10)
            self.fig_radar = Figure(figsize=(7.5, 3.5), dpi=100)
            self.ax_radar = self.fig_radar.add_subplot(111, polar=True)
            self.canvas_radar = FigureCanvasTkAgg(self.fig_radar, master=chart_frame)
            self.canvas_radar.get_tk_widget().pack(fill="both", expand=True)

    def _create_score_display(self, parent, score_type: str, max_value: int):
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=6)
        ttk.Label(row, text=f"{score_type}:", font=("Arial", 12, "bold"), width=6).pack(side="left")
        self.progress_vars[score_type] = tk.IntVar(value=0)
        ttk.Progressbar(row, variable=self.progress_vars[score_type], maximum=max_value, length=350).pack(side="left", padx=10)
        self.score_labels[score_type] = ttk.Label(row, text=f"0/{max_value}", font=("Arial", 12, "bold"))
        self.score_labels[score_type].pack(side="left", padx=10)

    def create_help_tab(self):
        help_frame = ttk.Frame(self.notebook)
        self.notebook.add(help_frame, text="Help & Definitions")
        nb = ttk.Notebook(help_frame)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self._add_definition_tab(nb, "TRL Definitions", "TRL", self._get_trl_definitions())
        self._add_definition_tab(nb, "MRL Definitions", "MRL", self._get_mrl_definitions())
        self._add_definition_tab(nb, "CRL Definitions", "CRL", self._get_crl_definitions())

    def _add_definition_tab(self, nb: ttk.Notebook, tab_title: str, prefix: str, definitions: Dict[int, str]):
        frame = ttk.Frame(nb)
        nb.add(frame, text=tab_title)
        sf = ScrollableFrame(frame)
        sf.pack(fill="both", expand=True, padx=10, pady=10)
        for level in sorted(definitions.keys()):
            box = ttk.LabelFrame(sf.inner, text=f"{prefix} {level}")
            box.pack(fill="x", padx=10, pady=6)
            ttk.Label(box, text=definitions[level], wraplength=1050, justify="left").pack(padx=10, pady=10)

    # ------------------------------------------------------------------------
    # Scoring & display updates
    # ------------------------------------------------------------------------
    def _current_selections(self) -> Dict[str, int]:
        return {cat: var.get() for cat, var in self.selection_vars.items()}

    def update_scores(self):
        selections = self._current_selections()

        # Update category records
        self.current_project["categories"] = {}
        for cat, level in selections.items():
            self.current_project["categories"][cat] = {
                "level": int(level),
                "max_level": int(self.categories[cat]["max_level"]),
                "type": self.categories[cat]["type"],
                "description": self.categories[cat]["levels"][level - 1] if 1 <= level <= self.categories[cat]["max_level"] else "",
            }

        trl = self.scorer.score_from_rules(selections, self.scorer.TRL_RULES)
        mrl = self.scorer.score_from_rules(selections, self.scorer.MRL_RULES)
        crl = self.scorer.score_from_rules(selections, self.scorer.CRL_RULES)

        self.current_project["scores"]["TRL"] = trl
        self.current_project["scores"]["MRL"] = mrl
        self.current_project["scores"]["CRL"] = crl
        self.current_project["updated_at"] = datetime.now().isoformat(timespec="seconds")

        self._update_score_display()
        self._update_results_tree()
        self._update_next_steps(selections, trl, mrl, crl)
        self._update_dashboard(selections)       # NEW
        self._update_recommendations(selections) # NEW
        if HAS_MPL:
            self._update_radar_chart(selections)

    def _update_score_display(self):
        scores = self.current_project["scores"]
        max_map = {"TRL": 9, "MRL": 10, "CRL": 9}
        for axis in ["TRL", "MRL", "CRL"]:
            val = int(scores.get(axis, 0))
            self.progress_vars[axis].set(val)
            self.score_labels[axis].config(text=f"{val}/{max_map[axis]}")

        profile = self.current_project["profile"]
        self.company_label.config(text=f"Company: {profile.get('company_name','')}")
        self.project_label.config(text=f"Project: {profile.get('project_title','')}")
        self.updated_label.config(text=f"Last updated: {self.current_project.get('updated_at') or ''}")

    def _update_next_steps(self, selections: Dict[str, int], trl: int, mrl: int, crl: int):
        trl_next = self.scorer.next_step(selections, self.scorer.TRL_RULES, trl)
        self.next_text_vars["TRL"].set(
            f"Target TRL {trl_next.target_level}\n{trl_next.to_multiline_text()}" if trl_next else "At maximum TRL (9)."
        )
        mrl_next = self.scorer.next_step(selections, self.scorer.MRL_RULES, mrl)
        self.next_text_vars["MRL"].set(
            f"Target MRL {mrl_next.target_level}\n{mrl_next.to_multiline_text()}" if mrl_next else "At maximum MRL (10)."
        )
        crl_next = self.scorer.next_step(selections, self.scorer.CRL_RULES, crl)
        self.next_text_vars["CRL"].set(
            f"Target CRL {crl_next.target_level}\n{crl_next.to_multiline_text()}" if crl_next else "At maximum CRL (9)."
        )

    def _update_results_tree(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        for cat in self.categories.keys():
            data = self.current_project["categories"][cat]
            level = data["level"]
            desc = data["description"]
            self.results_tree.insert("", "end", values=(cat, f"Level {level}", data["type"], desc))

    def _update_dashboard(self, selections: Dict[str, int]):
        """Update all dashboard visualizations."""
        if HAS_MPL:
            self._update_heatmap(selections)
            self._update_timeline()
            self._update_benchmark_table()

    def _update_heatmap(self, selections: Dict[str, int]):
        """Create a heatmap (bar chart) of category maturity."""
        self.ax_heatmap.clear()
        categories = list(self.categories.keys())
        levels = [selections.get(cat, 0) for cat in categories]
        max_levels = [self.categories[cat]["max_level"] for cat in categories]
        normalized = [lvl/max_lvl if max_lvl else 0.0 for lvl, max_lvl in zip(levels, max_levels)]

        cmap = plt.cm.RdYlGn
        colors = cmap(normalized)
        bars = self.ax_heatmap.barh(categories, normalized, color=colors)
        self.ax_heatmap.set_xlim(0, 1)
        self.ax_heatmap.set_xlabel("Normalized Maturity")
        self.ax_heatmap.set_title("Category Maturity Heatmap")

        for bar, lvl, max_lvl in zip(bars, levels, max_levels):
            width = bar.get_width()
            self.ax_heatmap.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                                 f"{lvl}/{max_lvl}", va='center')

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 1))
        sm.set_array([])
        plt.colorbar(sm, ax=self.ax_heatmap, label="Maturity Level")
        self.canvas_heatmap.draw_idle()

    def _update_timeline(self):
        """Simulated progress timeline (replace with real historical data)."""
        self.ax_timeline.clear()
        dates = ["Jan", "Feb", "Mar", "Apr", "May"]
        trl_history = [3, 4, 5, 5, self.current_project["scores"]["TRL"]]
        mrl_history = [2, 3, 4, 4, self.current_project["scores"]["MRL"]]
        crl_history = [2, 3, 3, 4, self.current_project["scores"]["CRL"]]

        self.ax_timeline.plot(dates, trl_history, marker='o', label='TRL', linewidth=2)
        self.ax_timeline.plot(dates, mrl_history, marker='s', label='MRL', linewidth=2)
        self.ax_timeline.plot(dates, crl_history, marker='^', label='CRL', linewidth=2)
        self.ax_timeline.set_ylabel("Readiness Level")
        self.ax_timeline.set_title("Progress Timeline (Simulated Data)")
        self.ax_timeline.legend()
        self.ax_timeline.grid(True, alpha=0.3)
        self.canvas_timeline.draw_idle()

    def _update_benchmark_table(self):
        """Compare current scores with industry benchmarks."""
        for row in self.benchmark_tree.get_children():
            self.benchmark_tree.delete(row)

        benchmarks = {
            "Early Stage Startup": {"TRL": 4, "MRL": 3, "CRL": 3},
            "Growth Stage": {"TRL": 6, "MRL": 5, "CRL": 5},
            "Established Company": {"TRL": 8, "MRL": 7, "CRL": 7},
        }
        your_scores = self.current_project["scores"]

        for stage, scores in benchmarks.items():
            trl_gap = your_scores["TRL"] - scores["TRL"]
            mrl_gap = your_scores["MRL"] - scores["MRL"]
            crl_gap = your_scores["CRL"] - scores["CRL"]
            self.benchmark_tree.insert("", "end", values=(
                stage,
                scores["TRL"],
                scores["MRL"],
                scores["CRL"],
                f"TRL:{trl_gap:+d} MRL:{mrl_gap:+d} CRL:{crl_gap:+d}"
            ))

    def _update_recommendations(self, selections: Dict[str, int]):
        """Generate and display recommendations."""
        critical_gaps = self._identify_critical_gaps(selections)
        roadmap = self._generate_roadmap(selections)
        resources = self._get_recommended_resources()

        # Update critical gaps text
        self.critical_gaps_text.delete("1.0", tk.END)
        if critical_gaps:
            for gap in critical_gaps[:3]:
                self.critical_gaps_text.insert(tk.END,
                    f"• {gap['category']} (Axis: {gap['axis']}): Level {gap['current']} → {gap['required']} "
                    f"(Impact: {gap['impact']:.1f})\n")
        else:
            self.critical_gaps_text.insert(tk.END, "No critical gaps identified. All requirements are met.\n")

        # Update roadmap text
        self.roadmap_text.delete("1.0", tk.END)
        for step in roadmap:
            self.roadmap_text.insert(tk.END, f"• {step}\n")

        # Update resources text
        self.resources_text.delete("1.0", tk.END)
        for resource in resources:
            self.resources_text.insert(tk.END, f"• {resource}\n")

    def _identify_critical_gaps(self, selections: Dict[str, int]) -> List[Dict]:
        """Identify the most critical gaps for improvement."""
        gaps = []
        for axis in ["TRL", "MRL", "CRL"]:
            rules = getattr(self.scorer, f"{axis}_RULES")
            current = self.current_project["scores"][axis]
            for level in range(current + 1, min(10, max(rules.keys()) + 1)):
                req = rules.get(level, {})
                for cat, min_level in req.items():
                    cur = selections.get(cat, 0)
                    if cur < min_level:
                        severity = min_level - cur
                        impact = self._calculate_impact(cat, axis)
                        gaps.append({
                            "category": cat,
                            "axis": axis,
                            "gap": severity,
                            "impact": impact,
                            "required": min_level,
                            "current": cur
                        })
        gaps.sort(key=lambda x: (x["impact"], x["gap"]), reverse=True)
        return gaps

    def _calculate_impact(self, category: str, axis: str) -> float:
        """Calculate impact weight for a category (simplified)."""
        impact_weights = {
            "Technology": 1.0,
            "Product Development": 0.9,
            "Manufacturing Scale-up": 0.8,
            "Finance": 0.7,
            "Team": 0.6,
        }
        return impact_weights.get(category, 0.5)

    def _generate_roadmap(self, selections: Dict[str, int]) -> List[str]:
        """Generate a simple development roadmap."""
        roadmap = []
        scores = self.current_project["scores"]
        if scores["TRL"] < 9:
            roadmap.append(f"Achieve TRL {scores['TRL']+1} by addressing technology and product development gaps.")
        if scores["MRL"] < 10:
            roadmap.append(f"Advance to MRL {scores['MRL']+1} by improving manufacturing research and scale-up.")
        if scores["CRL"] < 9:
            roadmap.append(f"Reach CRL {scores['CRL']+1} by strengthening commercial, team, and financial readiness.")
        if not roadmap:
            roadmap.append("All readiness levels are at maximum. Focus on continuous improvement and scaling.")
        return roadmap

    def _get_recommended_resources(self) -> List[str]:
        """Return a list of recommended resources."""
        return [
            "NASA Technology Readiness Level Handbook (NASA‑SP‑20205011254)",
            "DoD Manufacturing Readiness Level Deskbook",
            "ESA TRL Calculator (trlcalculator.esa.int)",
            "MultiRATE Holistic Readiness Level Calculator (multirate.eu)",
            "RLCalc Readiness Level Calculator (rlcalc.com)",
        ]

    def _update_radar_chart(self, selections: Dict[str, int]):
        """Update the radar chart of category maturity."""
        labels = list(self.categories.keys())
        values = []
        for cat in labels:
            max_level = self.categories[cat]["max_level"]
            cur = selections.get(cat, 0)
            values.append((cur / max_level) if max_level else 0.0)

        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values2 = values + values[:1]
        angles2 = angles + angles[:1]

        self.ax_radar.clear()
        self.ax_radar.set_theta_offset(np.pi / 2)
        self.ax_radar.set_theta_direction(-1)
        self.ax_radar.plot(angles2, values2)
        self.ax_radar.fill(angles2, values2, alpha=0.2)
        self.ax_radar.set_xticks(angles)
        self.ax_radar.set_xticklabels(labels, fontsize=8)
        self.ax_radar.set_ylim(0, 1.0)
        self.ax_radar.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        self.ax_radar.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
        self.ax_radar.set_title("Normalized maturity by category (current/max)", fontsize=10)
        self.canvas_radar.draw_idle()

    # ------------------------------------------------------------------------
    # Profile & persistence
    # ------------------------------------------------------------------------
    def save_profile(self):
        self.current_project["profile"]["company_name"] = self.company_var.get().strip()
        self.current_project["profile"]["project_title"] = self.title_var.get().strip()
        self.current_project["profile"]["project_description"] = self.description_text.get("1.0", tk.END).strip()
        self.update_scores()
        messagebox.showinfo("Saved", "Project profile saved.")

    def reset_assessment(self):
        if not messagebox.askyesno("Confirm", "Reset all selections and project information?"):
            return
        self.company_var.set("")
        self.title_var.set("")
        self.description_text.delete("1.0", tk.END)
        for cat, var in self.selection_vars.items():
            var.set(1)
        self.current_project["profile"] = {"company_name": "", "project_title": "", "project_description": ""}
        self.update_scores()
        self.notebook.select(0)

    def export_to_json(self):
        if not self.current_project["profile"]["company_name"] and not self.current_project["profile"]["project_title"]:
            if not messagebox.askyesno("Profile not set", "Profile is empty. Export anyway?"):
                return
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"TRL_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        if not filename:
            return
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.current_project, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exported", f"Assessment exported to:\n{filename}")

    def load_from_json(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load JSON:\n{e}")
            return
        profile = data.get("profile", {})
        self.company_var.set(profile.get("company_name", ""))
        self.title_var.set(profile.get("project_title", ""))
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", profile.get("project_description", ""))
        cats = data.get("categories", {})
        for cat, rec in cats.items():
            if cat in self.selection_vars:
                lvl = int(rec.get("level", 1))
                max_lvl = int(self.categories[cat]["max_level"])
                self.selection_vars[cat].set(min(max(lvl, 1), max_lvl))
        self.current_project["profile"] = {
            "company_name": self.company_var.get().strip(),
            "project_title": self.title_var.get().strip(),
            "project_description": self.description_text.get("1.0", tk.END).strip(),
        }
        self.update_scores()
        messagebox.showinfo("Loaded", f"Loaded assessment:\n{filename}")

    def export_to_csv(self):
        if not self.current_project["profile"]["company_name"] and not self.current_project["profile"]["project_title"]:
            if not messagebox.askyesno("Profile not set", "Profile is empty. Export anyway?"):
                return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"TRL_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Company", self.current_project["profile"].get("company_name", "")])
            w.writerow(["Project", self.current_project["profile"].get("project_title", "")])
            w.writerow(["Updated at", self.current_project.get("updated_at", "")])
            w.writerow([])
            w.writerow(["Score Type", "Value"])
            for axis in ["TRL", "MRL", "CRL"]:
                w.writerow([axis, self.current_project["scores"].get(axis, 0)])
            w.writerow([])
            w.writerow(["Category", "Axis", "Selected Level", "Max Level", "Description"])
            for cat in self.categories.keys():
                rec = self.current_project["categories"][cat]
                w.writerow([cat, rec["type"], rec["level"], rec["max_level"], rec["description"]])
        messagebox.showinfo("Exported", f"CSV exported to:\n{filename}")

    def export_to_excel(self):
        """Export assessment to a formatted Excel workbook."""
        if not HAS_PANDAS:
            messagebox.showerror("Error", "Pandas library required for Excel export.")
            return
        if not self.current_project["profile"]["company_name"] and not self.current_project["profile"]["project_title"]:
            if not messagebox.askyesno("Profile not set", "Profile is empty. Export anyway?"):
                return
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"TRL_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )
        if not filename:
            return

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Profile sheet
                profile_df = pd.DataFrame([
                    ["Company", self.current_project["profile"].get("company_name", "")],
                    ["Project", self.current_project["profile"].get("project_title", "")],
                    ["Description", self.current_project["profile"].get("project_description", "")],
                    ["Updated at", self.current_project.get("updated_at", "")]
                ])
                profile_df.to_excel(writer, sheet_name='Profile', index=False, header=False)

                # Scores sheet
                scores_df = pd.DataFrame([
                    ["TRL", self.current_project["scores"]["TRL"], 9],
                    ["MRL", self.current_project["scores"]["MRL"], 10],
                    ["CRL", self.current_project["scores"]["CRL"], 9]
                ], columns=["Axis", "Score", "Max"])
                scores_df.to_excel(writer, sheet_name='Scores', index=False)

                # Details sheet
                details_data = []
                for cat in self.categories.keys():
                    rec = self.current_project["categories"][cat]
                    details_data.append([cat, rec["type"], rec["level"], rec["max_level"], rec["description"]])
                details_df = pd.DataFrame(details_data, columns=["Category", "Axis", "Selected Level", "Max Level", "Description"])
                details_df.to_excel(writer, sheet_name='Details', index=False)

                # Next steps sheet
                next_steps = []
                for axis in ["TRL", "MRL", "CRL"]:
                    next_steps.append([axis, self.next_text_vars[axis].get()])
                next_df = pd.DataFrame(next_steps, columns=["Axis", "Next Step Guidance"])
                next_df.to_excel(writer, sheet_name='Next Steps', index=False)

            messagebox.showinfo("Exported", f"Excel workbook exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export Excel: {e}")

    def export_to_pdf(self):
        """Export a professional PDF report."""
        if not HAS_REPORTLAB:
            messagebox.showerror("Error", "ReportLab library required for PDF export.")
            return
        if not self.current_project["profile"]["company_name"] and not self.current_project["profile"]["project_title"]:
            if not messagebox.askyesno("Profile not set", "Profile is empty. Export anyway?"):
                return
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"TRL_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        )
        if not filename:
            return

        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            story.append(Paragraph("Technology Readiness Assessment Report", styles['Title']))
            story.append(Paragraph("<br/><br/>", styles['Normal']))

            # Project Information
            profile = self.current_project["profile"]
            story.append(Paragraph("Project Information", styles['Heading2']))
            story.append(Paragraph(f"<b>Company:</b> {profile.get('company_name', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Project:</b> {profile.get('project_title', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Description:</b> {profile.get('project_description', 'N/A')}", styles['Normal']))
            story.append(Paragraph(f"<b>Assessment Date:</b> {self.current_project.get('updated_at', 'N/A')}", styles['Normal']))
            story.append(Paragraph("<br/><br/>", styles['Normal']))

            # Scores
            story.append(Paragraph("Readiness Scores", styles['Heading2']))
            scores = self.current_project["scores"]
            score_table = [
                ["Metric", "Score", "Max", "Percentage"],
                ["TRL", scores["TRL"], 9, f"{scores['TRL']/9*100:.1f}%"],
                ["MRL", scores["MRL"], 10, f"{scores['MRL']/10*100:.1f}%"],
                ["CRL", scores["CRL"], 9, f"{scores['CRL']/9*100:.1f}%"],
            ]
            t = Table(score_table)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(t)
            story.append(Paragraph("<br/><br/>", styles['Normal']))

            # Next Steps
            story.append(Paragraph("Next-Step Guidance", styles['Heading2']))
            for axis in ["TRL", "MRL", "CRL"]:
                story.append(Paragraph(f"<b>{axis}:</b>", styles['Normal']))
                story.append(Paragraph(self.next_text_vars[axis].get().replace("\n", "<br/>"), styles['Normal']))
                story.append(Paragraph("<br/>", styles['Normal']))

            doc.build(story)
            messagebox.showinfo("Exported", f"PDF report exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

    # ------------------------------------------------------------------------
    # Additional tools (stubs for future expansion)
    # ------------------------------------------------------------------------
    def open_comparison_tool(self):
        messagebox.showinfo("Info", "Project comparison tool is under development.")

    def generate_roadmap(self):
        selections = self._current_selections()
        roadmap = self._generate_roadmap(selections)
        roadmap_text = "\n".join([f"• {step}" for step in roadmap])
        messagebox.showinfo("Development Roadmap", roadmap_text)

    def open_settings(self):
        messagebox.showinfo("Info", "Settings dialog is under development.")

    # ------------------------------------------------------------------------
    # Definitions (unchanged)
    # ------------------------------------------------------------------------
    def _get_trl_definitions(self) -> Dict[int, str]:
        return {
            1: "Lowest level of technology readiness. Scientific research begins to be translated into applied research and development.",
            2: "Practical applications are invented. Research and development is initiated.",
            3: "Active research and development is initiated. Includes analytical and laboratory studies to validate physical predictions or concept feasibility.",
            4: "Basic technological components are integrated and tested in a laboratory environment. Prototype development begins.",
            5: "A laboratory-scale integrated product/system demonstrates performance in the intended application(s).",
            6: "A pilot-scale integrated product/system demonstrates performance in the intended application(s).",
            7: "A full-scale prototype has been demonstrated in the intended application(s).",
            8: "Actual system has been proven to work in its near-final form under a representative set of expected conditions and environments.",
            9: "Product/system is in its final form, under the full range of operating conditions.",
        }

    def _get_mrl_definitions(self) -> Dict[int, str]:
        return {
            1: "Lowest level of manufacturing readiness. The focus is to add manufacturing considerations to the overall technology development.",
            2: "Manufacturing concepts are identified; manufacturing proof of concept begins.",
            3: "Manufacturing proof of concept is developed. This includes studies and experiments that help define manufacturing processes and methods.",
            4: "Capability to produce the technology in a laboratory environment. The maturity of the manufacturing processes, materials, and tooling are still relatively low.",
            5: "Capability to produce prototype components in a production relevant environment. Manufacturing processes and tooling have been demonstrated to produce prototype components.",
            6: "Capability to produce a prototype system or subsystem in a production relevant environment. Initial manufacturing process capabilities are established.",
            7: "Capability to produce systems, subsystems, or components in a production representative environment. Manufacturing processes and procedures are in development and/or validated.",
            8: "Pilot line capability demonstrated; ready to begin low rate production.",
            9: "Low rate production demonstrated; capability in place to begin full rate production.",
            10: "Full rate production demonstrated. Lean practices and continuous improvement are in place; manufacturing resources are available to meet planned full rate production schedules.",
        }

    def _get_crl_definitions(self) -> Dict[int, str]:
        return {
            1: "Lowest level of commercialization readiness. Knowledge of applications is limited.",
            2: "Product ideas exist but are speculative; initial market research is mainly secondary; early team formation begins.",
            3: "Initial product hypothesis defined; customer discovery underway; improved understanding of competition; advisors/mentors engaged.",
            4: "Value proposition clarified; product requirements aligned to customer needs; early partnerships/value-chain relationships; financing planning initiated.",
            5: "Strong competitive positioning; partnerships forming; pilot production or early sales activity; private investment raised or near-ready.",
            6: "Commercial model more complete; supply chain and partnerships maturing; purchase orders or equivalent commitments begin.",
            7: "Scaling through established supply agreements; broader market presence and repeatable sales motion developing.",
            8: "Widespread market entry and growth execution; organization adapts to market dynamics.",
            9: "Widespread deployment is achieved.",
        }

# ============================================================================
# Main entry point
# ============================================================================

def main():
    root = tk.Tk()
    app = TRLAssessmentAppV4(root)
    root.mainloop()

if __name__ == "__main__":
    main()