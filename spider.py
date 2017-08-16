import requests
from bs4 import BeautifulSoup


class MovieSpider(object):
    MOVIE_URL = 'https://movie.douban.com/cinema/nowplaying/shanghai/'
    COMMENT_URL = 'https://movie.douban.com/subject/{movie_id}/comments'

    def __init__(self):
        self.move_list = []

    @staticmethod
    def get_res(url, params=None):
        res = requests.get(url, params=params)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup

    def get_moves(self):
        res = self.get_res(self.MOVIE_URL)
        now_playing_div = res.find('div', id='nowplaying')
        now_playing_list = now_playing_div.find_all('li', class_='list-item')

        for item in now_playing_list:
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
            self.move_list.append(tmp)

    def get_movie_comments(self, movie_id):
        comment_text_list = []
        url = self.COMMENT_URL.format(movie_id=movie_id)
        for start in range(0, 100, 21):
            res = self.get_res(url, params={'start': start,
                                            'limit': 20,
                                            'sort': 'new_score'})
            comment_list = res.find('div', id='comments').find_all('div', class_='comment-item')
            for item in comment_list:
                comment = item.find('div', class_='comment')
                comment_content = comment.find('p').contents[0].strip()
                rating = comment.find('span', class_='rating').attrs['title']
                comment_text_list.append((rating, comment_content))
        return comment_text_list

if __name__ == '__main__':
    s = MovieSpider()
    s.get_moves()
