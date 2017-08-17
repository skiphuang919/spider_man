import sys
import requests
import re
import pprint
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime


class MovieSpider(object):
    MOVIE_URL = 'https://movie.douban.com/cinema/nowplaying/shanghai/'
    COMMENT_URL = 'https://movie.douban.com/subject/{movie_id}/comments'
    REFRESH_INTERVAL_SEC = 6 * 60 * 60
    RATING_LIST = ('很差', '较差', '还行', '推荐', '力荐', '其他')

    def __init__(self, move_name_to_analyze):
        self.move_name_to_analyze = move_name_to_analyze
        self.move_list = []
        client = MongoClient()
        self.movie_collection = client.movie_db.movie_collection

    @staticmethod
    def get_res(url, params=None):
        res = requests.get(url, params=params)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup

    @staticmethod
    def hours_span_from_now(start_time):
        return (datetime.utcnow() - start_time).seconds

    def get_movies(self):
        res = self.get_res(self.MOVIE_URL)
        now_playing_div = res.find('div', id='nowplaying')
        now_playing_list = now_playing_div.find_all('li', class_='list-item') if now_playing_div else []

        for item in now_playing_list:
            print('------{}------'.format(item['data-title']))
            tmp = dict()
            tmp['id'] = item['data-subject']
            tmp['name'] = item['data-title']
            tmp['score'] = item['data-score']
            tmp['release'] = item['data-release']
            tmp['duration'] = item['data-duration']
            tmp['region'] = item['data-region']
            tmp['director'] = item['data-director']
            tmp['actors'] = list(map(lambda x: x.strip(), item['data-actors'].split('/')))
            tmp['score'] = item['data-score']
            tmp['comment'] = self._get_movie_comments(tmp['id'])
            tmp['date'] = datetime.utcnow()
            self.move_list.append(tmp)
        print('Get {} movies'.format(len(self.move_list)))
        if self.move_list:
            res = self.movie_collection.insert_many(self.move_list)
            print('Insert {} items'.format(len(res.inserted_ids)))

    def _get_movie_comments(self, movie_id):
        comment_text_list = []
        url = self.COMMENT_URL.format(movie_id=movie_id)
        for start in range(0, 100, 21):
            res = self.get_res(url, params={'start': start,
                                            'limit': 20,
                                            'sort': 'new_score'})
            comment_div = res.find('div', id='comments')
            comment_list = comment_div.find_all('div', class_='comment') if comment_div else []
            for item in comment_list:
                comment_content = item.find('p').contents[0].strip()
                rating_span = item.find('span', class_='rating')
                rating = rating_span.attrs['title'] if rating_span else ''
                comment_text_list.append({'comment_content': comment_content,
                                          'rating': rating})
        return comment_text_list

    def _analyze_comments(self, comments):
        rating_info = {item: 0 for item in self.RATING_LIST}
        for c in comments:
            level = c['rating'] if c['rating'] in self.RATING_LIST else '其他'
            rating_info[level] += 1
        return rating_info

    def pump_key_words(self):
        pass

    def analyze_movie(self):
        info_list = []
        name_regex = re.compile(self.move_name_to_analyze)
        for item in self.movie_collection.find({'name': name_regex}):
            tmp = dict()
            tmp['name'] = item['name']
            tmp['score'] = item['score']
            tmp['comment_info'] = self._analyze_comments(item['comment'])
            info_list.append(tmp)
        return info_list

    def run(self):
        movie = self.movie_collection.find_one()
        if not movie or self.hours_span_from_now(movie['date']) > self.REFRESH_INTERVAL_SEC:
            print('refresh data...')
            self.get_movies()
            print('refresh done...')
        else:
            print('data refreshed...')
        res = self.analyze_movie()
        pprint.pprint(res)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python spider [movie name]')
    else:
        movie_name = sys.argv[-1]
        s = MovieSpider(movie_name)
        s.run()
