#!/usr/bin/env python3
"""
Quick demo script to run the NFS Mount Visualizer with sample data
"""

import streamlit as st
from nfs_mount_visualizer.app import main

if __name__ == "__main__":
    # Run in demo mode with sample data
    main(demo_mode=True)