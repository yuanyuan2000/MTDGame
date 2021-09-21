from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name = "mtdnetwork",
    author = "Alex Brown",
    packages = find_packages(),
    python_requires = ">=3.8",
    install_requires = required,
    entry_points = {
        "console_scripts" : [
            "mtdsim = mtdnetwork.run:main"
        ]
    },
    zip_safe = True,
    package_data = {
        "mtdnetwork.data" : ["*.txt"]
    }
)