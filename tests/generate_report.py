#!/usr/bin/env python3
"""Generate detailed test report from pytest results."""

import argparse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

def parse_coverage(coverage_xml):
    """Parse coverage data from coverage.xml."""
    tree = ET.parse(coverage_xml)
    root = tree.getroot()
    
    coverage_data = {
        'line': float(root.get('line-rate', 0)) * 100,
        'branch': float(root.get('branch-rate', 0)) * 100,
        'complexity': float(root.get('complexity', 0)),
        'packages': []
    }
    
    for package in root.findall('.//package'):
        pkg_data = {
            'name': package.get('name'),
            'line_rate': float(package.get('line-rate', 0)) * 100,
            'branch_rate': float(package.get('branch-rate', 0)) * 100,
            'classes': []
        }
        
        for class_ in package.findall('.//class'):
            class_data = {
                'name': class_.get('name'),
                'line_rate': float(class_.get('line-rate', 0)) * 100,
                'branch_rate': float(class_.get('branch-rate', 0)) * 100,
                'complexity': float(class_.get('complexity', 0))
            }
            pkg_data['classes'].append(class_data)
        
        coverage_data['packages'].append(pkg_data)
    
    return coverage_data

def parse_test_results(results_json):
    """Parse test results from pytest JSON report."""
    with open(results_json) as f:
        data = json.load(f)
    
    test_data = {
        'total': data['summary'].get('total', 0),
        'passed': data['summary'].get('passed', 0),
        'failed': data['summary'].get('failed', 0),
        'skipped': data['summary'].get('skipped', 0),
        'duration': data['summary'].get('duration', 0),
        'categories': {
            'ui': {'passed': 0, 'failed': 0, 'skipped': 0, 'details': []},
            'media': {'passed': 0, 'failed': 0, 'skipped': 0, 'details': []},
            'translation': {'passed': 0, 'failed': 0, 'skipped': 0, 'details': []},
            'worker': {'passed': 0, 'failed': 0, 'skipped': 0, 'details': []},
            'integration': {'passed': 0, 'failed': 0, 'skipped': 0, 'details': []}
        }
    }
    
    for test in data['tests']:
        # Determine test category
        markers = test.get('metadata', {}).get('markers', [])
        category = 'integration'  # default category
        for marker in markers:
            if marker in test_data['categories']:
                category = marker
                break
        
        # Update category stats
        outcome = test['outcome']
        if outcome == 'passed':
            test_data['categories'][category]['passed'] += 1
        elif outcome == 'failed':
            test_data['categories'][category]['failed'] += 1
        elif outcome == 'skipped':
            test_data['categories'][category]['skipped'] += 1
        
        # Add test details
        test_data['categories'][category]['details'].append({
            'name': test['nodeid'],
            'outcome': outcome,
            'duration': test.get('duration', 0),
            'error': test.get('call', {}).get('longrepr', '') if outcome == 'failed' else None
        })
    
    return test_data

def generate_html_report(template_path, test_data, coverage_data, output_path):
    """Generate HTML report using template."""
    with open(template_path) as f:
        template = f.read()
    
    # Replace placeholders with actual data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    template = template.replace(
        'document.getElementById(\'timestamp\').textContent = new Date().toLocaleString();',
        f'document.getElementById(\'timestamp\').textContent = "{timestamp}";'
    )
    
    # Update test summary
    summary_script = f"""
        document.getElementById('total-tests').textContent = '{test_data["total"]}';
        document.getElementById('passed-tests').textContent = '{test_data["passed"]}';
        document.getElementById('failed-tests').textContent = '{test_data["failed"]}';
        document.getElementById('skipped-tests').textContent = '{test_data["skipped"]}';
    """
    
    # Update coverage data
    coverage_script = f"""
        document.getElementById('line-coverage').style.width = '{coverage_data["line"]}%';
        document.getElementById('line-coverage-text').textContent = '{coverage_data["line"]:.1f}%';
        document.getElementById('branch-coverage').style.width = '{coverage_data["branch"]}%';
        document.getElementById('branch-coverage-text').textContent = '{coverage_data["branch"]:.1f}%';
    """
    
    # Generate test details for each category
    for category, data in test_data['categories'].items():
        details_html = []
        for test in data['details']:
            status_class = 'passed' if test['outcome'] == 'passed' else 'failed' if test['outcome'] == 'failed' else 'skipped'
            details_html.append(f"""
                <div class="test-details {status_class}">
                    <p><strong>{test['name']}</strong> ({test['duration']:.2f}s)</p>
                    {f'<pre><code>{test["error"]}</code></pre>' if test['error'] else ''}
                </div>
            """)
        
        category_script = f"""
            document.getElementById('{category}-tests').innerHTML = `
                <p>Passed: {data['passed']}, Failed: {data['failed']}, Skipped: {data['skipped']}</p>
                {''.join(details_html)}
            `;
        """
        summary_script += category_script
    
    # Insert all scripts
    template = template.replace(
        '// This will be replaced with actual test data by the CI/CD pipeline',
        summary_script + coverage_script
    )
    
    # Write output
    with open(output_path, 'w') as f:
        f.write(template)

def main():
    parser = argparse.ArgumentParser(description='Generate test report from pytest results')
    parser.add_argument('--test-results', required=True, help='Path to pytest JSON results file')
    parser.add_argument('--coverage-xml', required=True, help='Path to coverage XML file')
    parser.add_argument('--template', required=True, help='Path to HTML template file')
    parser.add_argument('--output', required=True, help='Output path for generated report')
    
    args = parser.parse_args()
    
    coverage_data = parse_coverage(args.coverage_xml)
    test_data = parse_test_results(args.test_results)
    generate_html_report(args.template, test_data, coverage_data, args.output)

if __name__ == '__main__':
    main()
