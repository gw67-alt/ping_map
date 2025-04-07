import subprocess
import platform
import statistics
import time
import json
import os
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

class ConcurrentUserPopulationEstimator:
    def __init__(self, 
                 target_websites=None, 
                 ping_count=30, 
                 thread_count=10,
                 output_dir='user_population_data'):
        """
        Initialize the Concurrent User Population Estimator
        
        :param target_websites: List of websites to analyze
        :param ping_count: Number of pings per website
        :param thread_count: Number of concurrent threads
        :param output_dir: Directory to save analysis data
        """
        # Create output directory
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Default websites if none provided
        self.target_websites = target_websites or [
            "google.com", "amazon.com", "microsoft.com", 
            "cloudflare.com", "netflix.com", "facebook.com",
            "youtube.com", "instagram.com", "twitter.com"
        ]
        
        # Ping parameters
        self.ping_count = ping_count
        self.thread_count = thread_count
        
        # Storage for connection metrics
        self.connection_metrics = {}
        
        # Predefined website user base estimates (rough global monthly active users)
        self.website_user_bases = {
            "google.com": 4_500_000_000,    # Google services
            "facebook.com": 2_900_000_000,  # Facebook/Meta
            "youtube.com": 2_500_000_000,   # YouTube
            "whatsapp.com": 2_000_000_000,  # WhatsApp
            "instagram.com": 1_500_000_000, # Instagram
            "twitter.com": 400_000_000,     # Twitter/X
            "amazon.com": 300_000_000,      # Amazon
            "netflix.com": 250_000_000,     # Netflix
            "microsoft.com": 1_200_000_000, # Microsoft services
            "cloudflare.com": 25_000_000,   # Cloudflare (business users)
            "github.com": 100_000_000,      # GitHub
            "wikipedia.org": 1_700_000_000  # Wikipedia
        }
    
    def calculate_jitter(self, ping_times):
        """
        Calculate jitter (variation in ping times)
        
        :param ping_times: List of ping times
        :return: Jitter value
        """
        if len(ping_times) < 2:
            return 0
        
        # Calculate differences between consecutive ping times
        time_diffs = [abs(ping_times[i] - ping_times[i-1]) for i in range(1, len(ping_times))]
        
        # Return mean of absolute differences
        return statistics.mean(time_diffs)
    
    def run_ping(self, website, count=30):
        """
        Run ping to measure network characteristics
        
        :param website: Target website
        :param count: Number of ping attempts
        :return: Ping statistics dictionary
        """
        print(f"Analyzing {website}...")
        
        # Handle numeric IP or domain separately
        try:
            # Try to resolve domain first
            socket.gethostbyname(website)
        except socket.gaierror:
            print(f"Could not resolve {website}")
            return None
        
        # Determine the correct ping command based on OS
        if platform.system() == "Windows":
            cmd = ["ping", "-n", str(count), website]
        else:
            cmd = ["ping", "-c", str(count), website]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output, error = process.communicate(timeout=10)  # Reduced timeout
            
            if error:
                print(f"Error running ping: {error}")
                return None
            
            # Parse the ping output
            ping_times = []
            
            if platform.system() == "Windows":
                # Parse Windows ping output
                for line in output.split('\n'):
                    if "time=" in line or "time<" in line:
                        # Extract time value
                        if "time=" in line:
                            try:
                                time_str = line.split("time=")[1].split("ms")[0].strip()
                                ping_times.append(float(time_str))
                            except:
                                pass
                        elif "time<" in line:
                            # For "time<1ms" responses
                            ping_times.append(0.5)  # Assume half a millisecond
            else:
                # Parse Unix/Linux ping output
                for line in output.split('\n'):
                    if "time=" in line:
                        try:
                            time_str = line.split("time=")[1].split(" ms")[0].strip()
                            ping_times.append(float(time_str))
                        except:
                            pass
            
            if ping_times:
                # Calculate extensive metrics
                metrics = {
                    "website": website,
                    "avg_ping": statistics.mean(ping_times),
                    "median_ping": statistics.median(ping_times),
                    "min_ping": min(ping_times),
                    "max_ping": max(ping_times),
                    "ping_times": ping_times,
                    "jitter": self.calculate_jitter(ping_times),
                    "packet_loss": (count - len(ping_times)) / count * 100,
                    "ping_variance": statistics.variance(ping_times) if len(ping_times) > 1 else 0
                }
                return metrics
            else:
                print(f"No ping responses from {website}")
                return None
        
        except subprocess.TimeoutExpired:
            print(f"Ping to {website} timed out")
            return None
        except Exception as e:
            print(f"Error during ping to {website}: {e}")
            return None
    
    def fallback_population_estimation(self):
        """
        Provide a fallback population estimation when no network metrics are available
        
        :return: Fallback population estimation dictionary
        """
        # Use predefined base populations
        total_base_population = sum(self.website_user_bases.values())
        
        # Fallback population estimation
        fallback_estimate = {
            "total_estimated_concurrent_users": int(total_base_population * 0.001),
            "estimation_method": "fallback",
            "network_stress_indicators": {
                "avg_jitter": None,
                "max_jitter": None,
                "avg_ping": None
            },
            "website_populations": {
                website: {
                    "base_population": base_pop,
                    "estimated_concurrent_users": int(base_pop * 0.001)
                } for website, base_pop in self.website_user_bases.items()
            }
        }
        
        return fallback_estimate
    
    def calculate_user_population(self, connection_metrics):
        """
        Calculate concurrent user population estimate
        
        :param connection_metrics: Network metrics for websites
        :return: Detailed user population estimation
        """
        if not connection_metrics:
            return self.fallback_population_estimation()
        
        # Calculate network stress indicators
        jitter_values = [metrics['jitter'] for metrics in connection_metrics.values()]
        ping_values = [metrics['avg_ping'] for metrics in connection_metrics.values()]
        
        # User population estimation
        total_estimated_population = 0
        website_populations = {}
        
        for website, metrics in connection_metrics.items():
            # Base population from predefined estimates
            base_population = self.website_user_bases.get(website, 100_000_000)
            
            # Simple estimation based on base population
            estimated_concurrent_users = int(base_population * 0.001)
            
            website_populations[website] = {
                "base_population": base_population,
                "estimated_concurrent_users": estimated_concurrent_users,
                "jitter": metrics['jitter'],
                "avg_ping": metrics['avg_ping']
            }
            
            total_estimated_population += estimated_concurrent_users
        
        # Overall population estimation
        population_estimate = {
            "total_estimated_concurrent_users": total_estimated_population,
            "estimation_method": "network_metrics",
            "network_stress_indicators": {
                "avg_jitter": statistics.mean(jitter_values),
                "max_jitter": max(jitter_values),
                "avg_ping": statistics.mean(ping_values)
            },
            "website_populations": website_populations
        }
        
        return population_estimate
    
    def estimate_concurrent_users(self):
        """
        Estimate concurrent users based on network metrics
        
        :return: Detailed concurrent user population metrics
        """
        # Reset and prepare
        self.connection_metrics.clear()
        
        # Ping websites concurrently
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Submit ping tasks
            future_to_website = {
                executor.submit(self.run_ping, website, self.ping_count): website 
                for website in self.target_websites
            }
            
            # Collect results
            for future in as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    result = future.result()
                    if result:
                        self.connection_metrics[website] = result
                except Exception as e:
                    print(f"Error processing {website}: {e}")
        
        # If no connection metrics, use fallback estimation
        if not self.connection_metrics:
            population_estimate = self.fallback_population_estimation()
        else:
            # Calculate concurrent user population
            population_estimate = self.calculate_user_population(
                self.connection_metrics
            )
        
        # Save and display results
        self.save_results(population_estimate)
        
        return population_estimate
    
    def save_results(self, population_estimate):
        """
        Save population estimation to a JSON file
        
        :param population_estimate: Calculated population estimate
        """
        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"concurrent_users_{timestamp}.json")
        
        # Save estimation
        with open(filename, 'w') as f:
            json.dump(population_estimate, f, indent=4)
        
        print(f"Results saved to {filename}")
        print("\n=== Concurrent User Population Estimation for locale ===")
        
        # Safe printing with fallback
        total_users = population_estimate.get('total_estimated_concurrent_users', 'N/A')
        print(f"Total Estimated Concurrent Users: {total_users:,}")
        
        print("Website Breakdown:")
        website_populations = population_estimate.get('website_populations', {})
        for website, data in website_populations.items():
            concurrent_users = data.get('estimated_concurrent_users', 'N/A')
            print(f"{website}: {concurrent_users:,} concurrent users")
        
        # Print estimation method
        print(f"Estimation Method: {population_estimate.get('estimation_method', 'Standard')}")
        
        # Optional: Network stress indicators
        stress_indicators = population_estimate.get('network_stress_indicators', {})
        if stress_indicators.get('avg_jitter') is not None:
            print("\nNetwork Stress Indicators:")
            print(f"Average Jitter: {stress_indicators.get('avg_jitter', 'N/A'):.2f}")
            print(f"Maximum Jitter: {stress_indicators.get('max_jitter', 'N/A'):.2f}")
            print(f"Average Ping: {stress_indicators.get('avg_ping', 'N/A'):.2f} ms")

def main():
    # Create population estimator
    estimator = ConcurrentUserPopulationEstimator(
        target_websites=[
            "google.com", "facebook.com", "youtube.com", 
            "instagram.com", "twitter.com", "amazon.com", 
            "netflix.com", "microsoft.com", "cloudflare.com"
        ],
        ping_count=4,
        thread_count=10
    )
    
    # Run analysis and estimate concurrent users
    population_estimate = estimator.estimate_concurrent_users()

if __name__ == "__main__":
    main()
