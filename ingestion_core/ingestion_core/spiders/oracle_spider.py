import scrapy

class OracleSpider(scrapy.Spider):
    name = "oracle_agent"
    # The master directory of all essays
    start_urls = ['http://www.paulgraham.com/articles.html']

    def parse(self, response):
        # 1. Extract every link on the page that ends in .html
        links = response.css('a::attr(href)').re(r'.*\.html')
        
        # 2. Command the agent to follow every single link autonomously
        for link in links:
            if link != 'index.html':  # Skip the homepage
                yield response.follow(link, callback=self.parse_essay)

    def parse_essay(self, response):
        # 3. Extract all raw text from the essay
        paragraphs = response.css('body ::text').getall()
        
        # 4. Clean the data (remove blank spaces and join into one massive block)
        full_text = ' '.join(p.strip() for p in paragraphs if p.strip())
        
        # 5. Data Quality Control: Only save essays with actual content
        if len(full_text) > 500:
            yield {
                'title': response.css('title::text').get(default='Paul Graham Essay'),
                # RAG best practice: Chunking. We take the first 4000 characters 
                # to ensure the mathematical vector remains highly concentrated.
                'content': full_text[:4000], 
                'author': "Paul Graham",
                'source_url': response.url
            }