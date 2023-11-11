from setuptools import setup, find_packages

setup(
    name='your_package_name',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests==2.31.0',
        'ffmpeg-python==0.2.0',
    ]
)
