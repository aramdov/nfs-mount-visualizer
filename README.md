# NFS Mount Visualizer

An interactive web application for visualizing NFS mount relationships between cluster nodes using Prometheus data. This tool helps system administrators and users understand and troubleshoot NFS mount accessibility issues in a cluster environment.

## Features

- **Interactive Network Graph**: Visualize NFS server-client relationships with color-coded mount status
- **Detailed Mount Table**: Filter and view mount information in tabular format
- **Historical Analysis**: Track mount accessibility over time with uptime calculations
- **Customizable Configuration**: Easily adapt to any cluster environment with JSON/YAML configuration
- **Real-time Updates**: Automatic or manual data refresh from Prometheus

## Requirements

- Python 3.6+
- Prometheus server with NFS mount metrics
- NFS mount exporter that provides `nfs_mount_accessible` metrics (or configurable)
  - You can configure and use your own custom metrics that you export to prometheus that contains mount access metadata/info. You can go off of our example prometheis metric minimum.

## Installation

### From PyPI

- We don't have this on PyPI, not sure if there is demand for it...

### From Source

```bash
git clone https://github.com/yourusername/nfs-mount-visualizer.git
cd nfs-mount-visualizer
pip install -e .
```

## Quick Start

1. Create a configuration file (YAML or JSON) with your cluster details:

```yaml
prometheus_url: "http://prometheus-server:9090"
cluster_nodes:
  - "node1"
  - "node2"
  - "storage1"
```

2. Run the application:

```bash
nfs-mount-visualizer --config your_config.yaml
```

3. Open your browser at the displayed URL (typically http://localhost:8501)

## Configuration

The application can be configured using a YAML or JSON file. Below is a sample configuration with all available options:

```yaml
# Prometheus server URL
prometheus_url: "http://localhost:9090"

# Refresh interval in seconds
refresh_interval: 300

# Cache directory for temporary files
cache_dir: ".cache"

# Application title
app_title: "NFS Mount Visualization"

# Prometheus metric name for NFS mount accessibility
metric_name: "nfs_mount_accessible"

# List of cluster nodes to include in the visualization
cluster_nodes:
  - "node1"
  - "node2"
  - "node3"
  - "storage1"

# Node types with custom colors and titles
node_types:
  default:
    color: "#607D8B"
    title: "Cluster Node"
  
  node1:
    color: "#6E9FED"
    title: "Head Node"
  
  storage1:
    color: "#9C27B0"
    title: "Storage Node"
```

## Prometheus Metric Format

The visualizer expects Prometheus metrics in a specific format, but the label names are fully configurable.

### Default Format
```
nfs_mount_accessible{source_node="server1", target_node="client1", mount_path="path1"} 1
```

Where:
- `source_node`: The NFS server node (configurable via `metric_mapping.server_label`)
- `target_node`: The NFS client node (configurable via `metric_mapping.client_label`)
- `mount_path`: The path being mounted (configurable via `metric_mapping.path_label`)
- Value: 1 for accessible, 0 for inaccessible

### Custom Metric Labels
You can adapt the visualizer to work with any metric structure by configuring the label mappings:

```yaml
metric_mapping:
  server_label: "nfs_server_hostname"    # Your actual server label name
  client_label: "compute_node"           # Your actual client label name  
  path_label: "export_path"              # Your actual path label name
  mount_path_prefix: "/shared/"          # Prefix for display purposes
```

This allows the visualizer to work with metrics like:
```
my_custom_nfs_metric{nfs_server_hostname="storage01", compute_node="node01", export_path="data"} 1
```

## Adapting to Your Cluster

### Design Decisions and Assumptions

The visualizer was designed with the following assumptions that you may need to adapt:

1. **Metric Structure**: Assumes a gauge metric with three labels identifying server, client, and mount path
2. **Mount Path Display**: Assumes mounts can be displayed with a configurable prefix (default `/mnt/`)
3. **Binary Status**: Assumes mount accessibility is binary (1=accessible, 0=inaccessible)
4. **Node Discovery**: Uses a predefined list of cluster nodes rather than auto-discovery

### Configuration Examples

The `examples/` directory contains complete configurations for different cluster types:

- `examples/slurm-cluster.yaml` - Slurm/TORQUE cluster with custom metric labels
- `examples/kubernetes-cluster.json` - Kubernetes cluster with persistent volume monitoring
- `examples/hpc-cluster.yaml` - HPC cluster with mixed Lustre/NFS storage

### Customization Guide

1. **Metric Labels**: Configure `metric_mapping` to match your Prometheus metric labels
2. **Visualization**: Customize colors, sizing, and layout via `visualization` settings
3. **Node Types**: Define node categories with custom colors and titles
4. **Network Layout**: Adjust physics parameters for optimal graph layout

### Troubleshooting

**No data showing?**
- Verify `prometheus_url` is accessible
- Check that `metric_name` matches your actual metric name
- Ensure `metric_mapping` labels match your metric structure
- Use Prometheus query browser to verify data exists

**Graph layout issues?**
- Adjust `visualization.physics` parameters
- Modify `node_sizing` for better visual balance
- Try different `height` and `width` settings

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/nfs-mount-visualizer.git
cd nfs-mount-visualizer
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Originally developed at [YerevaNN](https://www.yerevann.com/) for cluster monitoring
- Built with [Streamlit](https://streamlit.io/) and [PyVis](https://pyvis.readthedocs.io/)