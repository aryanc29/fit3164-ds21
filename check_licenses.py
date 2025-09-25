#!/usr/bin/env python3
"""
Simple license scanner using scancode-toolkit
Runs scancode as a subprocess and generates license reports
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import argparse
import scancode-toolkit  # Ensure scancode-toolkit is installed

def find_scancode_executable():
    """Find the scancode executable in various possible locations"""
    
    # Try common command variations
    commands_to_try = [
        ['scancode', '--version'],
        ['python', '-m', 'scancode', '--version'],
        ['py', '-m', 'scancode', '--version']
    ]
    
    for cmd in commands_to_try:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return cmd[:-1]  # Remove --version from the command
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    # Try to find scancode.exe in Python Scripts directory
    try:
        import site
        for site_dir in site.getsitepackages():
            scripts_dir = Path(site_dir).parent / "Scripts"
            scancode_exe = scripts_dir / "scancode.exe"
            if scancode_exe.exists():
                return [str(scancode_exe)]
    except:
        pass
    
    return None

def run_license_scan(target_path=".", output_dir="scan_reports", include_copyrights=True):
    """Run scancode license scan on the target path"""
    
    print(f"🔍 Scanning {os.path.abspath(target_path)} for license information...")
    
    # Find scancode command
    scancode_cmd = find_scancode_executable()
    if not scancode_cmd:
        print("❌ Error: scancode command not found.")
        print("Make sure scancode-toolkit is installed: pip install scancode-toolkit")
        return False
    
    print(f"✅ Found scancode: {' '.join(scancode_cmd)}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate output filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_path / f"license_scan_{timestamp}.json"
    html_file = output_path / f"license_scan_{timestamp}.html"
    
    # Build scancode command arguments
    scan_args = scancode_cmd + [
        '--license',              # Detect licenses
        '--info',                # Basic file info
        '--strip-root',          # Remove root path from results
        '--json-pp', str(json_file),  # Pretty-printed JSON output
        target_path
    ]
    
    if include_copyrights:
        scan_args.insert(-1, '--copyright')  # Insert before target_path
    
    print(f"🚀 Running: {' '.join(scan_args)}")
    print("⏳ This may take a few minutes for large repositories...")
    
    try:
        # Run scancode
        result = subprocess.run(scan_args, capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode != 0:
            print(f"❌ Scancode failed with return code {result.returncode}")
            print("STDERR:", result.stderr)
            return False
            
        print("✅ JSON report generated successfully!")
        
        # Try to generate HTML report as well
        html_args = scancode_cmd + [
            '--license',
            '--info',
            '--strip-root',
            '--html', str(html_file),
            target_path
        ]
        
        if include_copyrights:
            html_args.insert(-1, '--copyright')
        
        print("📄 Generating HTML report...")
        html_result = subprocess.run(html_args, capture_output=True, text=True, timeout=600)
        
        if html_result.returncode == 0:
            print("✅ HTML report generated successfully!")
        else:
            print("⚠️  HTML report generation failed, but JSON report is available")
        
    except subprocess.TimeoutExpired:
        print("❌ Scancode timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running scancode: {e}")
        return False
    
    # Analyze and summarize results
    if json_file.exists():
        analyze_results(json_file, output_path, timestamp)
    
    print(f"\n🎉 Scan complete! Reports saved in: {output_path.absolute()}")
    print(f"📊 JSON Report: {json_file.name}")
    if html_file.exists():
        print(f"🌐 HTML Report: {html_file.name}")
    
    return True

def analyze_results(json_file, output_dir, timestamp):
    """Analyze scancode results and create a summary"""
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summary_file = output_dir / f"license_summary_{timestamp}.txt"
        
        # Extract file information
        files = data.get('files', [])
        total_files = len([f for f in files if f.get('type') == 'file'])
        
        # Analyze licenses
        license_counts = {}
        files_with_licenses = []
        files_without_licenses = []
        
        for file_info in files:
            if file_info.get('type') != 'file':
                continue
                
            file_path = file_info.get('path', '')
            licenses = file_info.get('licenses', [])
            
            if licenses:
                files_with_licenses.append(file_path)
                for license_info in licenses:
                    license_key = license_info.get('key', 'unknown')
                    license_name = license_info.get('name', 'Unknown')
                    
                    if license_key not in license_counts:
                        license_counts[license_key] = {
                            'name': license_name,
                            'count': 0,
                            'files': []
                        }
                    
                    license_counts[license_key]['count'] += 1
                    license_counts[license_key]['files'].append(file_path)
            else:
                files_without_licenses.append(file_path)
        
        # Generate summary report
        summary = []
        summary.append("License Scan Summary")
        summary.append("===================")
        summary.append(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"Total Files Scanned: {total_files}")
        summary.append(f"Files with License Info: {len(files_with_licenses)}")
        summary.append(f"Files without License Info: {len(files_without_licenses)}")
        summary.append("")
        
        if license_counts:
            summary.append("Licenses Found:")
            summary.append("===============")
            for license_key, info in sorted(license_counts.items()):
                summary.append(f"\n{info['name']} ({license_key}): {info['count']} files")
                # Show a few example files
                for file_path in info['files'][:3]:
                    summary.append(f"  - {file_path}")
                if len(info['files']) > 3:
                    summary.append(f"  ... and {len(info['files']) - 3} more files")
        else:
            summary.append("No licenses detected in scanned files.")
        
        summary.append(f"\nFiles without license information ({len(files_without_licenses)}):")
        summary.append("=" * 50)
        for file_path in files_without_licenses[:20]:  # Show first 20
            summary.append(f"  - {file_path}")
        if len(files_without_licenses) > 20:
            summary.append(f"  ... and {len(files_without_licenses) - 20} more files")
        
        # Save summary
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary))
        
        # Print key stats to console
        print(f"\n📊 Scan Results:")
        print(f"   Total files: {total_files}")
        print(f"   Files with licenses: {len(files_with_licenses)}")
        print(f"   Files without licenses: {len(files_without_licenses)}")
        
        if license_counts:
            print("   Licenses found:")
            for license_key, info in sorted(license_counts.items()):
                print(f"     - {info['name']}: {info['count']} files")
        
        print(f"📋 Detailed summary: {summary_file.name}")
        
    except Exception as e:
        print(f"⚠️  Could not analyze results: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scan repository for license information using scancode-toolkit")
    parser.add_argument("--path", "-p", default=".", help="Path to scan (default: current directory)")
    parser.add_argument("--output", "-o", default="scan_reports", help="Output directory for reports")
    parser.add_argument("--no-copyright", action="store_true", help="Skip copyright detection (faster)")
    
    args = parser.parse_args()
    
    success = run_license_scan(
        target_path=args.path,
        output_dir=args.output,
        include_copyrights=not args.no_copyright
    )
    
    if success:
        print("\n✅ License scan completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ License scan failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()