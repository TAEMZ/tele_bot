"""
Telegram Bot Stress Testing Framework
Tests concurrent user load and generates performance report
"""
import asyncio
import time
import random
import statistics
from datetime import datetime
from typing import List, Dict
import psutil
import requests
from telebot import TeleBot
import matplotlib.pyplot as plt
from collections import defaultdict

# Configuration
BOT_TOKEN = "7962443530:AAHH6mdIexuTKw9J2Js0SMtwJ5Jtfe8yNe8"
TEST_DURATION = 300  # 5 minutes per test
COOLDOWN_PERIOD = 120  # 2 minutes between tests

# Test messages in Amharic and Oromo
AMHARIC_MESSAGES = [
    "ሰላም",
    "ራስ ምታት አለብኝ",
    "ስለ ማርበርግ ቫይረስ ምን ታውቃለህ?",
    "ጤና ይስጥልኝ እንዴት ነህ?",
    "የሆድ ህመም ምን ማድረግ አለብኝ?",
]

OROMO_MESSAGES = [
    "Akkam jirta",
    "Dhukkuba mataa qaba",
    "Waa'ee Marburg virus maal beekta?",
    "Nagaa, akkam jirta?",
    "Dhukkuba garaa yoo na qabe maal godha?",
]

class StressTestMetrics:
    """Track performance metrics during stress tests"""
    
    def __init__(self):
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.cpu_usage = []
        self.ram_usage = []
        self.language_times = defaultdict(list)
        self.start_time = None
        self.end_time = None
    
    def add_response(self, response_time: float, success: bool, language: str):
        """Record a response"""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.language_times[language].append(response_time)
    
    def record_system_metrics(self):
        """Record CPU and RAM usage"""
        self.cpu_usage.append(psutil.cpu_percent(interval=1))
        self.ram_usage.append(psutil.virtual_memory().percent)
    
    def get_stats(self) -> Dict:
        """Calculate statistics"""
        if not self.response_times:
            return {}
        
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(statistics.mean(self.response_times), 2),
            "min_response_time": round(min(self.response_times), 2),
            "max_response_time": round(max(self.response_times), 2),
            "median_response_time": round(statistics.median(self.response_times), 2),
            "avg_cpu": round(statistics.mean(self.cpu_usage), 2) if self.cpu_usage else 0,
            "avg_ram": round(statistics.mean(self.ram_usage), 2) if self.ram_usage else 0,
            "amharic_avg": round(statistics.mean(self.language_times['am']), 2) if self.language_times['am'] else 0,
            "oromo_avg": round(statistics.mean(self.language_times['om']), 2) if self.language_times['om'] else 0,
        }

class BotStressTester:
    """Main stress testing class"""
    
    def __init__(self, bot_token: str):
        self.bot = TeleBot(bot_token)
        self.test_results = {}
    
    async def simulate_user(self, user_id: int, duration: int, metrics: StressTestMetrics):
        """Simulate a single user sending messages via direct API"""
        end_time = time.time() + duration
        api_url = "http://89.58.28.152:8001/test_chat"
        
        while time.time() < end_time:
            # Randomly choose language
            language = random.choice(['am', 'om'])
            if language == 'am':
                message = random.choice(AMHARIC_MESSAGES)
            else:
                message = random.choice(OROMO_MESSAGES)
            
            # Send message and measure response time
            start = time.time()
            try:
                # Real API call to the bot
                payload = {
                    "text": message,
                    "language": language,
                    "user_id": f"stress_test_{user_id}"
                }
                
                # Use run_in_executor for synchronous requests
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(api_url, json=payload, timeout=100)
                )
                
                if response.status_code == 200:
                    response_time = time.time() - start
                    metrics.add_response(response_time, True, language)
                else:
                    print(f"User {user_id} API error: {response.status_code} - {response.text}")
                    response_time = time.time() - start
                    metrics.add_response(response_time, False, language)
                
            except Exception as e:
                response_time = time.time() - start
                metrics.add_response(response_time, False, language)
                print(f"User {user_id} connection error: {e}")
            
            # Wait before next message (random interval)
            await asyncio.sleep(random.uniform(2, 5))
    
    async def run_test(self, num_users: int, duration: int, test_name: str) -> StressTestMetrics:
        """Run a stress test with specified number of concurrent users"""
        print(f"\n{'='*60}")
        print(f"Starting {test_name}: {num_users} concurrent users")
        print(f"Duration: {duration} seconds")
        print(f"{'='*60}\n")
        
        metrics = StressTestMetrics()
        metrics.start_time = datetime.now()
        
        # Start system monitoring in background
        async def monitor_system():
            while time.time() < metrics.start_time.timestamp() + duration:
                metrics.record_system_metrics()
                await asyncio.sleep(5)  # Record every 5 seconds
        
        # Create tasks for all users + system monitor
        tasks = [
            self.simulate_user(i, duration, metrics)
            for i in range(num_users)
        ]
        tasks.append(monitor_system())
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        
        metrics.end_time = datetime.now()
        
        # Print immediate results
        stats = metrics.get_stats()
        print(f"\n{test_name} Results:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Success rate: {stats['success_rate']}%")
        print(f"  Avg response time: {stats['avg_response_time']}s")
        print(f"  CPU usage: {stats['avg_cpu']}%")
        print(f"  RAM usage: {stats['avg_ram']}%")
        
        return metrics
    
    async def run_spike_test(self) -> StressTestMetrics:
        """Sudden spike from 10 to 100 users"""
        print(f"\n{'='*60}")
        print("Starting SPIKE TEST: 10 → 100 users")
        print(f"{'='*60}\n")
        
        metrics = StressTestMetrics()
        metrics.start_time = datetime.now()
        
        # Start with 10 users
        tasks = [self.simulate_user(i, 60, metrics) for i in range(10)]
        
        # After 30 seconds, add 90 more users
        async def add_spike_users():
            await asyncio.sleep(30)
            print("⚡ SPIKE: Adding 90 more users!")
            new_tasks = [self.simulate_user(i, 30, metrics) for i in range(10, 100)]
            await asyncio.gather(*new_tasks)
        
        tasks.append(add_spike_users())
        await asyncio.gather(*tasks)
        
        metrics.end_time = datetime.now()
        return metrics
    
    def generate_report(self, all_results: Dict[str, StressTestMetrics]):
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("TELEGRAM BOT STRESS TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 80)
        
        # Find breaking point (where response time > 10s)
        breaking_point = None
        for test_name, metrics in all_results.items():
            stats = metrics.get_stats()
            if stats.get('avg_response_time', 0) > 10:
                breaking_point = test_name
                break
        
        if breaking_point:
            report.append(f"⚠️  System struggles at: {breaking_point}")
        else:
            report.append("✅ System handled all test loads successfully")
        
        report.append("")
        
        # Detailed Results
        report.append("TEST RESULTS")
        report.append("-" * 80)
        
        for test_name, metrics in all_results.items():
            stats = metrics.get_stats()
            report.append(f"\n{test_name}:")
            report.append(f"  Average response time: {stats['avg_response_time']}s")
            report.append(f"  CPU usage: {stats['avg_cpu']}%")
            report.append(f"  RAM usage: {stats['avg_ram']}%")
            report.append(f"  Success rate: {stats['success_rate']}%")
            report.append(f"  Total requests: {stats['total_requests']}")
        
        # Language Comparison
        report.append("\n" + "-" * 80)
        report.append("LANGUAGE COMPARISON")
        report.append("-" * 80)
        
        # Average across all tests
        all_amharic = []
        all_oromo = []
        for metrics in all_results.values():
            all_amharic.extend(metrics.language_times['am'])
            all_oromo.extend(metrics.language_times['om'])
        
        if all_amharic and all_oromo:
            am_avg = statistics.mean(all_amharic)
            om_avg = statistics.mean(all_oromo)
            diff = abs(am_avg - om_avg) / max(am_avg, om_avg) * 100
            
            report.append(f"Amharic average response time: {am_avg:.2f}s")
            report.append(f"Oromo average response time: {om_avg:.2f}s")
            report.append(f"Difference: {diff:.2f}%")
        
        # Recommendations
        report.append("\n" + "-" * 80)
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        
        # Find safe capacity (where response time < 5s)
        safe_capacity = 0
        for test_name, metrics in all_results.items():
            stats = metrics.get_stats()
            if stats.get('avg_response_time', 0) < 5:
                # Extract number from test name
                import re
                match = re.search(r'(\d+)', test_name)
                if match:
                    safe_capacity = int(match.group(1))
        
        report.append(f"✅ Safe operating capacity: {safe_capacity} concurrent users")
        report.append(f"⚠️  Consider scaling at: {int(safe_capacity * 0.8)} users")
        report.append("")
        
        # Save report
        report_text = "\n".join(report)
        with open("stress_test_report.txt", "w", encoding="utf-8") as f:
            f.write(report_text)
        
        print("\n" + report_text)
        return report_text
    
    def generate_charts(self, all_results: Dict[str, StressTestMetrics]):
        """Generate performance charts"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Extract data
        test_names = []
        avg_times = []
        cpu_usages = []
        ram_usages = []
        
        for test_name, metrics in all_results.items():
            stats = metrics.get_stats()
            test_names.append(test_name)
            avg_times.append(stats['avg_response_time'])
            cpu_usages.append(stats['avg_cpu'])
            ram_usages.append(stats['avg_ram'])
        
        # Chart 1: Response Time vs Users
        ax1.plot(test_names, avg_times, marker='o', linewidth=2, markersize=8)
        ax1.set_title('Response Time vs Concurrent Users', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Test Scenario')
        ax1.set_ylabel('Avg Response Time (seconds)')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=10, color='r', linestyle='--', label='10s threshold')
        ax1.legend()
        
        # Chart 2: CPU Usage
        ax2.plot(test_names, cpu_usages, marker='s', color='orange', linewidth=2, markersize=8)
        ax2.set_title('CPU Usage', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Test Scenario')
        ax2.set_ylabel('CPU Usage (%)')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=90, color='r', linestyle='--', label='90% threshold')
        ax2.legend()
        
        # Chart 3: RAM Usage
        ax3.plot(test_names, ram_usages, marker='^', color='green', linewidth=2, markersize=8)
        ax3.set_title('RAM Usage', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Test Scenario')
        ax3.set_ylabel('RAM Usage (%)')
        ax3.grid(True, alpha=0.3)
        
        # Chart 4: Success Rate
        success_rates = [all_results[name].get_stats()['success_rate'] for name in test_names]
        ax4.bar(test_names, success_rates, color='skyblue')
        ax4.set_title('Success Rate', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Test Scenario')
        ax4.set_ylabel('Success Rate (%)')
        ax4.set_ylim(0, 105)
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('stress_test_charts.png', dpi=300, bbox_inches='tight')
        print("\n✅ Charts saved to: stress_test_charts.png")
        plt.close()

async def main():
    """Run all stress tests"""
    tester = BotStressTester(BOT_TOKEN)
    all_results = {}
    
    print("\n🚀 TELEGRAM BOT STRESS TESTING")
    print("=" * 80)
    print("This will run multiple tests to find the bot's capacity")
    print("Total estimated time: ~1 hour")
    print("=" * 80)
    
    # Test 1: Baseline (10 users)
    metrics = await tester.run_test(10, TEST_DURATION, "Test 1: Baseline (10 users)")
    all_results["Test 1 (10 users)"] = metrics
    
    print(f"\n⏸️  Cooling down for {COOLDOWN_PERIOD} seconds...")
    await asyncio.sleep(COOLDOWN_PERIOD)
    
    # Test 2: Normal Load (50 users)
    metrics = await tester.run_test(50, TEST_DURATION, "Test 2: Normal Load (50 users)")
    all_results["Test 2 (50 users)"] = metrics
    
    print(f"\n⏸️  Cooling down for {COOLDOWN_PERIOD} seconds...")
    await asyncio.sleep(COOLDOWN_PERIOD)
    
    # Test 3: High Load (100 users)
    metrics = await tester.run_test(100, TEST_DURATION, "Test 3: High Load (100 users)")
    all_results["Test 3 (100 users)"] = metrics
    
    print(f"\n⏸️  Cooling down for {COOLDOWN_PERIOD} seconds...")
    await asyncio.sleep(COOLDOWN_PERIOD)
    
    # Test 4: Maximum Capacity (start at 150, increase by 50)
    for num_users in [150, 200, 250]:
        metrics = await tester.run_test(num_users, TEST_DURATION, f"Test 4: Max Capacity ({num_users} users)")
        all_results[f"Test 4 ({num_users} users)"] = metrics
        
        # Check if we hit breaking point
        stats = metrics.get_stats()
        if stats['avg_response_time'] > 10:
            print(f"\n⚠️  Breaking point found at {num_users} users!")
            break
        
        print(f"\n⏸️  Cooling down for {COOLDOWN_PERIOD} seconds...")
        await asyncio.sleep(COOLDOWN_PERIOD)
    
    # Test 5: Spike Test
    print(f"\n⏸️  Cooling down for {COOLDOWN_PERIOD} seconds...")
    await asyncio.sleep(COOLDOWN_PERIOD)
    
    metrics = await tester.run_spike_test()
    all_results["Test 5: Spike Test"] = metrics
    
    # Generate reports
    print("\n\n📊 Generating final report...")
    tester.generate_report(all_results)
    tester.generate_charts(all_results)
    
    print("\n✅ Stress testing complete!")
    print("📄 Report saved to: stress_test_report.txt")
    print("📊 Charts saved to: stress_test_charts.png")

if __name__ == "__main__":
    asyncio.run(main())
