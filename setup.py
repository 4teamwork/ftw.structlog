from setuptools import setup, find_packages
import os

version = '1.4.0'

tests_require = [
    'unittest2',
    'ftw.testing',
    'ftw.testbrowser',
    'requests_toolbelt',
    'plone.rest',
    'Plone',
    'freezegun < 0.3.15',
]


setup(name='ftw.structlog',
      version=version,
      description="Structured logging for Plone",
      long_description=open("README.rst").read() + "\n" + open(
          os.path.join("docs", "HISTORY.txt")).read(),

      classifiers=[
          "Environment :: Web Environment",
          'Framework :: Plone',
          'Framework :: Plone :: 4.3',
          "Intended Audience :: Developers",
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],

      keywords='structured logging plone',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      url='https://github.com/4teamwork/ftw.structlog',
      license='GPL2',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,


      install_requires=[
          'setuptools',
          'Zope2',
          'pytz',
          'tzlocal',
          'fluent-logger < 0.10.0',
      ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """)
