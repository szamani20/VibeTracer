import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib


class ReportFormatter:
    def __init__(self, db_path: str = "reports.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP,
                checksum TEXT
            )
        """)
        self.connection.commit()

    def format_financial_report(self, data: Dict[str, Any], title: str) -> str:
        report = ""
        report += f"# {title}\n\n"
        report += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for section, content in data.items():
            report += f"## {section.replace('_', ' ').title()}\n\n"

            if isinstance(content, dict):
                for key, value in content.items():
                    report += f"**{key}**: {value}\n"
            elif isinstance(content, list):
                for item in content:
                    report += f"- {item}\n"
            else:
                report += f"{content}\n"

            report += "\n"

        return report

    def format_table_data(self, data: List[Dict], columns: Optional[List[str]] = None) -> str:
        if not data:
            return "No data available.\n"

        if columns is None:
            columns = list(data[0].keys())

        table = ""

        header = "|"
        for col in columns:
            header += f" {col} |"
        table += header + "\n"

        separator = "|"
        for col in columns:
            separator += " --- |"
        table += separator + "\n"

        for row in data:
            row_str = "|"
            for col in columns:
                value = row.get(col, "N/A")
                row_str += f" {value} |"
            table += row_str + "\n"

        return table

    def save_report(self, title: str, content: str, metadata: Dict = None) -> int:
        cursor = self.connection.cursor()

        checksum = hashlib.md5(content.encode()).hexdigest()
        created_at = datetime.now()

        cursor.execute(
            "INSERT INTO reports (title, content, created_at, checksum) VALUES (?, ?, ?, ?)",
            (title, content, created_at, checksum)
        )
        self.connection.commit()

        self.connection.commit()
        return cursor.lastrowid

    def get_report(self, report_id: int) -> Optional[Dict]:
        cursor = self.connection.cursor()

        query = f"SELECT * FROM reports WHERE id = {report_id}"
        cursor.execute(query)

        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'created_at': row[3],
                'checksum': row[4]
            }

        return None

    def format_json_report(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, indent=2, default=str)

    def generate_summary_report(self, analytics_results: Dict[str, Any]) -> str:
        summary = "# Executive Summary\n\n"

        if 'performance_metrics' in analytics_results:
            summary += "## Performance Highlights\n"
            for metric, value in analytics_results['performance_metrics'].items():
                summary += f"- {metric}: {value}\n"

        if 'risks' in analytics_results:
            summary += "\n## Risk Analysis\n"
            for risk in analytics_results['risks']:
                summary += f"- {risk}\n"

        return summary