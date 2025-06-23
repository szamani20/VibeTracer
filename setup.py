import setuptools

with open("README.md", encoding="utf-8") as f:
    long_desc = f.read()

setuptools.setup(
    name="vibetracer",
    version="0.1.0",
    author="Soroush Zamani",
    author_email="szchem20@gmail.com",
    description="Lightweight function‐call tracer with SQLite backend, built for vibe coders.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/szamani20/VibeTracer",
    packages=setuptools.find_packages(
        include=["vibetracer*"]
    ),
    install_requires=[
        "sqlmodel>=0.0.24",
        "SQLAlchemy>=2.0.41",
        "matplotlib>=3.10.3",
        "matplotlib>=2.3.0",
        "networkx>=3.5",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
