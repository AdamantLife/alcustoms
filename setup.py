import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="alcustoms",
    version="2.0.1",
    author="AdamantLife",
    author_email="",
    description="A collection of code snippets and high-level interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AdamantLife/alcustoms",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "flask",
        "google",
        "google-api-python-client",
        "matplotlib",
        "numpy",
        "pillow",
        ## "pywin32",
        "python-hosts",
        "al-decorators @ git+https://github.com/AdamantLife/AL_Decorators",
        "al-web @ git+https://github.com/AdamantLife/AL_Web"
        ]
)
