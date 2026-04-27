#!/usr/bin/env python3
"""
API Cost Monitor and Controller
Track and limit Claude API usage to prevent unexpected costs
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APICostMonitor:
    """Monitor and control API costs with usage limits"""
    
    def __init__(self, cost_limit_usd: float = 10.0, usage_file: str = "api_usage.json"):
        self.cost_limit_usd = cost_limit_usd
        self.usage_file = Path(usage_file)
        self.usage_data = self._load_usage_data()
        
        # Claude pricing (as of 2025 - verify current rates)
        self.pricing = {
            "claude-sonnet-4": {
                "input_per_1k": 0.015,   # $0.015 per 1K input tokens
                "output_per_1k": 0.075   # $0.075 per 1K output tokens
            },
            "claude-haiku": {
                "input_per_1k": 0.00025,
                "output_per_1k": 0.00125
            }
        }
    
    def _load_usage_data(self) -> Dict:
        """Load existing usage data"""
        if self.usage_file.exists():
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "daily_usage": {},
            "session_start": datetime.now().isoformat(),
            "calls_made": 0,
            "failed_calls": 0
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def check_cost_limit(self) -> bool:
        """Check if we're within cost limits"""
        current_cost = self.usage_data["total_cost_usd"]
        if current_cost >= self.cost_limit_usd:
            logger.error(f"❌ COST LIMIT EXCEEDED: ${current_cost:.3f} >= ${self.cost_limit_usd}")
            return False
        
        remaining = self.cost_limit_usd - current_cost
        logger.info(f"💰 Cost status: ${current_cost:.3f} used, ${remaining:.3f} remaining")
        return True
    
    def estimate_call_cost(self, input_tokens: int, estimated_output_tokens: int = 2000) -> float:
        """Estimate cost of an API call"""
        model = "claude-sonnet-4"
        input_cost = (input_tokens / 1000) * self.pricing[model]["input_per_1k"]
        output_cost = (estimated_output_tokens / 1000) * self.pricing[model]["output_per_1k"]
        return input_cost + output_cost
    
    def pre_call_check(self, input_tokens: int, estimated_output_tokens: int = 2000) -> bool:
        """Check if we can afford this call"""
        if not self.check_cost_limit():
            return False
        
        estimated_cost = self.estimate_call_cost(input_tokens, estimated_output_tokens)
        projected_total = self.usage_data["total_cost_usd"] + estimated_cost
        
        if projected_total > self.cost_limit_usd:
            logger.error(f"❌ Call would exceed limit: ${projected_total:.3f} > ${self.cost_limit_usd}")
            return False
        
        logger.info(f"✅ Call approved: ${estimated_cost:.3f} (${projected_total:.3f} total)")
        return True
    
    def record_call(self, input_tokens: int, output_tokens: int, success: bool = True):
        """Record an API call"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.usage_data["daily_usage"]:
            self.usage_data["daily_usage"][today] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "calls": 0,
                "failed_calls": 0
            }
        
        # Calculate cost
        model = "claude-sonnet-4"
        input_cost = (input_tokens / 1000) * self.pricing[model]["input_per_1k"]
        output_cost = (output_tokens / 1000) * self.pricing[model]["output_per_1k"]
        call_cost = input_cost + output_cost
        
        # Update totals
        self.usage_data["total_input_tokens"] += input_tokens
        self.usage_data["total_output_tokens"] += output_tokens
        self.usage_data["total_cost_usd"] += call_cost
        self.usage_data["calls_made"] += 1
        
        # Update daily
        daily = self.usage_data["daily_usage"][today]
        daily["input_tokens"] += input_tokens
        daily["output_tokens"] += output_tokens
        daily["cost"] += call_cost
        daily["calls"] += 1
        
        if not success:
            self.usage_data["failed_calls"] += 1
            daily["failed_calls"] += 1
        
        self._save_usage_data()
        
        logger.info(f"📊 Call recorded: ${call_cost:.3f} ({'✅ success' if success else '❌ failed'})")
        logger.info(f"📈 Session total: ${self.usage_data['total_cost_usd']:.3f}")
    
    def generate_cost_report(self) -> str:
        """Generate detailed cost report"""
        data = self.usage_data
        
        report = f"""# API Cost Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Cost Summary
- **Total Cost:** ${data['total_cost_usd']:.3f}
- **Cost Limit:** ${self.cost_limit_usd:.2f}
- **Remaining Budget:** ${self.cost_limit_usd - data['total_cost_usd']:.3f}
- **Usage:** {(data['total_cost_usd'] / self.cost_limit_usd) * 100:.1f}%

## Token Usage
- **Input Tokens:** {data['total_input_tokens']:,}
- **Output Tokens:** {data['total_output_tokens']:,}
- **Total Tokens:** {data['total_input_tokens'] + data['total_output_tokens']:,}

## Call Statistics
- **Successful Calls:** {data['calls_made'] - data['failed_calls']}
- **Failed Calls:** {data['failed_calls']}
- **Success Rate:** {((data['calls_made'] - data['failed_calls']) / max(data['calls_made'], 1)) * 100:.1f}%
- **Wasted Cost (Failed):** ${(data['failed_calls'] * 0.05):.3f} (estimated)

## Daily Breakdown
"""
        
        for date, daily in sorted(data["daily_usage"].items()):
            report += f"""
### {date}
- Cost: ${daily['cost']:.3f}
- Calls: {daily['calls']} ({daily['failed_calls']} failed)
- Tokens: {daily['input_tokens']:,} in, {daily['output_tokens']:,} out
"""
        
        return report
    
    def reset_usage(self):
        """Reset usage tracking (use carefully!)"""
        self.usage_data = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "daily_usage": {},
            "session_start": datetime.now().isoformat(),
            "calls_made": 0,
            "failed_calls": 0
        }
        self._save_usage_data()
        logger.info("🔄 Usage data reset")

def main():
    """CLI interface for cost monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Cost Monitor")
    parser.add_argument("--limit", type=float, default=10.0, help="Cost limit in USD")
    parser.add_argument("--report", action="store_true", help="Generate cost report")
    parser.add_argument("--reset", action="store_true", help="Reset usage data")
    parser.add_argument("--check", action="store_true", help="Check current status")
    
    args = parser.parse_args()
    
    monitor = APICostMonitor(cost_limit_usd=args.limit)
    
    if args.reset:
        monitor.reset_usage()
    elif args.report:
        report = monitor.generate_cost_report()
        print(report)
        
        # Save report
        report_file = Path("api_cost_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
    elif args.check:
        monitor.check_cost_limit()
        print(f"Total calls: {monitor.usage_data['calls_made']}")
        print(f"Failed calls: {monitor.usage_data['failed_calls']}")
    else:
        print("Use --report, --check, or --reset")

if __name__ == "__main__":
    main()