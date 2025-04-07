import numpy as np
import subprocess
import socket
import random
import platform
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LinearSegmentedColormap
import time # For adding slight delay

class PingHeatmap:
    def __init__(self, resolution=90): # Reduced resolution for faster testing maybe?
        print(f"Initializing PingHeatmap with resolution {resolution}...")
        # Create world grid
        self.resolution = resolution
        # Linspace endpoints included: num=resolution means resolution points, resolution-1 intervals
        self.lat_grid = np.linspace(-90, 90, resolution)
        self.lon_grid = np.linspace(-180, 180, resolution * 2)

        # Initialize ping grid with a high value (representing no data)
        self.ping_grid = np.ones((resolution, resolution * 2)) * 1000.0

        # List to store detailed results for scatter plot: [lat, lon, ping, website]
        self.ping_results_list = []

        # Expanded known geolocation data (APPROXIMATE - real locations vary!)
        # Added more diversity + Australian entry
        self.geo_locations = {
        # --- Mapping generated for the 100-site list ---
        # IMPORTANT: These are VERY approximate locations based on HQs, known data center regions,
        # or major cities in the TLD country. Actual server locations depend heavily on CDNs
        # and the user's location. This dictionary provides a *static, symbolic* mapping for the heatmap.

        # == Major Global Services ==
        "google.com": [37.4220, -122.0841],      # Mountain View, CA (Google HQ)
        "cloudflare.com": [37.7749, -122.4194], # San Francisco, CA (Cloudflare HQ)
        "facebook.com": [37.4847, -122.1477],   # Menlo Park, CA (Meta HQ)
        "amazon.com": [39.0438, -77.4874],       # Ashburn, VA (Major AWS/Cloud Hub)
        "microsoft.com": [47.6740, -122.1215],   # Redmond, WA (Microsoft HQ)
        "apple.com": [37.3318, -122.0312],      # Cupertino, CA (Apple HQ)
        "instagram.com": [37.4847, -122.1477],   # Menlo Park, CA (Meta)
        "whatsapp.com": [37.4847, -122.1477],   # Menlo Park, CA (Meta)
        "live.com": [39.0438, -77.4874],       # Ashburn, VA (Microsoft Cloud Hub)
        "office.com": [39.0438, -77.4874],       # Ashburn, VA (Microsoft Cloud Hub)
        "bing.com": [39.0438, -77.4874],       # Ashburn, VA (Microsoft Cloud Hub)
        "icloud.com": [35.5789, -81.2009],       # Maiden, NC (Apple Data Center Region)

        # == Google Regional TLDs ==
        "google.com.au": [-33.8688, 151.2093],    # Sydney, AU
        "google.co.uk": [51.5074, -0.1278],         # London, UK
        "google.de": [50.1109, 8.6821],          # Frankfurt, DE (Major EU Hub)
        "google.fr": [48.8566, 2.3522],          # Paris, FR
        "google.ca": [43.6532, -79.3832],        # Toronto, CA
        "google.co.jp": [35.6895, 139.6917],   # Tokyo, JP
        "google.co.in": [19.0760, 72.8777],       # Mumbai, IN
        "google.com.br": [-23.5505, -46.6333],    # São Paulo, BR
        "google.co.za": [-26.2041, 28.0473],       # Johannesburg, ZA

        # == Other Popular Global/Tech Sites ==
        "wikipedia.org": [1.3521, 103.8198],      # Singapore (Wikimedia DC Region)
        "x.com": [37.7749, -122.4194],            # San Francisco, CA (X/Twitter HQ)
        "netflix.com": [37.2241, -121.9691],      # Los Gatos, CA (Netflix HQ)
        "github.com": [37.7749, -122.4194],       # San Francisco, CA (GitHub HQ / Microsoft)
        "yahoo.com": [40.7128, -74.0060],         # New York, NY (Approx Parent Co)
        "linkedin.com": [37.3688, -122.0363],     # Sunnyvale, CA (LinkedIn HQ / Microsoft)
        "reddit.com": [37.7749, -122.4194],       # San Francisco, CA (Reddit HQ)
        "tiktok.com": [1.3521, 103.8198],         # Singapore (Major Hub)
        "zoom.us": [37.3382, -121.8863],          # San Jose, CA (Zoom HQ)
        "ebay.com": [37.3382, -121.8863],          # San Jose, CA (eBay HQ)
        "wordpress.com": [37.7749, -122.4194],    # San Francisco, CA (Automattic HQ)

        # == News Outlets ==
        "bbc.co.uk": [51.5074, -0.1278],         # London, UK
        "cnn.com": [33.7490, -84.3880],           # Atlanta, GA (CNN HQ)
        "nytimes.com": [40.7128, -74.0060],         # New York, NY (NYT HQ)
        "theguardian.com": [51.5074, -0.1278],      # London, UK

        # == Regional Specific Sites ==
        "mercadolibre.com.ar": [-34.6037, -58.3816], # Buenos Aires, AR
        "yandex.ru": [55.7558, 37.6173],         # Moscow, RU
        "baidu.com": [39.9042, 116.4074],        # Beijing, CN
        "alibaba.com": [30.2741, 120.1551],     # Hangzhou, CN
        "rakuten.co.jp": [35.6895, 139.6917],   # Tokyo, JP
        "naver.com": [37.4204, 127.1269],       # Seongnam, KR (Near Seoul)
        "qq.com": [22.5431, 114.0579],           # Shenzhen, CN (Tencent HQ)

        # == Australian Focused Sites ==
        "news.com.au": [-33.8688, 151.2093],    # Sydney, AU (News Corp Aus)
        "abc.net.au": [-33.8688, 151.2093],     # Sydney, AU (ABC Main Office Area)
        "smh.com.au": [-33.8688, 151.2093],     # Sydney, AU (Nine Entertainment)
        "theage.com.au": [-37.8136, 144.9631],    # Melbourne, AU (Nine Entertainment)
        "telstra.com.au": [-37.8136, 144.9631],    # Melbourne, AU (Telstra HQ)
        "optus.com.au": [-33.7800, 151.1100],     # Sydney, AU (Macquarie Park Area - Optus HQ) - Adjusted slightly
        "seek.com.au": [-37.8136, 144.9631],    # Melbourne, AU (Seek HQ Area)
        "realestate.com.au": [-37.8136, 144.9631],# Melbourne, AU (REA Group HQ Area)
        "gov.au": [-35.2809, 149.1300],       # Canberra, AU (Capital)
        "csiro.au": [-35.2766, 149.1148],       # Canberra, AU (Acton Area - CSIRO HQ) - Adjusted slightly
        "bunnings.com.au": [-37.8245, 145.0600], # Melbourne, AU (Hawthorn East Area - Wesfarmers/Bunnings HQ) - Adjusted slightly
        "woolworths.com.au": [-33.7670, 150.9070], # Sydney, AU (Bella Vista Area - Woolworths HQ) - Adjusted slightly
        "coles.com.au": [-37.8245, 145.0600],    # Melbourne, AU (Hawthorn East Area - Coles HQ) - Adjusted slightly
        "commbank.com.au": [-33.8688, 151.2093],    # Sydney, AU (CBA HQ)
        "nab.com.au": [-37.8183, 144.9548],       # Melbourne, AU (Docklands Area - NAB HQ) - Adjusted slightly

        # == Default Fallback ==
        "fallback_default": [37.7749, -122.4194] # San Francisco, CA
    }
        print("Geolocation dictionary initialized.")

    def run_ping(self, website, count=4, timeout_sec=5):
        """Run ping to measure latency to a website's IP address."""
        print(f"  Attempting to resolve and ping {website}...")

        try:
            # Resolve hostname to IP address first
            # This helps bypass some CDN routing issues for ping, but not all
            # Use the first IPv4 address found
            ip_address = socket.gethostbyname(website)
            print(f"  Resolved {website} to {ip_address}")
            target = ip_address # Ping the IP
        except socket.gaierror:
            print(f"  Error: Could not resolve hostname {website}. Skipping.")
            return None
        except Exception as e:
            print(f"  Error during DNS resolution for {website}: {e}. Skipping.")
            return None

        # Determine the correct ping command based on OS
        system = platform.system()
        if system == "Windows":
            # -n count: number of pings
            # -w timeout_ms: wait timeout in milliseconds for each reply
            cmd = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), target]
        elif system == "Linux":
            # -c count: number of pings
            # -W timeout_sec: wait timeout in seconds for each reply
            # -q: quiet output (only summary) - makes parsing easier
            cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), "-q", target]
        else: # macOS uses similar flags to Linux for this purpose
             # -c count: number of pings
             # -W timeout_ms: wait timeout in milliseconds for each reply (NOTE: macOS uses ms!)
             # -q: quiet output
             cmd = ["ping", "-c", str(count), "-W", str(timeout_sec * 1000), "-q", target]

        print(f"  Executing command: {' '.join(cmd)}")
        ping_times = []
        try:
            # Start the process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Communicate and wait for completion or timeout
            # Use a slightly longer timeout for communicate itself
            output, error = process.communicate(timeout=timeout_sec * count + 5) # Give extra buffer time

            if process.returncode != 0:
                print(f"  Ping command failed for {target} (Return Code: {process.returncode}).")
                if error:
                    print(f"  Error output: {error.strip()}")
                if output:
                    print(f"  Standard output: {output.strip()}")
                return None

            # Parse the ping output (simplified for quiet output)
            # Look for the summary line: rtt min/avg/max/mdev = 1.234/2.345/3.456/0.123 ms
            for line in output.splitlines():
                if 'rtt min/avg/max/mdev' in line or 'round-trip min/avg/max/stddev' in line: # Linux/macOS
                    parts = line.split('=')[1].strip().split('/')
                    if len(parts) >= 4:
                        avg_ping_str = parts[1]
                        avg_ping = float(avg_ping_str)
                        print(f"  Successfully parsed avg ping (Linux/macOS): {avg_ping:.2f} ms from summary")
                        # Return just the average from summary
                        return {"website": website, "ip_address": target, "avg_ping": avg_ping}
                elif 'Average =' in line : # Windows specific summary line
                     parts = line.split('Average =')
                     if len(parts) > 1:
                         avg_ping_str = parts[1].strip().split('ms')[0].strip()
                         avg_ping = float(avg_ping_str)
                         print(f"  Successfully parsed avg ping (Windows): {avg_ping:.2f} ms from summary")
                         # Return just the average from summary
                         return {"website": website, "ip_address": target, "avg_ping": avg_ping}

            # If summary parsing failed, try line-by-line (non-quiet mode fallback, might not trigger with -q)
            if system == "Windows":
                for line in output.split('\n'):
                    if "time=" in line or "time<" in line:
                        if "time=" in line: time_str = line.split("time=")[1].split("ms")[0].strip()
                        else: time_str = '0.5' # time<1ms case
                        try: ping_times.append(float(time_str))
                        except ValueError: continue
            else: # Linux/macOS non-quiet
                for line in output.split('\n'):
                    if "time=" in line and "icmp_seq" in line:
                        time_str = line.split("time=")[1].split(" ms")[0].strip()
                        try: ping_times.append(float(time_str))
                        except ValueError: continue

            if ping_times:
                avg_ping = sum(ping_times) / len(ping_times)
                print(f"  Successfully parsed avg ping (line-by-line fallback): {avg_ping:.2f} ms")
                return {"website": website, "ip_address": target, "avg_ping": avg_ping, "ping_times": ping_times}
            else:
                 print(f"  Could not parse ping times from output for {target}.")
                 # print(f"--- Full Output ---\n{output}\n--- End Output ---") # Uncomment for deep debug
                 return None

        except subprocess.TimeoutExpired:
            print(f"  Ping command timed out for {target} after {timeout_sec * count + 5} seconds.")
            process.kill() # Ensure the process is terminated
            output, error = process.communicate() # Clean up
            return None
        except FileNotFoundError:
             print(f"  Error: 'ping' command not found. Is it installed and in your system's PATH?")
             return None
        except Exception as e:
            print(f"  An unexpected error occurred during ping to {target}: {e}")
            return None

    def get_website_location(self, website):
        """Get PREDEFINED approximate location for a website domain."""
        # Extract base domain (e.g., www.google.com -> google.com)
        parts = website.split('.')
        if len(parts) >= 2:
            base_domain = f"{parts[-2]}.{parts[-1]}"
            # Handle country codes like .co.uk
            if len(parts) >= 3 and len(parts[-2]) == 2 and len(parts[-1]) == 2:
                 base_domain = f"{parts[-3]}.{parts[-2]}.{parts[-1]}"
        else:
            base_domain = website # Cannot simplify further

        # Look up known locations by full name first, then base domain
        if website in self.geo_locations:
            loc = self.geo_locations[website]
            # print(f"  Found direct location for {website}: {loc}")
            return loc
        elif base_domain in self.geo_locations:
            loc = self.geo_locations[base_domain]
            # print(f"  Found base domain location for {website} ({base_domain}): {loc}")
            return loc
        else:
            # Fallback to a default location
            default_loc = self.geo_locations["fallback_default"]
            print(f"  Warning: No predefined location found for {website} or {base_domain}. Using default: {default_loc}")
            return default_loc

    def add_ping_point_to_grid(self, lat, lon, ping_time):
        """Add a ping measurement point to the grid (using minimum)."""
        # Find closest grid indices
        lat_idx = np.abs(self.lat_grid - lat).argmin()
        lon_idx = np.abs(self.lon_grid - lon).argmin()

        # Update ping time at this point, keeping the minimum (best) ping time
        self.ping_grid[lat_idx, lon_idx] = min(self.ping_grid[lat_idx, lon_idx], ping_time)
        # No print here, done in main loop

    def generate_visualization(self, output_file="ping_visualization.png", plot_type='scatter'):
        """Generate visualization from collected ping data."""
        print("\nGenerating visualization...")

        if not self.ping_results_list:
            print("Error: No successful ping data collected. Cannot generate visualization.")
            return

        # --- Setup Map ---
        plt.figure(figsize=(16, 8))
        ax = plt.axes(projection=ccrs.Miller()) # Miller projection is decent for world view
        ax.set_global()

        ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue', zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=1)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5, zorder=1)
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, zorder=2)

        # --- Create Colormap (Green -> Yellow -> Red) ---
        color_list = [
            (0, 1, 0, 1),    # Bright green - low ping
            (1, 1, 0, 1),    # Yellow - medium ping
            (1, 0, 0, 1)     # Deep red - high ping
        ]
        cmap = LinearSegmentedColormap.from_list('ping_cmap', color_list, N=256)

        # --- Extract data for plotting ---
        lats = [p[0] for p in self.ping_results_list]
        lons = [p[1] for p in self.ping_results_list]
        pings = [p[2] for p in self.ping_results_list]
        # websites = [p[3] for p in self.ping_results_list] # Could use for annotations

        if not pings: # Double check after extraction
             print("Error: No valid ping values found in results list.")
             plt.close()
             return

        min_ping = min(pings) if pings else 0
        max_ping = max(pings) if pings else 100 # Avoid division by zero if only one point

        print(f"Plotting {len(pings)} data points.")
        print(f"Ping range: {min_ping:.2f} ms to {max_ping:.2f} ms")

        # --- Choose Plot Type ---
        if plot_type == 'scatter':
            print("Using scatter plot visualization.")
            sc = ax.scatter(
                lons, lats,
                c=pings,
                cmap=cmap,
                vmin=min_ping,
                vmax=max_ping,
                s=60,  # Marker size
                transform=ccrs.PlateCarree(), # IMPORTANT: Data is in Lat/Lon
                edgecolor='black',
                linewidth=0.5,
                zorder=3 # Make sure points are on top
            )
            plt.colorbar(sc, ax=ax, label='Average Ping Latency (ms)', shrink=0.6)
            plt.title(f'Ping Latency to {len(pings)} Websites (Scatter Plot)')

        elif plot_type == 'pcolormesh':
            print("Using pcolormesh plot visualization (may look sparse).")
            # Prepare grid data - use the self.ping_grid updated earlier
            viz_grid = np.copy(self.ping_grid)
            viz_grid[viz_grid >= 1000] = np.nan # Replace placeholder with NaN

            if np.all(np.isnan(viz_grid)):
                 print("Error: All grid data is NaN for pcolormesh.")
                 plt.close()
                 return

            # Get meshgrid for plotting coordinates
            mesh_lons, mesh_lats = np.meshgrid(self.lon_grid, self.lat_grid)

            # Need valid min/max from the grid itself for color scaling
            grid_min_ping = np.nanmin(viz_grid)
            grid_max_ping = np.nanmax(viz_grid)
            print(f"Grid ping range for pcolormesh: {grid_min_ping:.2f} to {grid_max_ping:.2f} ms")

            # Add a small epsilon if min and max are the same
            if grid_min_ping == grid_max_ping:
                 grid_max_ping += 1e-6

            mesh = ax.pcolormesh(
                mesh_lons, mesh_lats,
                viz_grid,
                transform=ccrs.PlateCarree(),
                cmap=cmap,
                vmin=grid_min_ping,
                vmax=grid_max_ping,
                shading='auto', # or 'nearest'/'gouraud' if needed
                zorder=3
            )
            plt.colorbar(mesh, ax=ax, label='Average Ping Latency (ms)', shrink=0.6)
            plt.title(f'Ping Latency Heatmap ({len(pings)} points, pcolormesh)')

        else:
            print(f"Error: Unknown plot_type '{plot_type}'. Choose 'scatter' or 'pcolormesh'.")
            plt.close()
            return

        # --- Finalize and Save ---
        try:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Visualization saved to {output_file}")
            plt.show()
        except Exception as e:
            print(f"Error saving or showing plot: {e}")
        finally:
             plt.close() # Close the plot figure window


    def run_analysis(self, websites, ping_count=4, timeout_sec=5, plot_type='scatter', output_file="ping_visualization.png"):
        """Runs the full ping analysis and generates the visualization."""
        print(f"\n--- Starting Ping Analysis ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
        print(f"Pinging {len(websites)} websites (Count={ping_count}, Timeout={timeout_sec}s each)...")

        # Reset results from any previous runs on this object
        self.ping_grid.fill(1000.0)
        self.ping_results_list = []
        successful_pings = 0

        for i, website in enumerate(websites):
            print(f"\n[{i+1}/{len(websites)}] Pinging {website}...")
            ping_result = self.run_ping(website, count=ping_count, timeout_sec=timeout_sec)

            if ping_result and 'avg_ping' in ping_result:
                successful_pings += 1
                avg_ping = ping_result['avg_ping']
                print(f"  Success! Avg Ping: {avg_ping:.2f} ms")

                # Get location and add to grid and list
                lat, lon = self.get_website_location(website)
                print(f"  Mapped to location (Lat, Lon): ({lat:.4f}, {lon:.4f})")
                self.add_ping_point_to_grid(lat, lon, avg_ping)
                self.ping_results_list.append([lat, lon, avg_ping, website])
            else:
                print(f"  Ping failed or no result for {website}.")

            # Optional small delay between pings to avoid overwhelming network/servers
            # time.sleep(0.2)

        print(f"\n--- Analysis Complete ---")
        print(f"Successfully pinged {successful_pings} out of {len(websites)} websites.")

        # Generate the visualization
        self.generate_visualization(output_file=output_file, plot_type=plot_type)


# --- Main Execution ---
if __name__ == "__main__":
    print("Running Ping Heatmap Script...")
    print("Ensure you have installed required libraries: pip install numpy matplotlib cartopy")
    print("Cartopy may require additional dependencies (like GEOS, PROJ). See Cartopy installation guide.")
    print("Note: Pinging websites can be unreliable. Firewalls often block pings.")
    print("-" * 30)

    # Create the heatmap object
    heatmap = PingHeatmap(resolution=90) # 90x180 grid

    # Define a diverse list of websites to ping
    sites_to_ping = [
        # == Major Global CDNs/Services (High Repeats for Density) ==
        "google.com", "google.com", "google.com", "google.com", "google.com", # ~5
        "google.com", "google.com", # Total 7 google.com
        "cloudflare.com", "cloudflare.com", "cloudflare.com", "cloudflare.com", # ~4
        "cloudflare.com", "cloudflare.com", # Total 6 cloudflare.com
        "facebook.com", "facebook.com", "facebook.com", "facebook.com", # Total 4 facebook.com
        "amazon.com", "amazon.com", "amazon.com", "amazon.com", # Total 4 amazon.com (often AWS)
        "microsoft.com", "microsoft.com", # Total 2 microsoft.com (often Azure)
        "apple.com", "apple.com", "apple.com", # Total 3 apple.com
        "instagram.com", "instagram.com", "instagram.com", # Total 3 instagram.com (Meta)
        "whatsapp.com", # Total 1 whatsapp.com (Meta)
        "live.com", "live.com", # Total 2 live.com (Microsoft)
        "office.com", # Total 1 office.com (Microsoft)
        "bing.com", "bing.com", # Total 2 bing.com (Microsoft)
        "icloud.com", "icloud.com", # Total 2 icloud.com (Apple)

        # == Google Regional TLDs (Diversity + Repeats) ==
        "google.com.au", "google.com.au", "google.com.au", "google.com.au", "google.com.au", # 5x Local AU
        "google.co.uk", "google.co.uk", # UK
        "google.de", "google.de", # Germany
        "google.fr", "google.fr", # France
        "google.ca", "google.ca", # Canada
        "google.co.jp", "google.co.jp", # Japan
        "google.co.in", "google.co.in", # India
        "google.com.br", "google.com.br", # Brazil
        "google.co.za", "google.co.za", # South Africa

        # == Other Popular Global/Tech Sites ==
        "wikipedia.org", # Often Singapore/US/NL
        "x.com", # Formerly twitter.com
        "netflix.com",
        "github.com",
        "yahoo.com",
        "linkedin.com", # Microsoft
        "reddit.com",
        "tiktok.com",
        "zoom.us",
        "ebay.com",
        "wordpress.com",

        # == News Outlets (Global Reach) ==
        "bbc.co.uk", # UK based, global reach
        "cnn.com", # US based, global reach
        "nytimes.com", # US based, global reach
        "theguardian.com", # UK based, global reach

        # == Regional Specific Sites ==
        "mercadolibre.com.ar", # Argentina/South America
        "yandex.ru", # Russia
        "baidu.com", # China
        "alibaba.com", # China
        "rakuten.co.jp", # Japan
        "naver.com", # South Korea
        "qq.com", # China

        # == Australian Focused Sites ==
        "news.com.au",
        "abc.net.au", # Australian Broadcasting Corporation
        "smh.com.au", # Sydney Morning Herald
        "theage.com.au", # The Age (Melbourne)
        "telstra.com.au", # ISP
        "optus.com.au", # ISP
        "seek.com.au", # Job Site
        "realestate.com.au",
        "gov.au", # Australian Government Portal
        "csiro.au", # Australian Science Agency
        "bunnings.com.au", # Retailer
        "woolworths.com.au", # Retailer
        "coles.com.au", # Retailer
        "commbank.com.au", # Bank
        "nab.com.au", # Bank
    ]

    # Run the analysis and generate the scatter plot
    heatmap.run_analysis(
        websites=sites_to_ping,
        ping_count=4,       # Number of pings per site
        timeout_sec=5,      # Timeout per ping reply
        plot_type='scatter', # Use 'scatter' (recommended) or 'pcolormesh'
        output_file="ping_latency_scatter.png"
    )

    # # Example: To generate the pcolormesh heatmap instead (might look very sparse!)
    # print("\nGenerating pcolormesh version (might be sparse)...")
    # heatmap.generate_visualization(output_file="ping_latency_heatmap.png", plot_type='pcolormesh')

    print("-" * 30)
    print("Script finished.")
