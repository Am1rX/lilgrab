import asyncio
import aiohttp
import urllib.parse
from bs4 import BeautifulSoup
from typing import Set, Dict, List
from datetime import datetime
from rich.console import Console
from rich.progress import Progress
import time
import networkx as nx
from pyvis.network import Network
import os
from collections import defaultdict

console = Console()

class LinkGrabber:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.found_links: Dict[str, dict] = {}
        self.session = None
        self.rate_limit = 0.1  # 100ms between requests
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.graph = nx.DiGraph()  # Directed graph for site structure
        self.similar_links = defaultdict(set)  # Track similar links

    def normalize_url(self, base_url: str, href: str) -> str:
        """Normalize and join URLs properly"""
        try:
            normalized = str(urllib.parse.urljoin(base_url, href))
            # Remove trailing slashes and fragments
            normalized = normalized.rstrip('/')
            normalized = normalized.split('#')[0]
            normalized = normalized.split('?')[0]  # Remove query parameters
            return normalized
        except Exception:
            return ""

    def is_similar_link(self, url1: str, url2: str) -> bool:
        """Check if two URLs are similar (same path structure but different parameters)"""
        try:
            parsed1 = urllib.parse.urlparse(url1)
            parsed2 = urllib.parse.urlparse(url2)
            
            # Compare domains and paths
            return (parsed1.netloc == parsed2.netloc and 
                   parsed1.path.rstrip('/') == parsed2.path.rstrip('/'))
        except:
            return False

    def get_canonical_url(self, url: str) -> str:
        """Get the canonical form of a URL by checking similar URLs"""
        for group in self.similar_links.values():
            if url in group:
                return min(group)  # Use the shortest URL as canonical
        return url

    def add_similar_link(self, url: str):
        """Add a URL to the similar links tracking"""
        added = False
        for key, group in self.similar_links.items():
            if any(self.is_similar_link(url, existing) for existing in group):
                group.add(url)
                added = True
                break
        
        if not added:
            self.similar_links[url].add(url)

    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return url

    def get_path(self, url: str) -> str:
        """Extract path from URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.path or '/'
        except:
            return '/'

    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def fetch_url(self, url: str) -> dict:
        """Fetch a URL and return detailed information"""
        try:
            async with self.session.get(url) as response:
                content = await response.read()
                return {
                    'url': url,
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

    async def extract_links(self, url: str, html_content: bytes) -> List[str]:
        """Extract all links from HTML content"""
        links = set()
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'form']):
                href = tag.get('href') or tag.get('src') or tag.get('action')
                if href:
                    normalized_url = self.normalize_url(url, href)
                    if normalized_url and not normalized_url.startswith(('mailto:', 'tel:', 'javascript:')):
                        self.add_similar_link(normalized_url)
                        canonical_url = self.get_canonical_url(normalized_url)
                        links.add(canonical_url)
        except Exception as e:
            console.print(f"[red]Error extracting links from {url}: {e}[/red]")
        return list(links)

    async def scan_url(self, url: str, max_depth: int = 2, current_depth: int = 0):
        """Scan a URL for links with depth control"""
        if current_depth > max_depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        await asyncio.sleep(self.rate_limit)  # Rate limiting

        result = await self.fetch_url(url)
        self.found_links[url] = result

        # Add node to graph
        node_attrs = {
            'title': f"Status: {result.get('status')}\nType: {result.get('content_type', 'unknown')}",
            'label': self.get_path(url)[:30] + '...' if len(self.get_path(url)) > 30 else self.get_path(url)
        }
        self.graph.add_node(url, **node_attrs)

        if result.get('status') == 200 and 'text/html' in result.get('content_type', ''):
            links = await self.extract_links(url, result['content'])
            if current_depth < max_depth:
                tasks = []
                for link in links:
                    if link not in self.visited_urls:
                        # Add edge to graph
                        self.graph.add_edge(url, link)
                        tasks.append(self.scan_url(link, max_depth, current_depth + 1))
                await asyncio.gather(*tasks)

    def create_visualization(self, output_file: str = "site_map.html"):
        """Create an interactive visualization of the crawled site"""
        # Create a Pyvis network
        net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
        
        # Add nodes with different colors based on status
        for node, data in self.graph.nodes(data=True):
            status = self.found_links[node].get('status', 0)
            content_type = self.found_links[node].get('content_type', 'unknown')
            
            # Determine node color based on content type and status
            if status == 200:
                if 'html' in content_type.lower():
                    color = "#97c2fc"  # blue for HTML
                elif 'image' in content_type.lower():
                    color = "#ffb347"  # orange for images
                elif 'javascript' in content_type.lower():
                    color = "#98FB98"  # green for JS
                elif 'css' in content_type.lower():
                    color = "#DDA0DD"  # purple for CSS
                else:
                    color = "#97c2fc"  # default blue
            else:
                color = "#fb7e81"  # red for errors

            # Create detailed title with similar URLs
            similar_urls = [u for u in self.similar_links.get(node, set()) if u != node]
            title = f"Status: {status}\nType: {content_type}"
            if similar_urls:
                title += "\n\nSimilar URLs:"
                for similar in similar_urls[:5]:  # Show up to 5 similar URLs
                    title += f"\n- {similar}"
                if len(similar_urls) > 5:
                    title += f"\n... and {len(similar_urls) - 5} more"

            # Add node with onclick event to open URL
            net.add_node(node, 
                        title=title,
                        label=self.get_path(node)[:30] + '...' if len(self.get_path(node)) > 30 else self.get_path(node),
                        color=color)

        # Add edges
        for edge in self.graph.edges():
            net.add_edge(edge[0], edge[1])

        # Set physics layout and enable URL clicking
        net.set_options("""
        var options = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "springLength": 100
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": {
                    "enabled": true
                }
            },
            "nodes": {
                "shape": "dot",
                "size": 20,
                "font": {
                    "size": 12,
                    "face": "Tahoma"
                }
            }
        }
        """)

        # Add JavaScript to make nodes clickable
        net.html += """
        <script>
        network.on("click", function(params) {
            if (params.nodes.length > 0) {
                var node = params.nodes[0];
                window.open(node, '_blank');
            }
        });
        </script>
        """

        # Save the visualization
        try:
            net.save_graph(output_file)
            console.print(f"\n[green]Site map visualization saved to: {os.path.abspath(output_file)}[/green]")
        except Exception as e:
            console.print(f"\n[red]Error saving visualization: {e}[/red]")

    async def scan(self, url: str, max_depth: int = 2):
        """Main scanning function"""
        await self.init_session()
        console.print(f"[bold green]Starting scan of {url}[/bold green]")
        
        start_time = time.time()
        try:
            await self.scan_url(url, max_depth)
        finally:
            await self.close_session()
        
        duration = time.time() - start_time
        self.print_results(duration)
        
        # Create visualization
        self.create_visualization()

    def print_results(self, duration: float):
        """Print detailed scan results"""
        console.print("\n[bold blue]Scan Results[/bold blue]")
        console.print(f"Total unique URLs scanned: {len(self.visited_urls)}")
        console.print(f"Total similar URLs found: {sum(len(group) for group in self.similar_links.values()) - len(self.visited_urls)}")
        console.print(f"Scan duration: {duration:.2f} seconds")
        
        # Group results by status
        status_groups = {}
        for url, data in self.found_links.items():
            status = data.get('status', 0)
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append((url, data))

        # Print results by status code
        for status in sorted(status_groups.keys()):
            color = "green" if status == 200 else "red"
            console.print(f"\n[{color}]Status {status}:[/{color}]")
            for url, data in status_groups[status]:
                console.print(f"  URL: {url}")
                similar = [u for u in self.similar_links.get(url, set()) if u != url]
                if similar:
                    console.print(f"    Similar URLs: {len(similar)}")
                if 'content_type' in data:
                    console.print(f"    Type: {data['content_type']}")
                if 'size' in data:
                    console.print(f"    Size: {data['size']} bytes")
                if 'error' in data:
                    console.print(f"    Error: {data['error']}")

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

async def main():
    console.print('''
[bold cyan]Enhanced Link Grabber[/bold cyan]
    1. Quick Scan (depth=1)
    2. Full Scan (depth=2)
    3. Deep Scan (depth=3)
    4. Exit
    ''')

    while True:
        try:
            url = console.input("[yellow]Enter URL:[/yellow] ").strip()
            if not validate_url(url):
                console.print("[red]Invalid URL! Please include http:// or https://[/red]")
                continue

            option = console.input("[yellow]Select option:[/yellow] ")
            
            if option == '4':
                break
                
            depth = {'1': 1, '2': 2, '3': 3}.get(option, 1)
            grabber = LinkGrabber()
            await grabber.scan(url, depth)
            
        except KeyboardInterrupt:
            console.print("\n[red]Scan interrupted by user[/red]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main())

#Created by AMIRX
