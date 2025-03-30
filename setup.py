from setuptools import setup, find_packages

setup(
    name="pysyslog-lfc",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pysyslog': [
            'inputs/*.py',
            'parsers/*.py',
            'outputs/*.py',
            '*.py'
        ]
    },
    install_requires=[
        "systemd-python>=235",
        "configparser>=5.0.0",
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
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.9",
) 