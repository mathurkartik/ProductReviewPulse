from app_store_scraper import AppStore
from pprint import pprint

groww = AppStore(country='in', app_name='groww', app_id='1404871703')
groww.review(how_many=5)
pprint(groww.reviews)
