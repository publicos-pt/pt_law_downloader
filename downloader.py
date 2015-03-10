import re
import logging
import datetime

try:
    # Python 3
    from urllib.request import URLopener, urlopen
except ImportError:
    # Python 2
    from urllib import URLopener, urlopen

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

URI = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/'
DOCUMENT_ID_FORMAT = URI + '{document_id}' + '/details/{page}/maximized'
PUBLICATION_URL_FORMAT = 'https://dre.pt/home/-/dre/{publication_id}/details/' \
                         'maximized?serie=II&parte_filter=31'
# /application/file/137056
PDF_ID_REGEX = re.compile(r'/application/file/(\d+)')

DOCUMENT_META_REGEX = '(.*) n.º (\d+)/(\d{4})(, .*)?, ' \
                      'Série (.*) de (\d{4}-\d{2}-\d{2})'


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
    regex = re.compile(DOCUMENT_META_REGEX)
    match = regex.search(string)

    if match.group(4) is not None:
        sup = match.group(4)[2:]
    else:
        sup = None

    return {'name': match.group(1),
            'number': match.group(2),
            'year': match.group(3),
            'supplement': sup,
            'series': match.group(5),
            'date': match.group(6)}


def test_parse_document_string1():
    r = parse_document_string('Diário do Governo n.º 4/1975, 1º Suplemento, Série III de 1975-01-06')
    assert(r['name'] == 'Diário do Governo')
    assert(r['number'] == '4')
    assert(r['year'] == '1975')
    assert(r['supplement'] == '1º Suplemento')
    assert(r['series'] == 'III')
    assert(r['date'] == '1975-01-06')


def test_parse_document_string2():
    r = parse_document_string('Diário da República n.º 291/2000, Apêndice 171/2000, Série II de 2000-12-19')
    assert(r['name'] == 'Diário da República')
    assert(r['number'] == '291')
    assert(r['year'] == '2000')
    assert(r['supplement'] == 'Apêndice 171/2000')
    assert(r['series'] == 'II')
    assert(r['date'] == '2000-12-19')


def get_documents(series, year):
    """
    Returns a list of all documents of a given series and year as a dictionary.

    This performs 1 hit in DRE to get the list of documents plus hits to
    retrieve all publications of each document.
    """
    html = get_search_html(series, year)
    soup = BeautifulSoup(html)

    results = reversed(soup.find_all('div', class_='result'))

    documents = []
    for result in results:
        data = parse_document_string(result.a.string)
        dre_id = int(re.search('asearch/(\d+)/details', result.a['href']).group(1))
        data['dre_id'] = dre_id
        logger.debug('Getting document_id %d' % dre_id)

        data['publications'] = get_publications(dre_id)
        documents.append(data)

    return documents


def parse_publication_string(string):
    """
    Parses the publication string into a type, a number and its dre_id.
    """
    'Portaria n.º 286/2014 - [...][dre_id]'
    regex = re.compile('(.*) n.º (.*)  - %s(\d+)' % DOCUMENT_META_REGEX)
    match = regex.search(string)
    return {'type': match.group(1),
            'number': match.group(2),
            'dre_id': int(match.group(9))}


def parse_publication_html(publication_id):
    """
    Parses the html of a publication into a dictionary.
    """
    html = get_publication_html(publication_id)
    soup = BeautifulSoup(html)
    data = {}

    meta_data_div = soup.find('div', class_='main-details')

    li = meta_data_div.find('li', class_='dataPublicacao')
    date_string = li.text.split(':')[1]
    data['date'] = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

    li = meta_data_div.find('li', class_='tipoDiploma.tipo')
    data['type'] = li.text.split(':')[1]

    li = meta_data_div.find('li', class_='numero')
    data['number'] = li.text.split(':')[1]

    li = meta_data_div.find('li', class_='emissor.designacao')
    data['creator'] = li.text.split(':')[1]

    li = meta_data_div.find('li', class_='paginas')
    data['pages'] = li.text.split(':')[1]

    li = soup.find('li', class_='formatedSumarioWithLinks')
    data['summary'] = li.text.split(':')[1]

    li = soup.find('li', class_='formatedTextoWithLinks')
    data['text'] = str(li.div).replace('<div>', '').replace('</div>', '')

    return data


def get_publications(document_id):
    """
    Given a document id, returns the list of all publications on it.

    This does at least 1 hit in DRE. If the document has more than 20
    publications, it performs #publications//20 hits (1 hit/page of 20 results).
    """
    def _get_publications(u_list):
        publications = []
        for result in reversed(u_list.find_all('li')):
            data = parse_publication_string(result.a.get_text())
            dre_id = data['dre_id']
            logger.debug('Getting publication_id %d' % dre_id)

            data['pdf_id'] = int(PDF_ID_REGEX.search(result.a['href']).group(1))

            data.update(parse_publication_html(data['dre_id']))

            publications.append(data)

        return publications

    html = get_document_html(document_id, 1)
    soup = BeautifulSoup(html)

    div_list = soup.find('div', class_='list')

    publications = _get_publications(div_list.find('ul', recursive=False))

    if div_list.find('div', class_='pagination'):
        # has more than one page. Cycle them
        page = 1
        while '>' in div_list.ul.text:
            page += 1
            html = get_document_html(document_id, page)
            soup = BeautifulSoup(html)
            div_list = soup.find('div', class_='list')
            publications += _get_publications(div_list.find('ul', recursive=False))

    return publications


def test_get_publications_pagination():
    """
    Tests that we are able to obtain the 21 publications of a specific document.
    """
    assert(len(get_publications(114266)) == 21)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    test_parse_document_string1()
    test_parse_document_string2()
    #test_get_publications_pagination()

    get_documents('I', 2000)
