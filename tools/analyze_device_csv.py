#!/usr/bin/env python3
"""
Utility to analyze device discovery CSV files and provide online/offline statistics.
Can also filter CSVs to create online-only versions.
"""

import csv
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path


def parse_timestamp(timestamp_str):
    """Parse ISO format timestamp."""
    if not timestamp_str:
        return None
    try:
        if timestamp_str.endswith('Z'):
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return datetime.fromisoformat(timestamp_str)
    except:
        return None


def calculate_online_status(last_seen_str, threshold_minutes=30):
    """Calculate if device is online based on last_seen."""
    last_seen = parse_timestamp(last_seen_str)
    if not last_seen:
        return "Unknown", -1
    
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    time_diff = now - last_seen
    minutes_since = int(time_diff.total_seconds() / 60)
    
    if minutes_since <= threshold_minutes:
        return "Online", minutes_since
    return "Offline", minutes_since


def analyze_csv(filepath, threshold_minutes=30):
    """Analyze a device CSV file."""
    stats = {
        'total': 0,
        'online': 0,
        'offline': 0,
        'unknown': 0,
        'by_cid': {},
        'by_os': {}
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            stats['total'] += 1
            
            # Check if online_status already exists
            if 'online_status' in row and row['online_status']:
                status = row['online_status']
            else:
                # Calculate from last_seen
                status, _ = calculate_online_status(row.get('last_seen', ''), threshold_minutes)
            
            if status == "Online":
                stats['online'] += 1
            elif status == "Offline":
                stats['offline'] += 1
            else:
                stats['unknown'] += 1
            
            # Group by CID
            cid = row.get('cid', 'unknown')
            if cid not in stats['by_cid']:
                stats['by_cid'][cid] = {'online': 0, 'offline': 0, 'unknown': 0}
            stats['by_cid'][cid][status.lower()] += 1
            
            # Group by OS
            os_name = row.get('platform_name', 'unknown')
            if os_name not in stats['by_os']:
                stats['by_os'][os_name] = {'online': 0, 'offline': 0, 'unknown': 0}
            stats['by_os'][os_name][status.lower()] += 1
    
    return stats


def filter_online_devices(input_file, output_file, threshold_minutes=30):
    """Create a new CSV with only online devices."""
    online_count = 0
    total_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # Add online_status fields if not present
        if 'online_status' not in fieldnames:
            fieldnames = fieldnames + ['online_status', 'minutes_since_seen']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                total_count += 1
                
                # Check or calculate online status
                if 'online_status' in row and row['online_status'] == 'Online':
                    writer.writerow(row)
                    online_count += 1
                else:
                    status, minutes = calculate_online_status(row.get('last_seen', ''), threshold_minutes)
                    if status == "Online":
                        row['online_status'] = status
                        row['minutes_since_seen'] = minutes
                        writer.writerow(row)
                        online_count += 1
    
    return online_count, total_count


def main():
    parser = argparse.ArgumentParser(description='Analyze device discovery CSV files')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--threshold', type=int, default=30,
                       help='Minutes threshold for online status (default: 30)')
    parser.add_argument('--filter-online', metavar='OUTPUT_FILE',
                       help='Create new CSV with only online devices')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    # Analyze the CSV
    print(f"\nAnalyzing: {args.csv_file}")
    print(f"Online threshold: {args.threshold} minutes")
    print("-" * 60)
    
    stats = analyze_csv(args.csv_file, args.threshold)
    
    # Print overall statistics
    print(f"\nOverall Statistics:")
    print(f"  Total devices: {stats['total']}")
    print(f"  Online: {stats['online']} ({stats['online']*100/stats['total']:.1f}%)")
    print(f"  Offline: {stats['offline']} ({stats['offline']*100/stats['total']:.1f}%)")
    if stats['unknown'] > 0:
        print(f"  Unknown: {stats['unknown']} ({stats['unknown']*100/stats['total']:.1f}%)")
    
    # Print by CID if multiple
    if len(stats['by_cid']) > 1:
        print(f"\nBy CID:")
        for cid, counts in sorted(stats['by_cid'].items()):
            total = sum(counts.values())
            print(f"  {cid[:16]}...: {total} devices "
                  f"(Online: {counts['online']}, Offline: {counts['offline']})")
    
    # Print by OS if multiple
    if len(stats['by_os']) > 1:
        print(f"\nBy Operating System:")
        for os_name, counts in sorted(stats['by_os'].items()):
            total = sum(counts.values())
            print(f"  {os_name}: {total} devices "
                  f"(Online: {counts['online']}, Offline: {counts['offline']})")
    
    # Filter online devices if requested
    if args.filter_online:
        print(f"\nFiltering online devices to: {args.filter_online}")
        online, total = filter_online_devices(args.csv_file, args.filter_online, args.threshold)
        print(f"Exported {online} online devices out of {total} total")
        print(f"Online rate: {online*100/total:.1f}%")


if __name__ == "__main__":
    main()