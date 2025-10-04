#!/usr/bin/env python3
"""
Adam Curtis Documentary Downloader

Downloads all Adam Curtis documentaries from ThoughtMaybe.com and organizes them
by year and series with full episode titles.

Features:
- Automatically detects optimal parallel download workers based on connection speed
- Organizes videos into folders: (year) series_name/episode_number - episode_title.mp4
- Tracks download statistics (speed, total size, time saved via parallelization)
- Handles failures gracefully with automatic retry capability
- Uses only Python standard library (no external dependencies required)

Usage:
    python3 download_adam_curtis.py <html_file> [output_directory]

    html_file: HTML file containing all Adam Curtis documentaries (concatenated)
    output_directory: Where to save videos (default: ./adam_curtis_collection)

Example:
    python3 download_adam_curtis.py all_docs.html ./videos

Prerequisites:
    - Python 3.7+
    - wget command-line tool
    - curl (for speed test)

Author: Generated for downloading Adam Curtis documentaries from ThoughtMaybe
License: MIT
"""

import re
import os
import sys
import subprocess
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def sanitize_filename(name):
    """Remove or replace characters that are invalid in filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name


def parse_html_for_videos(html_file):
    """Parse multi-document HTML file to extract all series, years, and episode info."""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on DOCTYPE to get individual documents
    documents = re.split(r'<!DOCTYPE html>', content)
    documents = [doc for doc in documents if doc.strip()]

    print(f"Found {len(documents)} documentaries in file\n")

    series_list = []

    for doc_idx, doc in enumerate(documents):
        # Extract series title
        title_match = re.search(r'<h1 class="light-title entry-title">([^<]+)</h1>', doc)
        if not title_match:
            continue

        series_title = title_match.group(1)
        # Clean up HTML entities
        series_title = series_title.replace('&#8217;', "'").replace('&#8212;', '—')
        series_title = series_title.replace('&amp;', '&').replace('&#8211;', '–')

        # Extract year
        year_match = re.search(r'<span class=item-date>(\d{4})</span>', doc)
        year = year_match.group(1) if year_match else 'Unknown'

        # Extract video sources
        source_pattern = r'<source src=([^\s>]+)\s+(?:title="([^"]+)")?\s*type=video/mp4>'
        sources = re.findall(source_pattern, doc)

        if not sources:
            continue

        # Extract episode titles from playlist-title divs
        playlist_pattern = r'<div class=playlist-title><a[^>]*>([^<]+)</a></div>'
        playlist_titles = re.findall(playlist_pattern, doc)
        playlist_titles = [t.replace('&#8212;', '—').replace('&#8217;', "'").replace('&amp;', '&').replace('&#8211;', '–') for t in playlist_titles]

        episodes = []
        for idx, (url, source_title) in enumerate(sources):
            if idx < len(playlist_titles):
                episode_title = playlist_titles[idx]
            elif source_title:
                episode_title = source_title
            else:
                episode_title = series_title

            episodes.append({'url': url, 'title': episode_title})

        series_list.append({
            'title': series_title,
            'year': year,
            'episodes': episodes,
            'order': doc_idx
        })

        print(f"  [{doc_idx + 1:2d}] ({year}) {series_title} - {len(episodes)} episode(s)")

    return series_list


class DownloadStats:
    """Thread-safe download statistics tracker."""
    def __init__(self):
        self.lock = threading.Lock()
        self.total_bytes = 0
        self.total_time = 0
        self.download_count = 0
        self.active_downloads = 0

    def add_download(self, bytes_downloaded, time_taken):
        with self.lock:
            self.total_bytes += bytes_downloaded
            self.total_time += time_taken
            self.download_count += 1

    def increment_active(self):
        with self.lock:
            self.active_downloads += 1

    def decrement_active(self):
        with self.lock:
            self.active_downloads -= 1

    def get_stats(self):
        with self.lock:
            return {
                'total_bytes': self.total_bytes,
                'total_time': self.total_time,
                'download_count': self.download_count,
                'active_downloads': self.active_downloads,
                'avg_speed_mbps': (self.total_bytes * 8 / (1024 * 1024) / self.total_time) if self.total_time > 0 else 0,
                'total_gb': self.total_bytes / (1024 ** 3)
            }


def speed_test(url_sample, timeout=5):
    """Download a small chunk to estimate download speed and determine worker count."""
    print("\nRunning speed test to determine optimal worker count...")

    cmd = [
        'curl', '-s', '-o', '/dev/null', '-w', '%{speed_download}',
        '--max-time', str(timeout),
        '--range', '0-1048576',  # Download first 1MB
        url_sample
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        speed_bytes = float(result.stdout.strip())
        speed_mbps = (speed_bytes * 8) / (1024 * 1024)

        # Determine worker count based on speed
        if speed_mbps < 10:
            workers = 2
        elif speed_mbps < 50:
            workers = 4
        elif speed_mbps < 100:
            workers = 6
        else:
            workers = 8

        print(f"Estimated download speed: {speed_mbps:.1f} Mbps")
        print(f"Using {workers} parallel workers\n")
        return workers
    except Exception as e:
        print(f"Speed test failed: {e}. Using default 3 workers.\n")
        return 3


def download_video(url, output_dir, filename, stats):
    """Download a video using wget with browser headers and track statistics."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / filename

    # Skip if already exists
    if output_file.exists():
        file_size = output_file.stat().st_size
        print(f"[SKIP] {filename} (already exists, {file_size / (1024**2):.1f} MB)")
        return {'success': True, 'bytes': 0, 'time': 0}

    stats.increment_active()
    start_time = time.time()

    cmd = [
        'wget',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '--referer=https://thoughtmaybe.com/',
        '--timeout=30',
        '--tries=3',
        '--quiet',
        '--show-progress',
        '-O', str(output_file),
        url
    ]

    current_stats = stats.get_stats()
    print(f"[START] {filename} | Active: {current_stats['active_downloads']} | Avg: {current_stats['avg_speed_mbps']:.1f} Mbps")

    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed = time.time() - start_time
    stats.decrement_active()

    if result.returncode == 0:
        file_size = output_file.stat().st_size if output_file.exists() else 0
        speed_mbps = (file_size * 8 / (1024 * 1024) / elapsed) if elapsed > 0 else 0

        stats.add_download(file_size, elapsed)

        print(f"[DONE] {filename} | {file_size / (1024**2):.1f} MB in {elapsed:.1f}s | {speed_mbps:.1f} Mbps")
        return {'success': True, 'bytes': file_size, 'time': elapsed}
    else:
        # Clean up failed partial download
        if output_file.exists():
            output_file.unlink()

        error_msg = result.stderr.strip().split('\n')[-1] if result.stderr else "Unknown error"
        print(f"[FAILED] {filename}: {error_msg}")
        return {'success': False, 'bytes': 0, 'time': elapsed}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage: python3 download_adam_curtis.py <html_file> [output_directory]")
        print("Example: python3 download_adam_curtis.py all_docs.html ./videos")
        sys.exit(1)

    html_file = sys.argv[1]
    base_dir = sys.argv[2] if len(sys.argv) > 2 else './adam_curtis_collection'

    if not os.path.exists(html_file):
        print(f"Error: File '{html_file}' not found")
        sys.exit(1)

    print(f"Adam Curtis Documentary Downloader")
    print(f"{'='*70}")
    print(f"Parsing {html_file}...\n")

    series_list = parse_html_for_videos(html_file)

    if not series_list:
        print("No videos found in HTML file!")
        sys.exit(1)

    total_episodes = sum(len(s['episodes']) for s in series_list)
    print(f"\nFound {len(series_list)} series with {total_episodes} total episodes")

    # Speed test with first video
    if series_list and series_list[0]['episodes']:
        sample_url = series_list[0]['episodes'][0]['url']
        workers = speed_test(sample_url)
    else:
        workers = 3

    # Prepare download tasks
    download_tasks = []
    for series in series_list:
        year = series['year']
        series_name = f"({year}) {series['title']}"
        series_dir = os.path.join(base_dir, sanitize_filename(series_name))

        for idx, episode in enumerate(series['episodes'], 1):
            filename = f"{idx:02d} - {sanitize_filename(episode['title'])}.mp4"
            download_tasks.append({
                'url': episode['url'],
                'dir': series_dir,
                'filename': filename,
                'series': series_name
            })

    print(f"{'='*70}")
    print(f"Starting download of {len(download_tasks)} videos...")
    print(f"{'='*70}\n")

    # Download with statistics
    stats = DownloadStats()
    overall_start = time.time()
    success_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(download_video, task['url'], task['dir'], task['filename'], stats): task
            for task in download_tasks
        }

        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                result = future.result()
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"[ERROR] {task['filename']}: {e}")
                failed_count += 1

    overall_elapsed = time.time() - overall_start
    final_stats = stats.get_stats()

    print(f"\n{'='*70}")
    print(f"Download Complete!")
    print(f"{'='*70}")
    print(f"Success: {success_count} | Failed: {failed_count}")
    print(f"Total Downloaded: {final_stats['total_gb']:.2f} GB")
    print(f"Total Time: {overall_elapsed / 60:.1f} minutes")
    print(f"Average Speed: {final_stats['avg_speed_mbps']:.1f} Mbps")
    print(f"Cumulative Download Time: {final_stats['total_time'] / 60:.1f} minutes")
    print(f"Time Saved (Parallel): {(final_stats['total_time'] - overall_elapsed) / 60:.1f} minutes")
    print(f"\nVideos organized in: {base_dir}")
    print(f"{'='*70}")

    if failed_count > 0:
        print(f"\n⚠️  {failed_count} downloads failed. Run retry script to attempt again:")
        print(f"   python3 retry_failed.py {html_file} {base_dir}")


if __name__ == '__main__':
    main()
