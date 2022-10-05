from setuptools import setup

setup(
    name="momomail",
    version="0.0.1",
    python_requires=">=3.10",
    install_requires=[
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "pydantic",
    ],
    package_dir={"": "momomail"},
)
