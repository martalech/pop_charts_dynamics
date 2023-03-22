import scrapy
import requests
import io
import re
import numpy as np

from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from urllib.parse import urljoin

base_url = "https://www.hawes.com/"
first_year = 1958
last_year = 2022

# https://stackoverflow.com/questions/59130672/how-to-scrape-pdfs-using-python-specific-content-only
# https://pypdf2.readthedocs.io/en/latest/user/extract-text.html
class BooksSpider(scrapy.Spider):
    name = "NYTBestsellers"

    def generate_years (self):
        current_year = first_year

        while current_year < last_year:
            yield current_year
            current_year += 1

    def start_requests(self):
        #for year in self.generate_years():
        for year in [2000, 2001, 2006, 2007, 2008, 2012, 2014]:
            yield scrapy.Request(url=urljoin(base_url, f"{year}/{year}.htm"), callback=self.parse)
        
    def parse(self, response):
        year = response.url.split("/")[-2]
        date_hrefs = response.css('center a::attr(href)').getall()
        
        for date_href in date_hrefs:
            if year in date_href:
                url = urljoin(base_url, f"{year}/{date_href}")
                response = requests.get(url)
                with io.BytesIO(response.content) as f:
                    pdf = PdfReader(f)
                    # take non fiction
                    page = pdf.pages[1]
                    books_data = page.extract_text().split("\n")[8:]
                    i = 0
                    while i < len(books_data):
                        book_data = books_data[i].strip()
                        if "(8 of the top 10 are about September 11.)" in book_data:
                            i += 1
                            continue
                        if book_data == "":
                            i += 1
                            continue
                        position = re.findall(r'\d+', book_data[0:3])
                        if len(position) == 0:
                            i += 1
                            continue
                        
                        book_data = book_data.replace("1-", "10")
                        last_weeks_weeks_on_chart = re.findall(r'(?:\d+ \d+)|(?:-- \d+)|(?:\d+  \d+)|(?:--  \d+)', book_data[-7:])

                        while len(last_weeks_weeks_on_chart) == 0 and i < len(books_data) - 1:
                            last_weeks_weeks_on_chart += re.findall(r'(?:\d+ \d+)|(?:-- \d+)|(?:\d+  \d+)|(?:--  \d+)', books_data[i + 1][-7:])
                            book_data += books_data[i + 1]
                            i += 1
                        if last_weeks_weeks_on_chart == []:
                            print(date_href)
                            print("Error: ", book_data)
                            print(books_data)
                            print(i)
                            break
                        book_data = book_data.strip()
                        last_weeks_weeks_on_chart = last_weeks_weeks_on_chart[0].split()
                        if book_data != "":
                            position_end_index = len(position[0]) + 1
                            if last_weeks_weeks_on_chart[0] != "--":
                                last_week_position_length = len(last_weeks_weeks_on_chart[0]) + len(last_weeks_weeks_on_chart[1]) + 2
                                last_week_position = int(last_weeks_weeks_on_chart[0])
                                weeks_on_chart = int(last_weeks_weeks_on_chart[1])
                            else:
                                last_week_position_length = len(last_weeks_weeks_on_chart[1]) + 5
                                last_week_position = np.nan
                                weeks_on_chart = int(last_weeks_weeks_on_chart[1])
                            author_title = book_data[position_end_index:-last_week_position_length]

                            yield {
                                "author_title": author_title,
                                'first_day_of_the_week': date_href[0:-4],
                                'position': int(position[0]),
                                'last_week_position': last_week_position,
                                'weeks_on_chart': weeks_on_chart
                            }
                        i += 1
