from setuptools import setup, find_packages

setup(
    name="movie-generator-framework",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "asyncio",
        "psutil",
        "pyyaml",
        "jsonschema",
        "watchdog",
        "pytest",
        "pytest-asyncio",
        "pynvml",  # For GPU monitoring
        "openai",  # For GPT integration
        "pillow",  # For image processing
        "numpy",   # For numerical operations
        "torch",   # For ML models
        "transformers"  # For text generation
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="An agentic framework for automated movie generation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/movie-generator-framework",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
) 