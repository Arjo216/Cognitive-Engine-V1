import scrapy
from scrapy.crawler import CrawlerProcess
import json

class ArxivSpider(scrapy.Spider):
    name = "arxiv_ai"
    # We query the official API for the 100 most recent AI/ML papers
    start_urls = [
        "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=100"
    ]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) FounderOracle/1.0',
        'LOG_LEVEL': 'INFO',
        'FEEDS': {
            'science_corpus.json': {
                'format': 'json',
                'overwrite': True
            }
        }
    }

    def parse(self, response):
        self.logger.info("🟢 Infiltrating ArXiv Scientific Database...")
        # ArXiv uses Atom XML namespaces
        response.selector.register_namespace('atom', 'http://www.w3.org/2005/Atom')
        entries = response.xpath('//atom:entry')
        
        for entry in entries:
            # Clean the text using whitespace normalization
            title = entry.xpath('atom:title/text()').get(default='').strip()
            summary = entry.xpath('atom:summary/text()').get(default='').strip()
            summary = ' '.join(summary.split()) # Remove messy line breaks
            
            author = entry.xpath('atom:author/atom:name/text()').get(default='Unknown')
            url = entry.xpath('atom:id/text()').get(default='')

            yield {
                "title": f"Scientific Paper: {title}",
                "content": f"Abstract: {summary}",
                "author": author,
                "source_url": url,
                "domain": "science",
                "doc_type": "arxiv_paper"
            }

if __name__ == "__main__":
    print("🚀 Igniting Science Spider...")
    process = CrawlerProcess()
    process.crawl(ArxivSpider)
    process.start()