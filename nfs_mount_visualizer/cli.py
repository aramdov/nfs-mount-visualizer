#!/usr/bin/env python3
"""
Command-line interface for the NFS Mount Visualizer
"""

import argparse
import os
import sys
from nfs_mount_visualizer.app import main

def run():
    """Entry point for the CLI"""
    parser = argparse.ArgumentParser(description="NFS Mount Visualizer")
    parser.add_argument("--config", type=str, help="Path to configuration file (JSON or YAML)")
    args = parser.parse_args()
    
    main(args.config)

if __name__ == "__main__":
    run()