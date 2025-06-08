#!/usr/bin/env python3
"""
NFS Mount Relationship Visualizer
Creates an interactive visualization of NFS mounts between cluster nodes using Prometheus data
"""

import streamlit as st
import requests
import pandas as pd
from pyvis.network import Network
import time
from datetime import datetime, timedelta
import os
import json
import yaml
import argparse
import random
import numpy as np

# Streamlit app setup
def setup_page(title="NFS Mount Visualizer"):
    """Set up the Streamlit page configuration"""
    st.set_page_config(
        page_title=title,
        page_icon="🔄",
        layout="wide",
    )

def load_config(config_path=None):
    """Load configuration from file or use defaults"""
    default_config = {
        "prometheus_url": "http://localhost:9090",
        "cluster_nodes": ["node1", "node2", "node3"],
        "refresh_interval": 300,  # seconds
        "cache_dir": ".cache",
        "node_types": {
            "default": {"color": "#607D8B", "title": "Cluster Node"}
        },
        "app_title": "NFS Mount Visualizer",
        "metric_name": "nfs_mount_accessible",
        "metric_mapping": {
            "server_label": "source_node",
            "client_label": "target_node", 
            "path_label": "mount_path",
            "mount_path_prefix": "/mnt/"
        },
        "visualization": {
            "network": {
                "height": "700px",
                "width": "100%",
                "bgcolor": "#222222",
                "font_color": "white"
            },
            "edge_colors": {
                "accessible": "#4CAF50",
                "inaccessible": "#F44336"
            },
            "node_sizing": {
                "base_size": 25,
                "export_multiplier": 3
            },
            "physics": {
                "gravity": -8000,
                "central_gravity": 0.3,
                "spring_length": 200
            },
            "charts": {
                "line_chart_height": 400
            }
        }
    }
    
    config = default_config.copy()
    
    if config_path:
        try:
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
            elif config_path.endswith(('.yaml', '.yml')):
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
            else:
                st.warning(f"Unsupported config file format: {config_path}")
                return config
                
            # Update config with user values
            config.update(user_config)
        except Exception as e:
            st.error(f"Error loading config file: {str(e)}")
    
    # Ensure cache directory exists
    os.makedirs(config["cache_dir"], exist_ok=True)
    
    return config

def generate_sample_data(config):
    """Generate sample/fake data for demo purposes"""
    nodes = config["cluster_nodes"]
    mount_paths = ["data", "home", "scratch", "shared", "projects", "software", "backup"]
    
    # Create realistic mount relationships
    records = []
    
    # Storage nodes typically serve multiple mount points
    storage_nodes = [node for node in nodes if "storage" in node.lower()]
    compute_nodes = [node for node in nodes if node not in storage_nodes]
    
    # If no explicit storage nodes, treat first 2 nodes as storage
    if not storage_nodes:
        storage_nodes = nodes[:2]
        compute_nodes = nodes[2:]
    
    # Generate mounts - each storage node exports several paths
    for storage_node in storage_nodes:
        # Each storage node exports 2-4 mount paths
        num_exports = random.randint(2, 4)
        exported_paths = random.sample(mount_paths, num_exports)
        
        for mount_path in exported_paths:
            # Each export is mounted by 2-5 compute nodes
            num_clients = min(random.randint(2, 5), len(compute_nodes))
            client_nodes = random.sample(compute_nodes, num_clients)
            
            for client_node in client_nodes:
                # 85% of mounts are accessible, 15% have issues
                accessible = random.random() > 0.15
                
                records.append({
                    "nfs_server": storage_node,
                    "nfs_client": client_node,
                    "mount_path": mount_path,
                    "accessible": accessible
                })
    
    # Add some inter-compute node mounts (less common)
    if len(compute_nodes) > 2:
        for _ in range(random.randint(1, 3)):
            server = random.choice(compute_nodes)
            client = random.choice([n for n in compute_nodes if n != server])
            mount_path = random.choice(["tmp", "cache", "logs"])
            accessible = random.random() > 0.1  # Higher success rate for local mounts
            
            records.append({
                "nfs_server": server,
                "nfs_client": client,
                "mount_path": mount_path,
                "accessible": accessible
            })
    
    return pd.DataFrame(records)

def generate_sample_historical_data(config, server, client, mount_path, hours=6):
    """Generate sample historical data for demo purposes"""
    # Generate hourly data points
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Create time series with some realistic patterns
    time_points = []
    current_time = start_time
    
    # Start with a base accessibility rate
    base_rate = 0.95  # 95% uptime baseline
    
    values = []
    timestamps = []
    
    while current_time <= end_time:
        # Add some realistic downtime patterns
        hour = current_time.hour
        
        # Slightly higher chance of issues during maintenance windows (2-4 AM)
        if 2 <= hour <= 4:
            success_rate = base_rate - 0.1
        else:
            success_rate = base_rate
            
        # Add some random variation
        success_rate += random.uniform(-0.05, 0.05)
        success_rate = max(0.8, min(0.99, success_rate))  # Keep between 80-99%
        
        # Generate value (1 for accessible, 0 for not)
        accessible = 1 if random.random() < success_rate else 0
        
        timestamps.append(current_time)
        values.append(accessible)
        
        current_time += timedelta(minutes=10)  # 10-minute intervals
    
    return list(zip(timestamps, values))

def query_prometheus(prometheus_url, query, time_range=None):
    """Query Prometheus for data"""
    try:
        if time_range:
            # Query range for historical data
            end_time = int(time.time())
            start_time = end_time - time_range
            step = max(10, time_range // 100)  # Dynamically adjust step based on range

            response = requests.get(
                f"{prometheus_url}/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_time,
                    "end": end_time,
                    "step": step
                },
                timeout=10
            )
        else:
            # Instant query for current state
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to query Prometheus: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Prometheus: {str(e)}")
        return None

def get_mount_accessibility(config, demo_mode=False):
    """Get the current mount accessibility data from Prometheus or generate sample data"""
    if demo_mode:
        return generate_sample_data(config)
    
    result = query_prometheus(config["prometheus_url"], config["metric_name"])

    if not result or result["status"] != "success" or not result["data"]["result"]:
        st.warning("No mount accessibility data found in Prometheus")
        return pd.DataFrame()

    # Process the prometheus gauge data into a DataFrame
    mapping = config["metric_mapping"]
    records = []
    for metric in result["data"]["result"]:
        records.append({
            "nfs_server": metric["metric"][mapping["server_label"]],
            "nfs_client": metric["metric"][mapping["client_label"]],
            "mount_path": metric["metric"][mapping["path_label"]],
            "accessible": int(metric["value"][1]) == 1
            # Feel free to add more fields to the dataframe if you want to visualize more information.
        })

    return pd.DataFrame(records)

def create_pyvis_network(df, config, show_all_nodes=False, focus_nodes=None):
    """Create a PyVis network visualization from the mount accessibility data"""
    # Get visualization settings
    viz_config = config["visualization"]
    network_config = viz_config["network"]
    physics_config = viz_config["physics"]
    
    # Create a new network
    net = Network(
        height=network_config["height"], 
        width=network_config["width"], 
        bgcolor=network_config["bgcolor"], 
        font_color=network_config["font_color"], 
        directed=True
    )

    # Configure physics for better layout
    net.barnes_hut(
        gravity=physics_config["gravity"], 
        central_gravity=physics_config["central_gravity"], 
        spring_length=physics_config["spring_length"]
    )

    # Get node types with colors and titles
    node_types = config["node_types"]
    default_node = node_types.get("default", {"color": "#607D8B", "title": "Cluster Node"})

    # Determine which nodes to include
    if show_all_nodes:
        # Include all nodes in the visualization
        nodes_to_include = config["cluster_nodes"]
    else:
        # Include only focused nodes and their connected nodes
        nodes_to_include = set()

        if focus_nodes:
            # Always include the focused nodes
            nodes_to_include.update(focus_nodes)

            # Include nodes that have connections to/from focused nodes
            for _, row in df.iterrows():
                if row['nfs_server'] in focus_nodes:
                    nodes_to_include.add(row['nfs_client'])
                if row['nfs_client'] in focus_nodes:
                    nodes_to_include.add(row['nfs_server'])

    # Get node sizing config
    node_sizing = viz_config["node_sizing"]
    
    # Add the nodes
    for node in nodes_to_include:
        # Count exports (server) and mounts (client) for this node
        exports_count = len(df[df['nfs_server'] == node].drop_duplicates(['mount_path']))
        imports_count = len(df[df['nfs_client'] == node])

        # Add the node with appropriate styling
        node_info = node_types.get(node, default_node)

        # Highlight focused nodes
        highlight = focus_nodes and node in focus_nodes
        border_width = 3 if highlight else 1

        net.add_node(
            node,
            label=node,
            color=node_info["color"],
            title=f"{node} \n {node_info.get('title', 'Cluster Node')}  \n Exports: {exports_count} \n Mounts: {imports_count}",
            size=node_sizing["base_size"] + (exports_count * node_sizing["export_multiplier"]),
            borderWidth=border_width
        )

    # Get edge colors and mount path prefix
    edge_colors = viz_config["edge_colors"]
    mount_prefix = config["metric_mapping"]["mount_path_prefix"]
    
    # Add edges based on mount accessibility
    for _, row in df.drop_duplicates(['nfs_server', 'nfs_client', 'mount_path']).iterrows():
        # Only add edges for nodes we're including
        if row['nfs_server'] in nodes_to_include and row['nfs_client'] in nodes_to_include:
            edge_color = edge_colors["accessible"] if row['accessible'] else edge_colors["inaccessible"]

            # Create a title with detailed information
            title = f"Mount: {row['nfs_client']} mounts {row['nfs_server']}:{mount_prefix}{row['mount_path']}"
            title += "<br>Status: " + ("✅ Accessible" if row['accessible'] else "❌ Inaccessible")

            # Add the edge - Note: reversed source and target to show client->server relationship
            net.add_edge(
                row['nfs_client'],
                row['nfs_server'],
                title=title,
                color=edge_color,
                label=row['mount_path'],
                arrows="to",
                width=2
            )

    # Enable physics simulation button and other controls
    net.show_buttons(filter_=['physics', 'nodes', 'edges'])

    return net

def render_network_tab(config):
    """Render the network visualization tab"""
    if 'df' in st.session_state and not st.session_state.df.empty:
        # Add filters for the network view
        st.write("Filter the network visualization:")

        # Create columns for node filters
        col1, col2 = st.columns(2)

        with col1:
            # Filter by NFS Server nodes
            server_nodes = st.multiselect(
                "Focus on NFS Server nodes",
                options=sorted(st.session_state.df['nfs_server'].unique()),
                default=[]
            )

        with col2:
            # Filter by NFS Client nodes
            client_nodes = st.multiselect(
                "Focus on NFS Client nodes",
                options=sorted(st.session_state.df['nfs_client'].unique()),
                default=[]
            )

        # Create columns for accessibility filters
        col1, col2, col3 = st.columns(3)

        with col1:
            show_accessible = st.checkbox("Show accessible mounts", value=True)

        with col2:
            show_inaccessible = st.checkbox("Show inaccessible mounts", value=True)

        with col3:
            show_all_nodes = st.checkbox("Show all nodes", value=True)

        # Filter the DataFrame based on selections
        filtered_df = st.session_state.df.copy()

        # Apply accessibility filters
        if not show_accessible:
            filtered_df = filtered_df[filtered_df['accessible'] == False]

        if not show_inaccessible:
            filtered_df = filtered_df[filtered_df['accessible'] == True]

        # Apply node filters
        focus_nodes = list(set(server_nodes + client_nodes))
        if focus_nodes:
            if not show_all_nodes:
                # Only filter if not showing all nodes
                filtered_df = filtered_df[
                    (filtered_df['nfs_server'].isin(focus_nodes)) |
                    (filtered_df['nfs_client'].isin(focus_nodes))
                ]

        # Create the network visualization
        net = create_pyvis_network(
            filtered_df,
            config,
            show_all_nodes=show_all_nodes,
            focus_nodes=focus_nodes if focus_nodes else None
        )

        # Save to HTML file
        html_file = os.path.join(config["cache_dir"], "nfs_network.html")
        net.save_graph(html_file)

        # Read the HTML content
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Display with HTML component
        st.components.v1.html(html_content, height=730)
    else:
        st.info("No data available. Please refresh.")

def render_table_tab():
    """Render the mount table tab"""
    if 'df' in st.session_state and not st.session_state.df.empty:
        # Add filters for the table
        server_filter = st.multiselect("Filter by NFS Server",
                                       options=sorted(st.session_state.df['nfs_server'].unique()),
                                       default=[])

        # Get available mount paths based on selected server(s)
        mount_paths = []
        if server_filter:
            # Get mount paths only for the selected servers
            server_df = st.session_state.df[st.session_state.df['nfs_server'].isin(server_filter)]
            mount_paths = sorted(server_df['mount_path'].unique())

            # Add mount path filter that depends on selected server(s)
            mount_path_filter = st.multiselect(
                "Filter by Mount Path",
                options=mount_paths,
                default=[]
            )
        else:
            mount_path_filter = []
            st.info("Select an NFS Server to filter by mount path")

        client_filter = st.multiselect("Filter by NFS Client",
                                       options=sorted(st.session_state.df['nfs_client'].unique()),
                                       default=[])

        status_filter = st.multiselect("Filter by Status",
                                       options=["Accessible", "Inaccessible"],
                                       default=[])

        # Apply filters
        filtered_df = st.session_state.df.copy()

        if server_filter:
            filtered_df = filtered_df[filtered_df['nfs_server'].isin(server_filter)]

            # Apply mount path filter if selected
            if mount_path_filter:
                filtered_df = filtered_df[filtered_df['mount_path'].isin(mount_path_filter)]

        if client_filter:
            filtered_df = filtered_df[filtered_df['nfs_client'].isin(client_filter)]

        if status_filter:
            if "Accessible" in status_filter and "Inaccessible" not in status_filter:
                filtered_df = filtered_df[filtered_df['accessible'] == True]
            elif "Inaccessible" in status_filter and "Accessible" not in status_filter:
                filtered_df = filtered_df[filtered_df['accessible'] == False]

        # Display the filtered table
        st.dataframe(
            filtered_df.rename(columns={
                'nfs_server': 'NFS Server',
                'nfs_client': 'NFS Client',
                'mount_path': 'Mount Path',
                'accessible': 'Status'
            }).replace({True: "✅ Accessible", False: "❌ Inaccessible"}),
            use_container_width=True
        )
    else:
        st.info("No data available. Please refresh.")

def render_historical_tab(config):
    """Render the historical view tab"""
    st.write("Historical View of Mount Accessibility")

    # Add time range selector
    time_range = st.slider(
        "Select Time Range",
        min_value=1,
        max_value=24,
        value=6,
        help="Show data for the past X hours"
    )

    # Get available servers and clients from current data
    available_servers = []
    available_clients = []
    
    if 'df' in st.session_state and not st.session_state.df.empty:
        available_servers = sorted(st.session_state.df['nfs_server'].unique())
        available_clients = sorted(st.session_state.df['nfs_client'].unique())
    else:
        available_servers = config["cluster_nodes"]
        available_clients = config["cluster_nodes"]

    nfs_server = st.selectbox("NFS Server", options=available_servers)
    # Filter out the selected server from client options
    client_options = [n for n in available_clients if n != nfs_server]
    
    if client_options:
        nfs_client = st.selectbox("NFS Client", options=client_options)

        # Check if we're in demo mode
        demo_mode = st.session_state.get('demo_mode', False)
        
        if demo_mode:
            # Generate sample historical data
            hist_data = generate_sample_historical_data(config, nfs_server, nfs_client, "data", time_range)
            
            # Display sample data
            hist_df = pd.DataFrame(hist_data, columns=["timestamp", "accessible"])
            hist_df["mount_path"] = "data"  # Sample mount path
            
            # Calculate uptime percentage
            uptime = (hist_df["accessible"].sum() / len(hist_df)) * 100
            
            # Display uptime metric
            st.metric(
                label="Mount: data (sample data)",
                value=f"{uptime:.1f}% Uptime",
                delta=None
            )
            
            # Display the chart
            st.line_chart(
                hist_df.set_index("timestamp")["accessible"],
                use_container_width=True
            )
        else:
            # Query historical data from Prometheus
            mapping = config["metric_mapping"]
            query = f'{config["metric_name"]}{{{mapping["server_label"]}="{nfs_server}", {mapping["client_label"]}="{nfs_client}"}}'
            result = query_prometheus(config["prometheus_url"], query, time_range * 3600)

            if result and result["status"] == "success" and result["data"]["result"]:
                # Process and display historical data
                for series in result["data"]["result"]:
                    mount_path = series["metric"][mapping["path_label"]]
                    values = [(datetime.fromtimestamp(point[0]), int(point[1])) for point in series["values"]]

                    # Create a dataframe for this mount
                    hist_df = pd.DataFrame(values, columns=["timestamp", "accessible"])
                    hist_df["mount_path"] = mount_path

                    # Calculate uptime percentage
                    uptime = (hist_df["accessible"].sum() / len(hist_df)) * 100

                    # Display uptime metric
                    st.metric(
                        label=f"Mount: {mount_path}",
                        value=f"{uptime:.1f}% Uptime",
                        delta=None
                    )

                    # Display the chart
                    st.line_chart(
                        hist_df.set_index("timestamp")["accessible"],
                        use_container_width=True
                    )
            else:
                st.info(f"No historical data available for {nfs_server} to {nfs_client}")
    else:
        st.info("No NFS clients available for selection")

def main(config_path=None, demo_mode=False):
    """Main function to render the Streamlit app"""
    # Load configuration
    config = load_config(config_path)
    
    # Setup page
    setup_page(config["app_title"])
    
    # Store demo mode in session state
    if 'demo_mode' not in st.session_state:
        st.session_state.demo_mode = demo_mode
    
    # Display title with demo indicator
    title = config["app_title"]
    if st.session_state.demo_mode:
        title += " (Demo Mode - Sample Data)"
    st.title(title)

    # Add demo mode toggle and refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        refresh = st.button("🔄 Refresh Data")
    with col2:
        if st.button("🔄 Toggle Demo Mode"):
            st.session_state.demo_mode = not st.session_state.demo_mode
            st.rerun()

    # Use session state to keep track of last refresh time
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
        refresh = True

    # Check if it's time to auto-refresh
    if (datetime.now() - st.session_state.last_refresh).seconds >= config["refresh_interval"]:
        refresh = True

    # Get data if refresh is triggered
    if refresh:
        st.session_state.df = get_mount_accessibility(config, st.session_state.demo_mode)
        st.session_state.last_refresh = datetime.now()

    with col3:
        mode_text = "Demo Mode" if st.session_state.demo_mode else "Live Data"
        st.text(f"{mode_text} | Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

    # Create different views as tabs
    tab1, tab2, tab3 = st.tabs(["Network Graph", "Mount Table", "Historical View"])

    with tab1:
        render_network_tab(config)

    with tab2:
        render_table_tab()

    with tab3:
        render_historical_tab(config)

    # Add a footer with information
    st.divider()
    st.markdown("""
    **About this visualization:**
    - Green lines: Accessible mounts
    - Red lines: Inaccessible mounts
    - Node size reflects the number of exports

    Data sourced from Prometheus NFS mount exporter metrics.
    """)

def run_app():
    """Entry point for running the app from the command line"""
    parser = argparse.ArgumentParser(description="NFS Mount Visualizer")
    parser.add_argument("--config", type=str, help="Path to configuration file (JSON or YAML)")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with sample data")
    args = parser.parse_args()
    
    main(args.config, args.demo)

if __name__ == "__main__":
    run_app()