from setuptools import setup, find_packages

setup(
    name="ai6",
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
)
