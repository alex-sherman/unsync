from setuptools import setup
from pathlib import Path

setup(
    name='unsync',
    version='1.4.0',
    packages=['unsync'],
    url='https://github.com/alex-sherman/unsync',
    license='MIT',
    author='Alex-Sherman',
    author_email='asherman1024@gmail.com',
    description='Unsynchronize asyncio',
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
)
