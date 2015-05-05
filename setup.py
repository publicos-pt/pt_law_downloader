from distutils.core import setup

setup(name='pt-law-downloader',
      version='1.0.0',
      description='Downloader of the official texts of the portuguese law.',
      long_description=open('README.md').read(),
      author='Jorge C. Leitão',
      url='https://github.com/jorgecarleitao/pt_law_downloader',
      py_modules=['pt_law_downloader'],
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      install_requires=['Beautifulsoup4'])
