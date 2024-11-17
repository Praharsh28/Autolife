from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="autolife",
        version="1.0.0",
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            "PyQt5>=5.15.9",
            "requests>=2.31.0",
            "torch>=2.2.1",
            "python-dotenv>=1.0.0",
            "numpy>=1.25.2",
            "ffmpeg-python>=0.2.0",
            "colorlog>=6.7.0",
            "transformers>=4.36.0",
            "pillow>=10.2.0",
            "aiohttp>=3.9.1"
        ],
        extras_require={
            "test": [
                "pytest>=7.4.4",
                "pytest-cov>=4.1.0",
                "pytest-qt>=4.2.0",
                "pytest-xvfb>=3.0.0",
                "pytest-xdist>=3.5.0",
                "pytest-timeout>=2.1.0",
                "pytest-mock>=3.12.0"
            ]
        },
        python_requires=">=3.11",
    )
