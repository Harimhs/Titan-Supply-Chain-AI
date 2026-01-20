from fpdf import FPDF
from datetime import datetime
import os

# Import Neo4j Client directly to be safe and independent
from src.graph.neo4j_client import Neo4jClient

class TitanReportGenerator:
    def __init__(self):
        self.pdf = FPDF()
        self.db = Neo4jClient()
        
    def generate_report(self):
        # 1. Fetch Live Data
        stats_query = """
            MATCH (n) WHERE n:Factory OR n:Warehouse OR n:Port
            RETURN 
                count(n) as total,
                sum(CASE WHEN n:Factory THEN 1 ELSE 0 END) as factories,
                sum(CASE WHEN n:Warehouse THEN 1 ELSE 0 END) as warehouses,
                sum(CASE WHEN n:Port THEN 1 ELSE 0 END) as ports,
                sum(CASE WHEN n.status = 'Disrupted' THEN 1 ELSE 0 END) as disrupted
        """
        # Run query and handle empty DB case safely
        stats_result = self.db.run_query(stats_query)
        if not stats_result:
            stats = {'total': 0, 'factories': 0, 'warehouses': 0, 'ports': 0, 'disrupted': 0}
        else:
            stats = stats_result[0]
        
        disasters = self.db.run_query("MATCH (d:Disaster {status: 'Active'}) RETURN d.type as type, d.lat as lat, d.lon as lon")
        
        # 2. Setup PDF
        self.pdf.add_page()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        self.pdf.set_fill_color(10, 14, 26) # Dark Blue
        self.pdf.rect(0, 0, 210, 40, 'F')
        self.pdf.set_font("Arial", "B", 24)
        self.pdf.set_text_color(0, 212, 255) # Cyan
        self.pdf.cell(0, 20, "TITAN INTELLIGENCE REPORT", ln=True, align='C')
        
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.set_text_color(200, 200, 200)
        self.pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        self.pdf.ln(20)

        # Section 1: Executive Summary
        self.section_title("1. NETWORK STATUS")
        self.kpi_row("Total Facilities", stats['total'])
        self.kpi_row("Operational", stats['total'] - stats['disrupted'])
        self.kpi_row("Critical Failures", stats['disrupted'], is_alert=stats['disrupted'] > 0)
        self.pdf.ln(5)

        # Section 2: Asset Breakdown
        self.section_title("2. ASSET BREAKDOWN")
        self.body_text(f"Factories: {stats['factories']}")
        self.body_text(f"Warehouses: {stats['warehouses']}")
        self.body_text(f"Ports: {stats['ports']}")
        self.pdf.ln(5)

        # Section 3: Active Threats
        self.section_title("3. ACTIVE THREAT MONITORING")
        if disasters:
            for d in disasters:
                # FIXED: Removed '⚠' symbol, used '[!]' instead
                self.alert_text(f"[!] {d['type']} detected at [{d['lat']}, {d['lon']}]")
        else:
            self.body_text("No active major threats detected.")
        self.pdf.ln(5)

        # Section 4: Automated Recommendations
        self.section_title("4. AI RECOMMENDATIONS")
        if stats['disrupted'] > 0:
            # FIXED: Removed '•' symbol, used '-' instead
            self.body_text("- Rerouting protocols have been initialized for disrupted nodes.")
            self.body_text("- Recommended Action: Activate contingency suppliers in neighboring regions.")
            self.body_text("- Risk Level: HIGH - Immediate attention required.")
        else:
            self.body_text("- System operating at nominal capacity.")
            self.body_text("- Recommended Action: Continue routine monitoring.")
            self.body_text("- Risk Level: LOW.")

        # Ensure directory exists
        if not os.path.exists("static"):
            os.makedirs("static")

        # Save
        output_path = "static/TITAN_Report.pdf"
        self.pdf.output(output_path)
        return output_path

    def section_title(self, text):
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.set_text_color(10, 14, 26)
        self.pdf.cell(0, 10, text, ln=True)
        self.pdf.line(10, self.pdf.get_y(), 200, self.pdf.get_y())
        self.pdf.ln(5)

    def body_text(self, text):
        self.pdf.set_font("Arial", "", 11)
        self.pdf.set_text_color(50, 50, 50)
        self.pdf.multi_cell(0, 8, text)

    def alert_text(self, text):
        self.pdf.set_font("Arial", "B", 11)
        self.pdf.set_text_color(220, 50, 50) # Red
        self.pdf.multi_cell(0, 8, text)

    def kpi_row(self, label, value, is_alert=False):
        self.pdf.set_font("Arial", "", 12)
        self.pdf.set_text_color(50, 50, 50)
        self.pdf.cell(100, 10, label)
        
        self.pdf.set_font("Arial", "B", 12)
        if is_alert:
            self.pdf.set_text_color(220, 50, 50)
        else:
            self.pdf.set_text_color(0, 150, 100)
        self.pdf.cell(0, 10, str(value), ln=True)