from setuptools import setup
from pathlib import Path
import os

required = None
if os.name == "posix":
    required = ["uvloop"]

setup(
    name='unsync',
    version='1.2.1',
    packages=['unsync'],
    url='https://github.com/alex-sherman/unsync',
    license='MIT',
    author='Alex-Sherman',
    author_email='asherman1024@gmail.com',
    description='Unsynchronize asyncio',
    install_requires = required,
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
)
