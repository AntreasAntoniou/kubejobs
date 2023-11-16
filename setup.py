from setuptools import find_packages, setup

requirements = ["fire", "PyYAML", "kubernetes", "rich"]
dev_requirements = [
    "docformatter",
    "black",
    "isort",
    "flake8",
    "autoflake",
    "sphinx",
    "sphinx_rtd_theme",
    "sphinx-autodoc-typehints",
    "sphinx-material",
]

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="kubejobs",
    version="0.4.0",
    description="A Python library for creating and running Kubernetes Jobs",
    long_description=long_description,
    long_description_content_type="text/markdown",  # This is important!
    author="Antreas Antoniou",
    author_email="iam@antreas.io",
    url="https://github.com/AntreasAntoniou/kubejobs",
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
