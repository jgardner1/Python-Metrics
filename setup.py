from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='Python-Metrics',
      version=version,
      description="A metrics library to time and count what happens during a process.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Jonathan Gardner',
      author_email='jgardner@jonathangardner.net',
      url='https://github.com/jgardner1/Python-Metrics',
      license='GNU Affero General Public License v3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
