"""
Report Generator for TITAN
"""
import os
from datetime import datetime

class ReportGenerator:
    def __init__(self):
        self.report_dir = "src/reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def generate_incident_report(self, disaster_data, affected_nodes, chat_history):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.report_dir}/Incident_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(f"# 🚨 TITAN Incident Report\n")
            f.write(f"**Date:** {datetime.now()}\n\n")
            f.write(f"## Incident Details\n")
            f.write(f"- **Type:** {disaster_data.get('type')}\n")
            f.write(f"- **Location:** {disaster_data.get('lat')}, {disaster_data.get('lon')}\n\n")
            
            f.write(f"## Impact Assessment\n")
            f.write(f"- **Facilities Affected:** {len(affected_nodes)}\n")
            for node in affected_nodes[:10]:
                f.write(f"  - {node.get('name')} ({node.get('type')})\n")
                
        return filename