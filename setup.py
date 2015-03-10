# encoding: utf-8
from distutils.core import setup

setup(name='pt-law-downloader',
      version='0.1',
      description='Downloader of the official texts of the portuguese law.',
      long_description=open('README.md').read(),
      author='Jorge C. Leitão',
      url='https://github.com/jorgecarleitao/pt_law_downloader',
      py_modules=['pt_law_downloader'],
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
)
