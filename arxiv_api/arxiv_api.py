# http://arxiv.org/help/api/user-manual#extension_elements
from __future__ import print_function

try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import feedparser
from requests.exceptions import HTTPError

API_ROOT_URI = 'http://export.arxiv.org/api/'

# TODO: Field queries ("Details of Query Construction")
QUERY_FIELDS = ["all", "ti", "au", "abs", "co", "jr", "cat", "rn", "id"]

CATEGORIES = ["stat.AP", "stat.CO", "stat.ML", "stat.ME", "stat.TH", "q-bio.BM",
              "q-bio.CB", "q-bio.GN", "q-bio.MN", "q-bio.NC", "q-bio.OT", "q-bio.PE", "q-bio.QM", "q-bio.SC",
              "q-bio.TO", "cs.AR", "cs.AI", "cs.CL", "cs.CC", "cs.CE", "cs.CG", "cs.GT", "cs.CV", "cs.CY", "cs.CR",
              "cs.DS", "cs.DB", "cs.DL", "cs.DM", "cs.DC", "cs.GL", "cs.GR", "cs.HC", "cs.IR", "cs.IT", "cs.LG",
              "cs.LO", "cs.MS", "cs.MA", "cs.MM", "cs.NI", "cs.NE", "cs.NA", "cs.OS", "cs.OH", "cs.PF", "cs.PL",
              "cs.RO", "cs.SE", "cs.SD", "cs.SC", "nlin.AO", "nlin.CG", "nlin.CD", "nlin.SI", "nlin.PS", "math.AG",
              "math.AT", "math.AP", "math.CT", "math.CA", "math.CO", "math.AC", "math.CV", "math.DG", "math.DS",
              "math.FA", "math.GM", "math.GN", "math.GT", "math.GR", "math.HO", "math.IT", "math.KT", "math.LO",
              "math.MP", "math.MG", "math.NT", "math.NA", "math.OA", "math.OC", "math.PR", "math.QA", "math.RT",
              "math.RA", "math.SP", "math.ST", "math.SG", "astro-ph", "cond-mat.dis-nn", "cond-mat.mes-hall",
              "cond-mat.mtrl-sci", "cond-mat.other", "cond-mat.soft", "cond-mat.stat-mech", "cond-mat.str-el",
              "cond-mat.supr-con", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nucl-ex", "nucl-th",
              "physics.acc-ph", "physics.ao-ph", "physics.atom-ph", "physics.atm-clus", "physics.bio-ph",
              "physics.chem-ph", "physics.class-ph", "physics.comp-ph", "physics.data-an", "physics.flu-dyn",
              "physics.gen-ph", "physics.geo-ph", "physics.hist-ph", "physics.ins-det", "physics.med-ph",
              "physics.optics", "physics.ed-ph", "physics.soc-ph", "physics.plasm-ph", "physics.pop-ph",
              "physics.space-ph", "quant-ph"]


# TODO: Do I want to support boolean operators?
# DONE: support keyword inputs.
def query(search_query=None, id_list=None, start=0, max_results=10, prune=True):
    # Gets a list of top results, each of which is a dict
    # NOTE: https://arxiv.org/help/api/user-manual#query_details
    query_list = []
    if search_query:
        query_list.append("search_query={}".format(quote_plus(search_query)))
    if id_list:
        query_list.append("id_list={}".format(','.join(id_list)))
    if start is not None:
        query_list.append("start={}".format(start))
    if max_results is not None:
        query_list.append("max_results={}".format(int(max_results)))

    query_string = API_ROOT_URI + 'query?{}'.format('&amp;'.join(query_list))
    # print(query_string)
    results = feedparser.parse(query_string)
    if results.get('status') != 200:
        # TODO: better error reporting
        raise Exception("HTTP Error " + str(results.get('status', 'no status')) + " in query")
    else:
        results = results['entries']

    for result in results:
        # Renamings and modifications
        mod_query_result(result)
        if prune:
            prune_query_result(result)

    return results


def mod_query_result(result):
    # Useful to have for download automation
    result['pdf_url'] = None
    for link in result['links']:
        if 'title' in link and link['title'] == 'pdf':
            result['pdf_url'] = link['href']

    result['affiliation'] = result.pop('arxiv_affiliation', 'None')
    result['arxiv_url'] = result.pop('link')
    result['title'] = result['title'].rstrip('\n')
    result['summary'] = result['summary'].rstrip('\n')
    result['authors'] = [d['name'] for d in result['authors']]

    if 'arxiv_comment' in result:
        result['arxiv_comment'] = result['arxiv_comment'].rstrip('\n')
    else:
        result['arxiv_comment'] = None
    if 'arxiv_journal_ref' in result:
        result['journal_reference'] = result.pop('arxiv_journal_ref')
    else:
        result['journal_reference'] = None
    if 'arxiv_doi' in result:
        result['doi'] = result.pop('arxiv_doi')
    else:
        result['doi'] = None


def prune_query_result(result):
    prune_keys = ['updated_parsed',
                  'published_parsed',
                  'arxiv_primary_category',
                  'summary_detail',
                  'author',
                  'author_detail',
                  'links',
                  'guidislink',
                  'title_detail',
                  'tags',
                  'id']
    for key in prune_keys:
        try:
            del result['key']
        except KeyError:
            pass


def download(obj, dirname='./'):
    # Downloads file in obj (can be result or unique page) if it has a .pdf link
    if 'pdf_url' in obj and 'title' in obj and obj['pdf_url'] and obj['title']:
        filename = dirname + obj['title'] + ".pdf"
        try:
            import urllib
            urllib.urlretrieve(obj['pdf_url'], filename)

            # Return the filename of the pdf
        except AttributeError:  # i.e. except python is python 3
            from urllib import request
            request.urlretrieve(obj['pdf_url'], filename)

        return filename
    else:
        print("Object passed in has no PDF URL, or has no title")
