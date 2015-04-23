import unittest

from pt_law_downloader import parse_document_string, parse_publication_string, \
    get_publications


class TestDownloader(unittest.TestCase):

    def test_parse_document_string1(self):
        r = parse_document_string('Diário do Governo n.º 4/1975, 1º Suplemento, '
                                  'Série III de 1975-01-06')
        assert(r['name'] == 'Diário do Governo')
        assert(r['number'] == '4/1975')
        assert(r['supplement'] == '1º Suplemento')
        assert(r['series'] == 'III')
        assert(r['date'] == '1975-01-06')

    def test_parse_document_string2(self):
        r = parse_document_string('Diário da República n.º 291/2000, Apêndice '
                                  '171/2000, Série II de 2000-12-19')
        assert(r['name'] == 'Diário da República')
        assert(r['number'] == '291/2000')
        assert(r['supplement'] == 'Apêndice 171/2000')
        assert(r['series'] == 'II')
        assert(r['date'] == '2000-12-19')

    def test_parse_document_string3(self):
        r = parse_document_string('Diário da República n.º 291/2000, Série I de '
                                  '2000-12-19')
        assert(r['name'] == 'Diário da República')
        assert(r['number'] == '291/2000')
        assert(r['supplement'] is None)
        assert(r['series'] == 'I')
        assert(r['date'] == '2000-12-19')

    def test_parse_publication_string1(self):
        r = parse_publication_string('Portaria n.º 5/75  - Diário do Governo n.º '
                                     '1/1975, Série I de 1975-01-02300809')
        assert(r['type'] == 'Portaria')
        assert(r['number'] == '5/75')
        assert(r['dre_id'] == 300809)

    def test_parse_publication_string2(self):
        r = parse_publication_string('Despacho  - Diário do Governo n.º 1/1975, '
                                     'Série I de 1975-01-02300805')
        assert(r['type'] == 'Despacho')
        assert(r['number'] is None)
        assert(r['dre_id'] == 300805)

    def test_get_publications_pagination(self):
        """
        Tests that we are able to get the 21 publications of a specific document.
        """
        assert(len(get_publications(114266)) == 21)
