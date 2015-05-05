[![Build Status](https://travis-ci.org/publicos-pt/pt_law_downloader.svg?branch=master)](https://travis-ci.org/publicos-pt/pt_law_downloader)
[![Coverage Status](https://coveralls.io/repos/publicos-pt/pt_law_downloader/badge.svg?branch=master)](https://coveralls.io/r/publicos-pt/pt_law_downloader?branch=master)

# PT Law Downloader

PT law downloader is an open source Python package to download the official texts
of the Portuguese law.

## Author

The authors of this package are Jorge C. Leitão and Helder Guerreiro.

## The code

This package is written in Python 3, depends on beautifulSoup 4
(`pip install beautifulsoup4`), and is licenced under MIT licence (see LICENCE).

## To run the tests

Run the tests with:

    python -m unittest discover

## Usage

Law is organized in documents that contain publications. Its interface is defined
by 4 functions:

* `get_publication(publication_id)`: returns the publication `publication_id`
* `get_publications(document_id)`: returns the list of publications of a `document_id`.
  Uses `get_publication(publication_id)`.
* `get_document(document_id)`: returns a single dictionary with a `document_id`,
  which includes all its publications. Uses `get_publications(document_id)`.
* `get_documents(series, year)`: returns a list of dictionaries, each entry a 
  `document_id`. Uses `get_document(document_id)`.

Typically series is either `'I'` or `'II'`, year is an int (e.g. 2002).
