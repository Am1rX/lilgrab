import asyncio
import aiohttp
import urllib.parse
import urllib.robotparser
from bs4 import BeautifulSoup
from typing import Set, Dict, List
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import time
import networkx as nx
from pyvis.network import Network
import os
from collections import defaultdict

console = Console()

class LinkGrabber:
    """
    An asynchronous web crawler that scans a website up to a specified depth,
    collects all links, and generates an interactive site map.
    """
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.visited_urls: Set[str] = set()
        self.found_links: Dict[str, dict] = {}
        self.graph = nx.DiGraph()
        self.target_domain: str = ""
        
        # Use a semaphore to limit concurrent requests instead of a fixed delay
        self.semaphore = asyncio.Semaphore(10)
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.headers = {'User-Agent': 'PythonLinkGrabber/1.0'}
        
        # For progress bar
        self.progress: Progress | None = None
        self.task_id = None
        self.scanned_count = 0
        
        # For robots.txt parsing
        self.robot_parser = urllib.robotparser.RobotFileParser()

    def normalize_url(self, base_url: str, href: str) -> str | None:
        """
        Normalizes a URL by joining it with the base, sorting query parameters,
        and removing the fragment. This is a more robust way to find canonical URLs.
        """
        try:
            url = urllib.parse.urljoin(base_url, href.strip())
            parsed = urllib.parse.urlparse(url)
            
            # Sort query parameters to handle URLs like /page?a=1&b=2 and /page?b=2&a=1 as the same
            sorted_query = urllib.parse.urlencode(sorted(urllib.parse.parse_qsl(parsed.query)))
            
            # Reconstruct the URL with a cleaned path and sorted query, removing the fragment
            path = parsed.path if parsed.path else '/'
            normalized = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                path,
                '',
                sorted_query,
                ''  # Remove fragment
            ))
            return normalized
        except Exception as e:
            console.print(f"[bright_black]Could not normalize URL '{href}': {e}[/bright_black]")
            return None

    def get_domain(self, url: str) -> str:
        """Extracts the domain (netloc) from a URL."""
        try:
            return urllib.parse.urlparse(url).netloc
        except:
            return ''

    async def init_session(self):
        """Initializes the aiohttp ClientSession."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout, headers=self.headers)

    async def close_session(self):
        """Closes the aiohttp ClientSession."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch_url(self, url: str) -> dict:
        """Fetches a single URL and returns its details."""
        try:
            # Use the semaphore to limit concurrency
            async with self.semaphore:
                async with self.session.get(url, allow_redirects=True) as response:
                    content = await response.read()
                    return {
                        'url': str(response.url), # Use the final URL after redirects
                        'status': response.status,
                        'content_type': response.headers.get('content-type', 'unknown'),
                        'size': len(content),
                        'content': content,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                'url': url,
                'status': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def extract_links(self, base_url: str, html_content: bytes) -> List[str]:
        """Extracts all valid, in-domain links from HTML content."""
        links = set()
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'form']):
                href = tag.get('href') or tag.get('src') or tag.get('action')
                if not href:
                    continue

                normalized_url = self.normalize_url(base_url, href)
                if not normalized_url or normalized_url.startswith(('mailto:', 'tel:', 'javascript:')):
                    continue

                # Ensure we only scan links within the target domain
                if self.get_domain(normalized_url) == self.target_domain:
                    links.add(normalized_url)
        except Exception as e:
            console.print(f"[red]Error extracting links from {base_url}: {e}[/red]")
        return list(links)

    async def scan_url(self, url: str, max_depth: int, current_depth: int = 0):
        """Recursively scans a URL, respecting depth limits and visited status."""
        if current_depth > max_depth or url in self.visited_urls:
            return

        # Check robots.txt before fetching
        if not self.robot_parser.can_fetch(self.headers['User-Agent'], url):
            console.print(f"[yellow]Skipping (disallowed by robots.txt): {url}[/yellow]")
            return

        self.visited_urls.add(url)
        
        result = await self.fetch_url(url)
        self.found_links[url] = result

        # Update progress bar
        self.scanned_count += 1
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, description=f"[cyan]Scanned: [bold]{self.scanned_count}[/bold] URLs")

        # Add node to the graph
        path = urllib.parse.urlparse(url).path or '/'
        label = path[:30] + '...' if len(path) > 30 else path
        self.graph.add_node(url, label=label, title=f"Status: {result.get('status', 0)}")

        if result.get('status') == 200 and 'text/html' in result.get('content_type', ''):
            links = await self.extract_links(url, result['content'])
            if current_depth < max_depth:
                tasks = []
                for link in links:
                    if link not in self.visited_urls:
                        self.graph.add_edge(url, link)
                        tasks.append(self.scan_url(link, max_depth, current_depth + 1))
                await asyncio.gather(*tasks)

    def create_visualization(self, output_file: str = "site_map.html"):
        """Creates an interactive Pyvis visualization of the site structure."""
        if not self.graph.nodes:
            console.print("[yellow]Graph is empty, skipping visualization.[/yellow]")
            return

        net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", notebook=False)
        
        for node in self.graph.nodes():
            data = self.found_links.get(node, {})
            status = data.get('status', 0)
            content_type = data.get('content_type', 'unknown')
            
            if status >= 400: color = "#fb7e81"  # Red for client/server errors
            elif status >= 300: color = "#ffb347"  # Orange for redirects
            elif status == 200: color = "#97c2fc"  # Blue for success
            else: color = "#cccccc" # Grey for unknown/error
            
            title = f"URL: {node}\nStatus: {status}\nType: {content_type}"
            net.add_node(node, label=self.graph.nodes[node]['label'], title=title, color=color)

        net.add_edges(self.graph.edges())
        
        net.set_options("""
        var options = {
          "physics": { "solver": "forceAtlas2Based", "forceAtlas2Based": { "gravitationalConstant": -100, "springLength": 100 } },
          "interaction": { "hover": true, "navigationButtons": true, "keyboard": true },
          "nodes": { "shape": "dot", "size": 16 }
        }
        """)
        
        # Add JS to open node URL in a new tab on click
        net.html = net.html.replace("</body>", """
        <script>
        network.on("click", function(params) {
          if (params.nodes.length > 0) {
            var node = params.nodes[0];
            window.open(node, '_blank');
          }
        });
        </script>
        </body>""")

        try:
            net.save_graph(output_file)
            console.print(f"\n[green]Site map visualization saved to: [link=file://{os.path.abspath(output_file)}]{os.path.abspath(output_file)}[/link][/green]")
        except Exception as e:
            console.print(f"\n[red]Error saving visualization: {e}[/red]")

    async def scan(self, url: str, max_depth: int):
        """Main entry point for the scanning process."""
        await self.init_session()
        self.target_domain = self.get_domain(url)
        console.print(f"[bold green]Starting scan of [underline]{url}[/underline] (Domain: {self.target_domain})[/bold green]")
        
        # Fetch and parse robots.txt
        robots_url = urllib.parse.urljoin(url, '/robots.txt')
        self.robot_parser.set_url(robots_url)
        try:
            await asyncio.get_event_loop().run_in_executor(None, self.robot_parser.read)
            console.print(f"[bright_black]Successfully parsed {robots_url}[/bright_black]")
        except Exception as e:
            console.print(f"[yellow]Could not fetch or parse robots.txt: {e}[/yellow]")

        start_time = time.time()
        
        progress_columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ]
        
        try:
            with Progress(*progress_columns, console=console) as progress:
                self.progress = progress
                self.task_id = self.progress.add_task("[cyan]Crawling...", total=None) # Indeterminate
                await self.scan_url(url, max_depth)
                self.progress.update(self.task_id, total=1, completed=1, description="[green]Crawl complete!")
        finally:
            await self.close_session()
        
        duration = time.time() - start_time
        self.print_results(duration)
        self.create_visualization()

    def print_results(self, duration: float):
        """Prints a summary of the scan results."""
        console.print("\n[bold blue]----- Scan Summary -----[/bold blue]")
        console.print(f"Total unique URLs scanned: [bold]{len(self.visited_urls)}[/bold]")
        console.print(f"Scan duration: [bold]{duration:.2f} seconds[/bold]")
        
        status_groups = defaultdict(list)
        for url, data in self.found_links.items():
            status_groups[data.get('status', 0)].append(url)

        for status in sorted(status_groups.keys()):
            color = "green" if 200 <= status < 300 else "yellow" if 300 <= status < 400 else "red"
            console.print(f"\n[bold {color}]Status {status}: {len(status_groups[status])} URLs[/bold {color}]")
            # for url in status_groups[status][:5]: # Print first 5 for brevity
            #     console.print(f"  - {url}")
            # if len(status_groups[status]) > 5:
            #     console.print(f"  ... and {len(status_groups[status]) - 5} more.")

def validate_url(url: str) -> bool:
    """Validates if the URL has a scheme and netloc."""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

async def main():
    """Main function to run the crawler from the command line."""
    console.print('''
[bold]An interactive site map generator.[/bold]
''')
    
    while True:
        try:
            url = console.input("[bold yellow]Enter the full URL to scan (e.g., https://www.google.com):[/bold yellow] ").strip()
            if not validate_url(url):
                console.print("[red]Invalid URL! Please include the scheme (http:// or https://).[/red]\n")
                continue

            depth_str = console.input("[bold yellow]Enter scan depth (1=Quick, 2=Full, 3=Deep):[/bold yellow] ").strip()
            depth = int(depth_str) if depth_str.isdigit() and int(depth_str) > 0 else 1
            
            grabber = LinkGrabber()
            await grabber.scan(url, depth)
            
        except (KeyboardInterrupt, asyncio.CancelledError):
            console.print("\n\n[bold red]Scan interrupted by user. Exiting.[/bold red]")
            break
        except Exception as e:
            console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
        
        if console.input("\n[yellow]Scan another site? (y/n): [/yellow]").lower() != 'y':
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]Program terminated.[/bold red]")

