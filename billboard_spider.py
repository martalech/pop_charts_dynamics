import scrapy

from datetime import datetime, timedelta
from urllib.parse import urljoin

base_url = "https://www.billboard.com/charts/hot-100/"
first_week = datetime(1958, 8, 4)
last_week = datetime(2023, 1, 6)

class BillboardSpider(scrapy.Spider):
    name = "billboardhot100"

    def generate_weeks(self):
        current_week = first_week

        while current_week < last_week:
            yield current_week.strftime("%Y-%m-%d")
            current_week += timedelta(weeks=1)

    def start_requests(self):
        for week in self.generate_weeks():
            yield scrapy.Request(url=urljoin(base_url, week), callback=self.parse)
        
    def parse(self, response):
        date = response.url.split("/")[-2]

        hits_containers = response.css('div.o-chart-results-list-row-container')
        for hit_container in hits_containers:
            c_titles = hit_container.css('h3.c-title::text').getall()
            c_taglines = hit_container.css('p.c-tagline::text').getall()

            has_songwriters = len([el for el in c_titles if "Songwriter(s)" in el]) > 0
            has_producers = len([el for el in c_titles if "Producer(s)" in el]) > 0
            has_label = len([el for el in c_titles if "Imprint/Promotion Label" in el]) > 0

            yield {
                'first_day_of_the_week': date,
                'artist': hit_container.css('span.c-label::text').getall()[-7].strip(),
                'song_name': hit_container.css('h3.c-title::text').get().strip(),
                'position': hit_container.css('span.c-label::text').get().strip(),
                'last_week_position': hit_container.css('span.c-label::text').getall()[-3].strip(),
                'peak_position': hit_container.css('span.c-label::text').getall()[-2].strip(),
                'weeks_on_chart': hit_container.css('span.c-label::text').getall()[-1].strip(),
                'songwriters': c_taglines[-1 - 1 * int(has_label) - 1 * int(has_producers)] if has_songwriters else "Not Listed",
                'producers': c_taglines[-1 - 1 * int(has_label)] if has_producers else "Not Listed",
                'promotion_label': c_taglines[-1] if has_label else "Not Listed",
            }