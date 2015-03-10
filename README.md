# PT Law Downloader

PT law downloader is an open source Python package to download the official texts
of the Portuguese law.

## Author

The authors of this package are Jorge C. Leitão and Helder Guerreiro.  

## The code

This package is written in Python 2+3, depends on beautifulSoup 4
(`pip install beautifulsoup4`), and is licenced under MIT licence (see LICENCE).

## Usage

Create a directory `cached_html/` and run

`python -m downloader`

The API consists of three functions:

* `get_documents(series, year)`
* `get_document(document_id)`
* `get_publications(document_id)`
