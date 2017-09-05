# spider_man
抓取豆掰正在热映的电影，分析影评

## flow
* 抓取最新数据持久化于mongoDB
* 分析指定电影的短评生产词云

## require
* requests
* ThreadPool
* bs4
* mongoDB
* jieba
* worldclound

## example
```
$ python spider 二十二
fresh data ...
--------------------
Analyze result:
Building prefix dict from the default dictionary ...
Loading model from cache /tmp/jieba.cache
Loading model cost 0.806 seconds.
Prefix dict has been built succesfully.
{'comment_info': {'其他': 2, '力荐': 51, '很差': 4, '推荐': 17, '较差': 6, '还行': 20},
 'name': '二十二',
 'score': '8.9'}

```
![generated img](https://github.com/skiphuang919/spider_man/blob/master/demo.jpg)
