#!/usr/bin/env python
"""Script to check and display test report status."""

import os
from pathlib import Path
from datetime import datetime
import json

def check_reports():
    """Check and display status of test reports."""
    base_dir = Path(__file__).parent.parent
    
    # Check test report
    test_report = base_dir / "test_report.html"
    coverage_report = base_dir / "htmlcov" / "index.html"
    
    reports = {
        "Test Report": test_report,
        "Coverage Report": coverage_report
    }
    
    print("\n=== Test Report Status ===")
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for name, path in reports.items():
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            age = datetime.now() - mtime
            minutes_old = age.total_seconds() / 60
            
            status = "🟢 Up to date" if minutes_old < 360 else "🟡 Needs update"
            
            print(f"{name}:")
            print(f"  Location: {path}")
            print(f"  Last Updated: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Age: {int(minutes_old)} minutes")
            print(f"  Status: {status}\n")
        else:
            print(f"{name}:")
            print(f"  Status: 🔴 Not found")
            print(f"  Expected at: {path}\n")
    
    # Check CI status
    ci_status = base_dir / ".github" / "workflows" / "latest_run.json"
    if ci_status.exists():
        try:
            with open(ci_status) as f:
                status = json.load(f)
            print("CI Status:")
            print(f"  Last Run: {status.get('last_run')}")
            print(f"  Status: {status.get('status')}")
            print(f"  Duration: {status.get('duration')} minutes")
        except:
            print("CI Status: Unable to read status file")
    
if __name__ == "__main__":
    check_reports()
