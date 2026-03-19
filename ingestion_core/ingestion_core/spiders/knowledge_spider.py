import scrapy

class KnowledgeSpider(scrapy.Spider):
    # The unique identifier for this specific crawler
    name = "knowledge_agent"
    
    # The starting point for the swarm
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
    ]

    def parse(self, response):
        # Extract the core data blocks
        for quote in response.css('div.quote'):
            yield {
                'content': quote.css('span.text::text').get(),
                'author': quote.css('span small.author::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
                'source_url': response.url
            }

        # Autonomous Navigation: Find the 'Next' page button and follow it
        next_page = response.css('li.next a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)