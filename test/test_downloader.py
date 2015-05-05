import datetime
import unittest

from pt_law_downloader import parse_document_string, get_publication, \
    get_document, get_documents, PUBLICATION_META_RE


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

    def test_parse_publication_string(self):
        match = PUBLICATION_META_RE.search('Despacho ')
        assert(match.groupdict() == {'type': 'Despacho', 'number': None})

        match = PUBLICATION_META_RE.search('Portaria n.º 5/75 ')
        assert(match.groupdict() == {'type': 'Portaria', 'number': '5/75'})

    def test_get_document(self):
        """
        Test correct meta-data of get_document
        """
        result = get_document(114266)
        # publications are tested somewhere else. Let's just track their count.
        result['publications'] = ['' for _ in result['publications']]

        expected = {'publications': ['']*21,
                    'series': 'I-A',
                    'dre_id': 114266,
                    'supplement': None,
                    'date': '2000-12-13',
                    'number': '286/2000',
                    'name': 'Diário da República'}

        self.assertEqual(expected, result)

    def test_get_publication(self):
        result = get_publication(583605)

        self.assertTrue(result['summary'].startswith(
            'Exonera, sob proposta do Governo'))
        self.assertTrue(result['text'].startswith(
            '<?xml version="1.0" encoding="UTF-8"?>'))

        del result['summary']
        del result['text']

        expected = {'dre_id': 583605,
                    'date': datetime.date(2000, 12, 13),
                    'type': 'Decreto do Presidente da República',
                    'number': '58/2000',
                    'creator': 'Presidência da República',
                    'pages': '7082 - 7082',
                    'pdf_id': 583537}

        self.assertEqual(expected, result)

    def test_get_publications(self):

        document = next(get_documents('I', 2002))
        pubs = document['publications'][:]
        document['publications'] = ['' for _ in document['publications']]

        expected = {'publications': ['']*3,
                    'series': 'I-A',
                    'dre_id': 118243,
                    'supplement': None,
                    'date': '2002-01-02',
                    'number': '1/2002',
                    'name': 'Diário da República'}

        self.assertEqual(expected, document)

        expected = {'dre_id': 584794,
                    'date': datetime.date(2002, 1, 2),
                    'type': 'Decreto-Lei',
                    'number': '1/2002',
                    'creator': 'Ministério da Economia',
                    'pages': '6 - 7',
                    'pdf_id': 584725}

        del pubs[0]['text']
        del pubs[0]['summary']

        self.assertEqual(expected, pubs[0])
