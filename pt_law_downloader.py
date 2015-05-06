import re
import logging
import datetime
from urllib.request import urlopen

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

URI = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/'
DOCUMENT_ID_FORMAT = URI + '{document_id}' + '/details/{page}/maximized'
PUBLICATION_URL_FORMAT = 'https://dre.pt/home/-/dre/{publication_id}/details/' \
                         'maximized?serie=II&parte_filter=31'
# e.g. /application/file/a/137056
PDF_ID_REGEX = re.compile(r'/application/file/a/(\d+)')


DOCUMENT_META_REGEX = re.compile(
    r'(?P<dr_name>Diário da República|Diário do Governo)'
    r'(?: n.º )(?P<dr_number>[0-9A-Za-z/-]+)'
    r'(?P<dr_supplement>, .*)?, '
    r'Série (?P<dr_series>.*) de '
    r'(?P<dr_date>\d{4}-\d{2}-\d{2})$')

PUBLICATION_META_RE = re.compile('^(?P<type>.*?)(?:'
                                 '(?: n.º )(?P<number>[0-9A-Za-z/-]+))?\s?$')


def cache(file_name_format):
    """
    A decorator to cache the result of the function into a file. The result
    must be a string.

    The decorator argument is the file name format. The format must contain the
    same number of positional arguments as the function

    E.g. 'd_{0}_{1}.html' for a function of 2 arguments.
    """
    def cache_function(function):
        def func_wrapper(*args, **kwargs):
            file_name = file_name_format.format(*args, **kwargs)
            try:
                with open(file_name, 'r') as cache_file:
                    data = '\n'.join(cache_file.readlines())
            except IOError:
                data = function(*args, **kwargs)
                with open(file_name, 'w') as cache_file:
                    cache_file.write(data)
            return data
        return func_wrapper
    return cache_function


def get_html(url):
    response = urlopen(url)
    return response.read().decode('utf-8')


def get_search_html(series=None, year=None):
    """
    Returns the HTML of the search of documents.
    """
    url = URI + '/advanced/maximized?types=DR&perPage=1000000'

    if year is not None:
        url += '&ano=%d' % year
    if series is not None:
        assert(series in ('I', 'II'))
        url += '&serie=%s' % series

    return get_html(url)


@cache('cached_html/doc_{0}_{1}.html')
def get_document_html(document_id, page):
    return get_html(DOCUMENT_ID_FORMAT.format(document_id=document_id, page=page))


@cache('cached_html/{0}.html')
def get_publication_html(publication_id):
    return get_html(PUBLICATION_URL_FORMAT.format(publication_id=publication_id))


def parse_document_string(string):
    """
    Parses the string identifying the document.
    """
    match = DOCUMENT_META_REGEX.search(string)

    if match.group('dr_supplement') is not None:
        sup = match.group('dr_supplement')[2:]
    else:
        sup = None

    return {'name': match.group('dr_name'),
            'number': match.group('dr_number'),
            'supplement': sup,
            'series': match.group('dr_series'),
            'date': match.group('dr_date')}


def get_document(document_id):
    logger.debug('Getting document_id %d' % document_id)

    html = get_document_html(document_id, 1)
    soup = BeautifulSoup(html)

    data = parse_document_string(soup.find('h1').string)
    data['dre_id'] = document_id

    data['publications'] = get_publications(document_id, soup)

    return data


def get_documents(series, year):
    """
    Returns a list of all documents of a given series and year as a dictionary.

    This performs 1 hit in DRE to get the list of documents plus hits to
    retrieve all publications of each document.
    """
    html = get_search_html(series, year)
    soup = BeautifulSoup(html)

    for entry in reversed(soup.find_all('div', class_='result')):
        dre_id = int(re.search('asearch/(\d+)/details', entry.a['href']).group(1))
        yield get_document(dre_id)


def get_publication(publication_id):
    """
    Gets and parses the html of a publication_id into a dictionary.
    """
    logger.debug('Getting publication_id %d' % publication_id)
    html = get_publication_html(publication_id)
    soup = BeautifulSoup(html)

    match = PUBLICATION_META_RE.search(soup.find('h1').string)
    data = match.groupdict()
    if publication_id == 638275:
        # see test_638275
        data['type'] = 'Decreto do Ministro da República'
        data['number'] = '4/93'
    data['dre_id'] = publication_id

    a = soup.find('a', class_='download-file')
    data['pdf_id'] = int(PDF_ID_REGEX.search(a['href']).group(1))

    meta_data_div = soup.find('div', class_='main-details')

    li = meta_data_div.find('li', class_='dataPublicacao')
    date_string = li.text.split(':')[1]
    data['date'] = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

    li = meta_data_div.find('li', class_='tipoDiploma.tipo')
    type_string = li.text.split(':')[1]
    if publication_id == 638275:
        type_string = data['type']
    assert(type_string == data['type'])

    li = meta_data_div.find('li', class_='numero')
    if data['number']:
        number_string = li.text.split(':')[1]
        if publication_id == 638275:
            number_string = data['number']
        assert(number_string == data['number'])

    li = meta_data_div.find('li', class_='emissor.designacao')
    if li is None:
        data['creator'] = None
    else:
        data['creator'] = li.text.split(':')[1]

    li = meta_data_div.find('li', class_='paginas')
    if li is None:
        data['pages'] = None
    else:
        data['pages'] = li.text.split(':')[1]

    li = soup.find('li', class_='formatedSumarioWithLinks')
    if li is None:
        data['summary'] = None
    else:
        data['summary'] = li.text.split(':')[1]

    li = soup.find('li', class_='formatedTextoWithLinks')
    if li is None:
        data['text'] = None
    else:
        data['text'] = str(li.div).replace('<div>', '').replace('</div>', '')

    return data


def get_publications(document_id, soup=None):
    """
    Given a document id, returns the list of all publications on it.

    This does at least 1 hit in DRE. If the document has more than 20
    publications, it performs #publications//20 hits (1 hit/page of 20 results).

    If soup is not None, it does -1 hit since it uses the soup to extract the list
    of publications.
    """
    def _get_publications(u_list):
        pubs = []
        for result in reversed(u_list.find_all('li')):
            if not result.find('a'):
                # publication has no id or any information. Just add an empty
                # identifying a missing publication of this document.
                data = {'dre_id': None,
                        'number': None,
                        'type': None}
                pubs.append(data)
                continue
            dre_id = int(result.a.find('span', class_='rgba').string)
            pubs.append(get_publication(dre_id))

        return pubs

    if soup is None:
        html = get_document_html(document_id, 1)
        soup = BeautifulSoup(html)

    div_list = soup.find('div', class_='list')
    if div_list is None:
        return []

    publications = _get_publications(div_list.find('ul', recursive=False))

    if div_list.find('div', class_='pagination'):
        # has more than one page. Cycle them
        page = 1
        while '>' in div_list.ul.text:
            page += 1
            html = get_document_html(document_id, page)
            soup = BeautifulSoup(html)
            div_list = soup.find('div', class_='list')
            if div_list is not None:
                publications += _get_publications(
                    div_list.find('ul', recursive=False))

    return publications
