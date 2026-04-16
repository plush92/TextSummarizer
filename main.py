#!/usr/bin/env python3
"""
Text Summarizer CLI Tool

A command-line interface for summarizing text using AI models.
Accepts input from files or stdin and generates structured summaries.
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from summarizer import TextSummarizer
from config import Config


def read_input_text(args):
    """Read text from file or stdin"""
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    
    elif args.text:
        return args.text
    
    else:
        print("Reading from stdin... (Press Ctrl+D when finished)")
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(0)


def save_output(summary_data, output_file=None):
    """Save summary output to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not output_file:
        output_file = f"summary_{timestamp}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("TEXT SUMMARY REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("📝 SHORT SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"{summary_data['summary']}\n\n")
            
            f.write("🔑 KEY POINTS\n")
            f.write("-" * 15 + "\n")
            for i, point in enumerate(summary_data['key_points'], 1):
                f.write(f"{i}. {point}\n")
            f.write("\n")
            
            f.write("✅ ACTION ITEMS\n")
            f.write("-" * 17 + "\n")
            for i, action in enumerate(summary_data['action_items'], 1):
                f.write(f"{i}. {action}\n")
        
        return output_file
    except Exception as e:
        print(f"Error saving output: {e}")
        return None


def display_output(summary_data):
    """Display summary output to console"""
    print("\n" + "=" * 60)
    print("📝 SHORT SUMMARY")
    print("-" * 20)
    print(summary_data['summary'])
    
    print(f"\n🔑 KEY POINTS")
    print("-" * 15)
    for i, point in enumerate(summary_data['key_points'], 1):
        print(f"{i}. {point}")
    
    print(f"\n✅ ACTION ITEMS")
    print("-" * 17)
    for i, action in enumerate(summary_data['action_items'], 1):
        print(f"{i}. {action}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Summarize text using AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file document.txt --output summary.txt
  %(prog)s --text "Your text here" --no-save
  echo "Text content" | %(prog)s
  %(prog)s < input.txt --output results.txt
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '--file', '-f',
        help='Input text file to summarize'
    )
    input_group.add_argument(
        '--text', '-t',
        help='Direct text input to summarize'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: auto-generated filename)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Display results only, do not save to file'
    )
    
    # Model options
    parser.add_argument(
        '--model',
        choices=['openai', 'anthropic', 'local'],
        default='openai',
        help='AI model to use (default: openai)'
    )
    parser.add_argument(
        '--max-length',
        type=int,
        default=150,
        help='Maximum length for summary (default: 150 words)'
    )
    
    # Other options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Run interactive configuration setup'
    )
    
    args = parser.parse_args()
    
    # Handle setup mode
    if args.setup:
        from config import setup_config
        setup_config()
        sys.exit(0)
    
    # Read input text
    if args.verbose:
        print("Reading input text...")
    
    text = read_input_text(args)
    
    if not text.strip():
        print("Error: No input text provided.")
        sys.exit(1)
    
    # Initialize summarizer
    try:
        config = Config()
        summarizer = TextSummarizer(
            model_type=args.model,
            config=config,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"Error initializing summarizer: {e}")
        sys.exit(1)
    
    # Generate summary
    if args.verbose:
        print("Generating summary...")
    
    try:
        summary_data = summarizer.summarize(
            text, 
            max_length=args.max_length
        )
    except Exception as e:
        print(f"Error generating summary: {e}")
        sys.exit(1)
    
    # Display results
    display_output(summary_data)
    
    # Save results
    if not args.no_save:
        if args.verbose:
            print("\nSaving output...")
        
        output_file = save_output(summary_data, args.output)
        if output_file:
            print(f"\n💾 Summary saved to: {output_file}")
        else:
            print("\n❌ Failed to save summary")
    
    if args.verbose:
        print("\n✨ Done!")


if __name__ == "__main__":
    main()