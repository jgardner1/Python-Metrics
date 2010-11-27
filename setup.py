from setuptools import setup, find_packages
import sys, os

version = '0.2'

setup(name='pymetrics',
      version=version,
      description="A metrics library to time and count what happens during a process.",
      long_description="""\
""",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Framework :: Pylons',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Utilities',
      ],
      keywords='metrics timer',
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
