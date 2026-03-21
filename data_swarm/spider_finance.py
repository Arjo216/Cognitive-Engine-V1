import scrapy
from scrapy.crawler import CrawlerProcess

class SecEdgarSpider(scrapy.Spider):
    name = "sec_edgar"
    # SEC strictly requires a valid User-Agent with an email, or they IP-ban you
    custom_settings = {
        'USER_AGENT': 'FounderOracle Research Engine (oraclecrawlerbot123@gmail.com)', 
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5, # Polite rate-limiting
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'finance_corpus.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }

    # Grabbing the latest 10-K and 10-Q filings
    start_urls = [
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-k&count=50&output=atom",
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-q&count=50&output=atom"
    ]

    def parse(self, response):
        self.logger.info("🟢 Breaching SEC EDGAR Financial Database...")
        response.selector.register_namespace('atom', 'http://www.w3.org/2005/Atom')
        entries = response.xpath('//atom:entry')

        for entry in entries:
            title = entry.xpath('atom:title/text()').get(default='').strip()
            summary = entry.xpath('atom:summary/text()').get(default='').strip()
            url = entry.xpath('atom:link/@href').get(default='')

            if url:
                # The SEC feed gives relative URLs, we must make them absolute
                url = response.urljoin(url)

            yield {
                "title": f"SEC Filing: {title}",
                "content": f"Filing Summary: {summary} Note: Full financial tables require deep XBRL parsing.",
                "author": "U.S. Securities and Exchange Commission",
                "source_url": url,
                "domain": "finance",
                "doc_type": "sec_filing"
            }

if __name__ == "__main__":
    print("🚀 Igniting Finance Spider...")
    process = CrawlerProcess()
    process.crawl(SecEdgarSpider)
    process.start()