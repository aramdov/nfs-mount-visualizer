from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nfs-mount-visualizer",
    version="0.1.0",
    author="YerevaNN",
    author_email="your.email@example.com",
    description="Interactive visualization of NFS mounts between cluster nodes using Prometheus data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nfs-mount-visualizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "streamlit>=1.0.0",
        "pandas>=1.0.0",
        "pyvis>=0.1.9",
        "requests>=2.25.0",
        "pyyaml>=5.1",
    ],
    entry_points={
        "console_scripts": [
            "nfs-mount-visualizer=nfs_mount_visualizer.cli:run",
        ],
    },
)