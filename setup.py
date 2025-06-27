from setuptools import setup, find_packages

setup(
    name="ProductAnalyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0",
        "langchain>=0.1",
        "chromadb>=0.4",
        "atlassian-python-api>=3.41",
        "requests>=2.31",
        "streamlit>=1.28",
    ],
)
