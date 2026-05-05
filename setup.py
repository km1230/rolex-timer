"""Setup script for Rolex timer."""

from setuptools import setup, find_packages

setup(
    name='rolex-timer',
    version='1.0.0',
    description='A terminal-based time tracking tool',
    author='Your Name',
    py_modules=['rolex', 'timer', 'storage', 'models'],
    install_requires=[
        'click>=8.0.0',
    ],
    entry_points={
        'console_scripts': [
            'rolex=rolex:cli',
        ],
    },
    python_requires='>=3.7',
)
