from setuptools import setup, find_packages

setup(
    name="stonks",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "yfinance==0.2.54",
        "selenium==4.23.1",
        "requests==2.32.3",
        "chromedriver-autoinstaller==0.6.4",
        "selenium-wire==5.1.0",
        "brotlipy==0.7.0",
    ],
    python_requires=">=3.7",
) 