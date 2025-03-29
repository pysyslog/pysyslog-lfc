from setuptools import setup, find_packages

setup(
    name="pysyslog-lfc",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "configparser>=5.0.0",
        "watchdog>=2.1.0",
        "python-json-logger>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pysyslog=pysyslog.main:main",
        ],
    },
    author="PySyslog LFC Team",
    author_email="support@pysyslog.org",
    description="A lightweight, modular log processor with flow-based configuration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rsyslog/pysyslog-lfc",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 