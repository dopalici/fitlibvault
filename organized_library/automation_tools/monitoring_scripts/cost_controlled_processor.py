#!/usr/bin/env python3
"""
Cost-Controlled Fitness Library Processor
Processes files with strict cost controls and optimized token usage
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional
import anthropic
import logging

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
from api_cost_monitor import APICostMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CostControlledProcessor:
    """Process fitness library files with strict cost controls"""
    
    def __init__(self, api_key: str, cost_limit: float = 5.0):
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cost_monitor = APICostMonitor(cost_limit_usd=cost_limit)
        
        # Ultra-minimal template for maximum efficiency
        self.minimal_template = """Enhance fitness note. Keep title/ID unchanged.

{title}
{content}

Add: Quick takeaway, 3 key points, research with DOI/PMID links, practical use.
Enhanced format required. Max efficient response."""
    
    def count_tokens(self, text: str) -> int:
        """Rough token count estimation"""
        return len(text.split()) * 1.3  # Conservative estimate
    
    def process_file_with_cost_control(self, file_path: Path, max_output_tokens: int = 1500) -> Optional[str]:
        """Process single file with cost controls"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title and core content
            title = self._extract_title(content)
            core_content = self._extract_minimal_content(content)
            
            # Create minimal prompt
            prompt = self.minimal_template.format(
                title=title,
                content=core_content[:1000]  # Limit content to 1000 chars
            )
            
            input_tokens = self.count_tokens(prompt)
            
            # Pre-call cost check
            if not self.cost_monitor.pre_call_check(int(input_tokens), max_output_tokens):
                logger.error(f"❌ Skipping {file_path.name} - would exceed cost limit")
                return None
            
            logger.info(f"🔄 Processing {file_path.name} (est. {input_tokens:.0f} input tokens)")
            
            # Make API call
            start_time = time.time()
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_output_tokens,  # Reduced from 4000 to 1500
                temperature=0.3,  # Lower temperature for efficiency
                messages=[{"role": "user", "content": prompt}]
            )
            
            call_duration = time.time() - start_time
            
            # Extract response
            enhanced_content = response.content[0].text
            output_tokens = self.count_tokens(enhanced_content)
            
            # Record the call
            self.cost_monitor.record_call(
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                success=True
            )
            
            logger.info(f"✅ Processed {file_path.name} in {call_duration:.1f}s")
            logger.info(f"📊 Tokens: {input_tokens:.0f} in, {output_tokens:.0f} out")
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            
            # Record failed call
            estimated_input = self.count_tokens(prompt) if 'prompt' in locals() else 1000
            self.cost_monitor.record_call(
                input_tokens=int(estimated_input),
                output_tokens=0,
                success=False
            )
            return None
    
    def _extract_title(self, content: str) -> str:
        """Extract title from content"""
        import re
        match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else "Unknown Title"
    
    def _extract_minimal_content(self, content: str) -> str:
        """Extract only essential content"""
        lines = content.split('\n')
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('#') and 
                not line.startswith('**ID:**') and
                not line.startswith('**Created:**') and
                not line.startswith('**Links:**')):
                content_lines.append(line)
        
        return '\n'.join(content_lines[:5])  # Only first 5 substantial lines
    
    def batch_process_with_limits(self, files: list, output_dir: Path, 
                                 max_files: int = 10, max_cost: float = 2.0) -> dict:
        """Process files with strict limits"""
        
        logger.info(f"🎯 Starting cost-controlled batch processing")
        logger.info(f"📊 Limits: {max_files} files, ${max_cost} budget")
        
        output_dir.mkdir(exist_ok=True)
        results = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "cost_limit_reached": False
        }
        
        for i, file_path in enumerate(files[:max_files]):
            # Check cost limit before each file
            if self.cost_monitor.usage_data["total_cost_usd"] >= max_cost:
                logger.warning(f"💰 Cost limit ${max_cost} reached. Stopping.")
                results["cost_limit_reached"] = True
                break
            
            logger.info(f"📋 Processing file {i+1}/{min(len(files), max_files)}: {file_path.name}")
            
            enhanced_content = self.process_file_with_cost_control(file_path)
            
            if enhanced_content:
                # Save result
                output_file = output_dir / f"rewritten_{file_path.name}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(enhanced_content)
                
                results["processed"] += 1
                logger.info(f"✅ Saved: {output_file}")
            else:
                results["failed"] += 1
            
            # Brief pause between calls
            time.sleep(2)
            
            # Status update
            current_cost = self.cost_monitor.usage_data["total_cost_usd"]
            logger.info(f"💰 Session cost: ${current_cost:.3f}")
        
        return results

def main():
    """CLI interface with cost controls"""
    parser = argparse.ArgumentParser(description="Cost-Controlled Fitness Library Processor")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--section", default="B", help="Section to process")
    parser.add_argument("--start-num", type=int, default=42, help="Start number")
    parser.add_argument("--end-num", type=int, default=48, help="End number")
    parser.add_argument("--cost-limit", type=float, default=2.0, help="Maximum cost in USD")
    parser.add_argument("--max-files", type=int, default=10, help="Maximum files to process")
    parser.add_argument("--output-dir", default="processed_notes", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Estimate costs without processing")
    
    args = parser.parse_args()
    
    # Find files to process
    base_dir = Path(".")
    if (Path(__file__).parent.parent / f"{args.section}{args.start_num}. ").exists():
        base_dir = Path(__file__).parent.parent
    
    files = []
    for num in range(args.start_num, args.end_num + 1):
        pattern = f"{args.section}{num}. *.md"
        found_files = list(base_dir.glob(pattern))
        files.extend(found_files)
    
    if not files:
        logger.error(f"❌ No files found for {args.section}{args.start_num}-{args.end_num}")
        return
    
    logger.info(f"📁 Found {len(files)} files to process")
    
    if args.dry_run:
        processor = CostControlledProcessor(args.api_key, args.cost_limit)
        total_estimated_cost = 0
        
        for file_path in files[:args.max_files]:
            with open(file_path, 'r') as f:
                content = f.read()
            estimated_tokens = processor.count_tokens(content[:2000])  # Sample
            estimated_cost = processor.cost_monitor.estimate_call_cost(int(estimated_tokens))
            total_estimated_cost += estimated_cost
            
            print(f"{file_path.name}: ~${estimated_cost:.3f}")
        
        print(f"\nTotal estimated cost: ${total_estimated_cost:.3f}")
        print(f"Within budget: {'✅' if total_estimated_cost <= args.cost_limit else '❌'}")
        return
    
    # Process files with cost control
    processor = CostControlledProcessor(args.api_key, args.cost_limit)
    output_dir = Path(args.output_dir)
    
    results = processor.batch_process_with_limits(
        files, output_dir, args.max_files, args.cost_limit
    )
    
    # Final report
    final_cost = processor.cost_monitor.usage_data["total_cost_usd"]
    
    print(f"""
🏁 COST-CONTROLLED PROCESSING COMPLETE
💰 Total Cost: ${final_cost:.3f} / ${args.cost_limit:.2f}
✅ Processed: {results['processed']} files
❌ Failed: {results['failed']} files
⏭️ Skipped: {results['skipped']} files
🛑 Cost Limit Reached: {'Yes' if results['cost_limit_reached'] else 'No'}
    """)
    
    # Generate cost report
    cost_report = processor.cost_monitor.generate_cost_report()
    report_file = Path("cost_controlled_report.md")
    with open(report_file, 'w') as f:
        f.write(cost_report)
    print(f"📊 Cost report saved: {report_file}")

if __name__ == "__main__":
    main()