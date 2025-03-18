from setuptools import setup, find_packages

setup(
    name="video-cropper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "python-multipart",
        "uvicorn",
        "jinja2",
        "ffmpeg-python",
    ],
) 