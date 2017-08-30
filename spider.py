import sys
import requests
import re
import pprint
import jieba
import os
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from wordcloud import WordCloud

d = os.path.dirname(__file__)


class MovieSpider(object):
    MOVIE_URL = 'https://movie.douban.com/cinema/nowplaying/shanghai/'
    COMMENT_URL = 'https://movie.douban.com/subject/{movie_id}/comments'
    REFRESH_INTERVAL_SEC = 6 * 60 * 60
    RATING_LIST = ('很差', '较差', '还行', '推荐', '力荐', '其他')

    CH_PATTERN = re.compile(r'^[\u4e00-\u9fa5]+$')

    TMP_FILE_PATH = os.path.join(d, 'tmp.txt')

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

    def extract_words_to_file(self, comments):
        with open(self.TMP_FILE_PATH, 'a') as f:
            for comment in comments:
                comment_content = comment['comment_content']
                seg_list = filter(lambda x: re.match(self.CH_PATTERN, x) is not None,
                                  jieba.lcut(comment_content, cut_all=False))
                f.write(' '.join(seg_list))

    def generate_comment_cloud(self, comments):

        self.extract_words_to_file(comments)
        word_cloud = WordCloud(font_path='/home/kevin/Downloads/DroidSansFallbackFull.ttf',
                               width=1200,
                               height=800)

        with open(self.TMP_FILE_PATH) as f:
            word_cloud.generate(f.read())

        os.remove(self.TMP_FILE_PATH)

        image = word_cloud.to_image()
        image.show()

    def analyze_movie(self):
        result = dict()
        movie_item = self.movie_collection.find_one({'name': self.move_name_to_analyze})
        if movie_item:
            self.generate_comment_cloud(movie_item['comment'])
            result['name'] = movie_item['name']
            result['score'] = movie_item['score']
            rating_info = {item: 0 for item in self.RATING_LIST}
            for c in movie_item['comment']:
                level = c['rating'] if c['rating'] in self.RATING_LIST else '其他'
                rating_info[level] += 1
                result['comment_info'] = rating_info
        return result

    def run(self):
        movie = self.movie_collection.find_one()
        if not movie or self.hours_span_from_now(movie['date']) > self.REFRESH_INTERVAL_SEC:
            print('refresh data...')
            self.movie_collection.delete_many({})
            self.get_movies()
            print('refresh done...')
        else:
            print('fresh data ...')
        print('-'*20)
        print('Analyze result:')
        res = self.analyze_movie()
        pprint.pprint(res)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python spider [movie name]')
    else:
        movie_name = sys.argv[-1]
        s = MovieSpider(movie_name)
        s.run()
