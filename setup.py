from setuptools import setup

setup(
    name="pygmail",
    version="0.0.1",
    python_requires=">=3.10",
    packages=["pygmail"],
    entry_points={"console_scripts": ["pygmail=pygmail.__main__:main"]},
)
