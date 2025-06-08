"""
Tests for the configuration loading functionality
"""
import os
import tempfile
import json
import yaml
import pytest
from nfs_mount_visualizer.app import load_config

def test_default_config():
    """Test loading default configuration"""
    config = load_config()
    assert config["prometheus_url"] == "http://localhost:9090"
    assert "cluster_nodes" in config
    assert "refresh_interval" in config
    assert "cache_dir" in config

def test_json_config():
    """Test loading configuration from JSON file"""
    test_config = {
        "prometheus_url": "http://test-server:9090",
        "refresh_interval": 60,
        "app_title": "Test Title"
    }
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp.write(json.dumps(test_config).encode('utf-8'))
        temp_name = temp.name
    
    try:
        config = load_config(temp_name)
        assert config["prometheus_url"] == "http://test-server:9090"
        assert config["refresh_interval"] == 60
        assert config["app_title"] == "Test Title"
        # Default values should still be present for unspecified fields
        assert "cluster_nodes" in config
        assert "cache_dir" in config
    finally:
        os.unlink(temp_name)

def test_yaml_config():
    """Test loading configuration from YAML file"""
    test_config = """
    prometheus_url: http://yaml-server:9090
    refresh_interval: 120
    app_title: YAML Test
    """
    
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp:
        temp.write(test_config.encode('utf-8'))
        temp_name = temp.name
    
    try:
        config = load_config(temp_name)
        assert config["prometheus_url"] == "http://yaml-server:9090"
        assert config["refresh_interval"] == 120
        assert config["app_title"] == "YAML Test"
        # Default values should still be present for unspecified fields
        assert "cluster_nodes" in config
        assert "cache_dir" in config
    finally:
        os.unlink(temp_name)

def test_invalid_file():
    """Test loading from an invalid file format"""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
        temp.write(b"This is not a valid config file")
        temp_name = temp.name
    
    try:
        config = load_config(temp_name)
        # Should fall back to defaults
        assert config["prometheus_url"] == "http://localhost:9090"
    finally:
        os.unlink(temp_name)