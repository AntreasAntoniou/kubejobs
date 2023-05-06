from pkg_resources import require
from setuptools import find_packages, setup

requirements = ["fire", "PyYAML", "kubernetes"]
dev_requirements = [
    "docformatter",
    "black",
    "isort",
    "flake8",
    "autoflake",
    "sphinx",
    "sphinx_rtd_theme",
    "sphinx-autodoc-typehints",
]

setup(
    name="kubejobs",
    version="0.1.0",
    description="A Python library for creating and running Kubernetes Jobs",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/kubejobs",
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)
