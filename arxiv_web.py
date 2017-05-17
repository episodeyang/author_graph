import threading
import time

from web_crawler.web_crawler import SimpleCrawler

visited = {}
# queue = ['https://www.arxiv.org']
queue = ['https://arxiv.org/abs/1506.02078']
# https://arxiv.org/find/cs/1/au:+Karpathy_A/0/1/0/all/0/1
# URL_MASK = '^(https?://(www\.)?arxiv.org)?(/[^/](.*))?$'
URL_MASK = '^(https?://(www\.)?arxiv.org)?(/(abs|find)/(.*))?$'
# queue = ['http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton']
# URL_MASK = '^(https?://export.arxiv.org)?(/[^/](.*))?$'

global_lock = threading.Lock()
threads = []
for i in range(1):
    spider = SimpleCrawler(global_lock, 'Thread-{}'.format(i + 1), visited, queue,
                           url_mask=URL_MASK,
                           dump_path='../dump',
                           index_path='../index.yml',
                           query_delay=1.0
                           )
    spider.start()
    time.sleep(5)
