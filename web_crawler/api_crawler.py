import ssl
import threading
import urllib.request
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import re

REGEX_RELATIVE = re.compile('/[^/](.*)')


class SimpleCrawler(threading.Thread):
    def __init__(self, lock, name, visited, queue=None, root=None, url_mask=None, dump_path='./dump/{sanitized_url}',
                 index_path="./index.yaml", query_delay=1.0):
        threading.Thread.__init__(self)
        self.lock = lock
        self.dump_path = dump_path
        self.index_path = index_path
        self.name = name
        self.visited = visited
        self.queue = queue
        self.query_delay = query_delay
        if root:
            self.queue.append(root)
        if url_mask:
            self.url_mask = re.compile(url_mask)

    def get_dump_path(self, **kwargs):
        return self.dump_path.format(**kwargs)

    def crawl(self, url=None):
        with self.lock:
            if not url:
                if not self.queue:
                    return
                url = self.queue.pop(0)
            if url in self.visited:
                return
            self.visited[url] = True
            if not self.url_mask.match(url):
                return

        print(self.name + ' crawling ', url)

        try:
            with urllib.request.urlopen(url, context=ssl._create_unverified_context()) as response:
                # todo: add finite length
                html = response.read()
                with open(self.get_dump_path(url=url), 'w+') as f:
                    f.write(str(html))
            for link in self.find_links(html, self.url_mask, current_url=url):
                self.add_unique(link)
        except urllib.error.HTTPError as e:
            print(e)

        time.sleep(self.query_delay)

    @staticmethod
    def find_links(html, mask=None, current_url=''):
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.findAll('a'):
            try:
                if not mask or mask.match(a['href']) and a['href']:
                    url = a['href']
                    new_url = ('https://' + SimpleCrawler.get_net_location(
                        current_url) + url) if REGEX_RELATIVE.match(url) else url
                    # print("======", current_url, url, new_url, sep='\n')
                    yield new_url
            except KeyError:
                print('Warning: anchor has empty href.')
            except IndexError:
                print('Warning: url is empty')

    @staticmethod
    def get_net_location(url):
        return urlparse(url).netloc

    def add_unique(self, link):
        """adds a link if the link has not been visited."""
        with self.lock:
            if link not in self.visited:
                self.queue.append(link)

    def run(self):
        while self.queue:
            self.crawl()
        print('crawling finished')

    def __enter__(self):
        # todo: add loading index
        pass

    def __exit__(self):
        # todo: add saving index
        pass


visited = {}
# queue = ['https://www.arxiv.org']
queue = ['https://arxiv.org/abs/1506.02078']
# queue = ['http://export.arxiv.org/api/{method_name}?{parameters}']
# queue = ['http://export.arxiv.org/api/query?search_']
URL_MASK = '^(https?://(www\.)?arxiv.org)?(/[^/](.*))?$'

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
    # time.sleep(5)
