# 📖 Enhanced Link Grabber & Site Map Visualizer

## Overview

This is a powerful and fast asynchronous web crawler written in Python. It's designed to scan a website up to a specified depth, discover all internal links, and generate a beautiful, interactive site map visualization.

Perfect for:

* SEO analysis
* Understanding a website's structure
* Finding broken links

The script uses `asyncio` and `aiohttp` for high-speed, concurrent scanning, and generates a visual graph using `pyvis` and `networkx`. The command-line UI is powered by `rich` for an elegant experience.

---

## ✨ Features

* **Asynchronous Scanning**: Scans multiple pages concurrently using `asyncio` and `aiohttp`.
* **Depth Control**: Set scan depth (e.g., 1 for shallow, 3 for deep crawl).
* **Interactive Visualization**: Generates a `site_map.html` with a zoomable, clickable graph.
* **Domain-Scoped**: Only scans pages within the same domain.
* **robots.txt Aware**: Skips paths disallowed by `robots.txt`.
* **Elegant CLI**: Colorful and informative command-line interface using `rich`.
* **URL Normalization**: Prevents duplicate scans by handling URL variations smartly.

---

## ⚙️ Requirements

Requires **Python 3.7+** and the following libraries:

* `aiohttp`
* `beautifulsoup4`
* `rich`
* `networkx`
* `pyvis`

---

## 🚀 Installation & Setup

1. **Clone or Download** this repository.
2. Save the script as `link_grabber.py`
3. (Optional) Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the required packages:

   ```bash
   pip install aiohttp beautifulsoup4 rich networkx pyvis
   ```

---

## 🖥️ How to Use

Run the script from terminal:

```bash
python link_grabber.py
```

### You'll be prompted to:

* **Enter the full URL** (e.g., `https://www.google.com`)
* **Select scan depth** (1, 2, or 3)

A real-time progress bar will appear as the crawler works.

```bash
[bold]An interactive site map generator.[/bold]
[bold yellow]Enter the full URL to scan (e.g., https://www.google.com):[/bold yellow]
```

---

## 📊 Output

After the scan completes:

* **Terminal Summary**: Lists scanned URLs grouped by HTTP status (200, 404, etc.)
* **Interactive Graph**: A file named `site_map.html` will be created in your directory

### Example Visualization (site\_map.html):

> *This is a placeholder description for the HTML output.*

In the graph:

* **Nodes** represent pages or links.
* **Edges** are connections between pages.
* **Colors** show status (e.g., Blue = 200 OK, Red = 404 Error).
* **Clickable**: Click nodes to open the URL in a browser.

---

## 📝 Author

Created with ❤️ by **AMIRX**
