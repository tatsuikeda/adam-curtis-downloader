# Adam Curtis Documentary Downloader

Download and organize all Adam Curtis documentaries from ThoughtMaybe.com with proper episode names and chronological organization.

## Features

- 🎬 Downloads all Adam Curtis documentaries (56+ episodes, ~24GB)
- 📁 Organizes by year and series: `(year) series_name/episode_number - episode_title.mp4`
- ⚡ Parallel downloads with automatic worker optimization based on connection speed
- 📊 Real-time statistics tracking (speed, progress, time saved)
- 🔄 Automatic retry for failed downloads
- 🐍 Pure Python - only uses standard library (no pip install needed!)

## Prerequisites

- Python 3.7 or higher
- `wget` command-line tool
- `curl` (for speed test)

### Installing wget

**macOS:**
```bash
brew install wget
```

**Ubuntu/Debian:**
```bash
sudo apt-get install wget
```

**Windows:**
Download from [GNU Wget](https://eternallybored.org/misc/wget/)

## Quick Start

1. Use the included `all_adam_curtis_docs_till_shifty.html` (index snapshot from ThoughtMaybe)

2. **Run the downloader:**
```bash
python3 download_adam_curtis.py all_adam_curtis_docs_till_shifty.html
```

3. **Optional: Specify output directory:**
```bash
python3 download_adam_curtis.py all_adam_curtis_docs_till_shifty.html ./my_videos
```

## Output Structure

```
adam_curtis_collection/
├── (1992) Pandora's Box/
│   ├── 01 - Part 1 — The Engineers Plot.mp4
│   ├── 02 - Part 2 — To The Brink Of Eternity.mp4
│   └── ...
├── (2002) The Century of the Self/
│   ├── 01 - Part 1 — Happiness Machines.mp4
│   ├── 02 - Part 2 — The Engineering of Consent.mp4
│   └── ...
├── (2021) Can't Get You Out of My Head/
│   └── ...
└── (2025) Shifty/
    └── ...
```

## Retry Failed Downloads

If some downloads fail (intermittent network issues), use the retry script:

```bash
python3 retry_failed.py all_adam_curtis_docs_till_shifty.html
```

This will:
- Scan for missing videos
- Retry downloads one at a time with better error reporting
- Skip already downloaded files

## Statistics Example

```
======================================================================
Download Complete!
======================================================================
Success: 56 | Failed: 0
Total Downloaded: 23.52 GB
Total Time: 8.7 minutes
Average Speed: 171.4 Mbps
Cumulative Download Time: 17.4 minutes
Time Saved (Parallel): 8.6 minutes

Videos organized in: ./adam_curtis_collection
======================================================================
```

## Documentaries Included

The collection includes all Adam Curtis works from 1992-2025:

1. **Pandora's Box** (1992) - 6 episodes
2. **The Living Dead** (1995) - 3 episodes
3. **25 Million Pounds** (1996)
4. **The Way of All Flesh** (1997)
5. **The Mayfair Set** (1999) - 4 episodes
6. **The Century of the Self** (2002) - 4 episodes
7. **The Power of Nightmares** (2004) - 3 episodes
8. **The Trap** (2007) - 3 episodes
9. **All Watched Over By Machines of Loving Grace** (2011) - 3 episodes
10. **Bitter Lake** (2015)
11. **HyperNormalisation** (2016)
12. **Can't Get You Out of My Head** (2021) - 6 episodes
13. **Russia 1985–1999: TraumaZone** (2022) - 7 episodes
14. **Shifty** (2025) - 5 episodes
15. ...and more!

## How It Works

1. **Parses HTML** - Extracts video URLs, titles, years from concatenated HTML documents
2. **Speed Test** - Tests download speed to determine optimal parallel workers (2-8)
3. **Parallel Download** - Downloads multiple videos simultaneously using ThreadPoolExecutor
4. **Statistics** - Tracks individual and cumulative download speeds, sizes, and times
5. **Organization** - Creates year-prefixed folders with properly named episode files

## Troubleshooting

**Downloads fail with "Unknown error":**
- Some videos may take longer to download - just run `retry_failed.py`
- Check your internet connection
- Ensure wget is installed: `wget --version`

**"Command not found: wget":**
- Install wget using instructions above

**Script finds no videos:**
- Ensure HTML file contains the full page source from ThoughtMaybe
- Check that the HTML file path is correct

## Files

- `download_adam_curtis.py` - Main download script
- `retry_failed.py` - Retry utility for failed downloads
- `README.md` - This file
- `.gitignore` - Ignores downloads and temporary files
 - `all_adam_curtis_docs_till_shifty.html` - ThoughtMaybe index snapshot up to 2025 "Shifty"

## License

MIT License - Use freely, attribute if you share

## Credits

Scripts created for downloading Adam Curtis documentaries from [ThoughtMaybe.com](https://thoughtmaybe.com)

Adam Curtis documentaries © BBC

