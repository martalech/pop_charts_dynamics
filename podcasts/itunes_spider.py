import scrapy

from datetime import datetime, timedelta
from urllib.parse import urljoin

base_url = "http://www.itunescharts.net/us/charts/podcasts/"
category = "/full"
first_day = datetime(2009, 11, 24)
last_day = datetime(2023, 2, 23)

class ITunesSpider(scrapy.Spider):
    name = "iTunesPodcasts"

    def generate_days(self):
        current_day = first_day

        while current_day < last_day:
            yield current_day.strftime("%Y/%m/%d")
            current_day += timedelta(days=1)

    def start_requests(self):
        for day in self.generate_days():
            yield scrapy.Request(url=urljoin(base_url, day), callback=self.parse)
        
    def parse(self, response):
        date = response.url.split("/")[-3] + "-" + response.url.split("/")[-2] + "-" + response.url.split("/")[-1]

        podcasts_container = response.css('li[id^="chart_us"]')

        for podcast_container in podcasts_container:
            title_a = podcast_container.css('span.entry a::text').get()

            yield {
                'day': date,
                'title': podcast_container.css('span.entry::text').get().strip() if title_a is None else title_a.strip(),
                'position': podcast_container.css('span.no::text').get().strip(),
            }