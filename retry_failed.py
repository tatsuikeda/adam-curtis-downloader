#!/usr/bin/env python3
"""
Retry failed downloads by re-running the downloader on missing files.
"""

import os
import sys
from download_organized_v2 import parse_html_for_videos, sanitize_filename, download_video, DownloadStats
import time

def find_missing_videos(html_file, base_dir):
    """Find videos that should exist but don't."""
    series_list = parse_html_for_videos(html_file)

    missing = []

    for series in series_list:
        year = series['year']
        series_name = f"({year}) {series['title']}"
        series_dir = os.path.join(base_dir, sanitize_filename(series_name))

        for idx, episode in enumerate(series['episodes'], 1):
            episode_title = episode['title']
            filename = f"{idx:02d} - {sanitize_filename(episode_title)}.mp4"
            filepath = os.path.join(series_dir, filename)

            if not os.path.exists(filepath):
                missing.append({
                    'url': episode['url'],
                    'dir': series_dir,
                    'filename': filename,
                    'series': series_name
                })

    return missing

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 retry_failed.py <html_file> [base_download_dir]")
        sys.exit(1)

    html_file = sys.argv[1]
    base_dir = sys.argv[2] if len(sys.argv) > 2 else './downloads'

    print(f"Checking for missing videos in {base_dir}...\n")

    missing = find_missing_videos(html_file, base_dir)

    if not missing:
        print("✓ All videos downloaded successfully!")
        sys.exit(0)

    print(f"Found {len(missing)} missing videos:\n")
    for task in missing:
        print(f"  - {task['filename']}")

    print(f"\n{'='*70}")
    print("Retrying failed downloads (one at a time for better error messages)...")
    print(f"{'='*70}\n")

    stats = DownloadStats()
    success_count = 0
    failed_count = 0
    failed_list = []

    for task in missing:
        result = download_video(task['url'], task['dir'], task['filename'], stats)
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
            failed_list.append(task['filename'])

    final_stats = stats.get_stats()

    print(f"\n{'='*70}")
    print(f"Retry Complete!")
    print(f"{'='*70}")
    print(f"Success: {success_count} | Failed: {failed_count}")

    if failed_count > 0:
        print(f"\nStill failing:")
        for fname in failed_list:
            print(f"  ✗ {fname}")

    if final_stats['total_gb'] > 0:
        print(f"\nTotal Downloaded: {final_stats['total_gb']:.2f} GB")
        print(f"Average Speed: {final_stats['avg_speed_mbps']:.1f} Mbps")

    print(f"{'='*70}")

if __name__ == '__main__':
    main()
