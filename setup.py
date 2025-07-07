import setuptools

with open("README.md", encoding="utf-8") as f:
    long_desc = f.read()

setuptools.setup(
    name="vibetracer",
    version="0.1.1",
    author="Soroush Zamani",
    author_email="szchem20@gmail.com",
    description="Lightweight function‐call tracer with SQLite backend, built for vibe coders.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/szamani20/VibeTracer",
    packages=setuptools.find_packages(
        include=["vibetracer*"]
    ),
    entry_points={
        'console_scripts': [
            'vibetracer = vibetracer.command.runner:main',
        ],
    },
    install_requires=[
        "sqlmodel>=0.0.24",
        "SQLAlchemy>=2.0.41",
        "matplotlib>=3.10.3",
        "networkx>=3.5",
        "openai>=1.93.0",
        "anthropic>=0.55.0",
        "google-genai>=1.23.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
