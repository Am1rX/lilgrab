# Enhanced Link Grabber

A powerful asynchronous web crawler and site mapper built in Python that visualizes website structure and relationships.

## Features

- 🚀 **Asynchronous Crawling**: Fast and efficient website scanning using `aiohttp`
- 📊 **Interactive Visualization**: Creates beautiful, interactive site maps using `pyvis` and `networkx`
- 🎯 **Smart URL Detection**: Identifies and groups similar URLs to reduce redundancy
- 📱 **Multi-Resource Support**: Tracks HTML, images, JavaScript, CSS, and other web resources
- 🔍 **Depth Control**: Three scanning modes (Quick, Full, and Deep) for different levels of analysis
- 📈 **Detailed Reporting**: Comprehensive status reports and error tracking
- ⚡ **Rate Limiting**: Built-in rate limiting to prevent server overload

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Am1rX/lilgrab
cd lilgrab
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- aiohttp
- beautifulsoup4
- networkx
- pyvis
- rich

## Usage

Run the script:
```bash
python linkgrabber.py
```

The program will present you with four options:
1. Quick Scan (depth=1) - Scans only the immediate links on the page
2. Full Scan (depth=2) - Scans immediate links and their child pages
3. Deep Scan (depth=3) - Performs a deeper crawl of the website
4. Exit

Enter the URL you want to scan (including http:// or https://) and select your desired scan depth.

## Output

- **Console Output**: Detailed scan results including:
  - Total unique URLs scanned
  - Similar URLs found
  - Status codes for each URL
  - Content types and sizes
  - Error reports if any

- **Visual Output**: An interactive HTML file (`site_map.html`) containing:
  - Color-coded nodes representing different types of resources
  - Clickable nodes that open the corresponding URLs
  - Hover tooltips with detailed information
  - Force-directed graph layout for optimal visualization

## Color Coding

The visualization uses different colors to represent various types of resources:
- 🔵 Blue: HTML pages
- 🟠 Orange: Images
- 🟢 Green: JavaScript files
- 🟣 Purple: CSS files
- 🔴 Red: Error states

## Features in Detail

### URL Normalization
- Removes trailing slashes
- Eliminates fragments and query parameters
- Standardizes relative URLs to absolute URLs

### Similar URL Detection
- Groups URLs with identical paths but different parameters
- Reduces redundancy in the visualization
- Maintains relationships between similar resources

### Rate Limiting
- Implements a 100ms delay between requests
- Prevents overwhelming target servers
- Configurable rate limit settings

## Notes

- The crawler respects basic rate limiting but does not implement robots.txt parsing
- Some websites may block automated requests
- Use responsibly and in accordance with the target website's terms of service

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created by AMIRX

## Contributing

Contributions, issues, and feature requests are welcome! 
