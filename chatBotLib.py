# -*- coding: utf-8 -*-
import random
import urllib
import urllib2
import json

#
# シードを含むツイートからランダムに1ツイート選択する
# param  シード
# return 選択したツイート
#
def getKeywordTweet(keyword):

	# file open
	FH = open('tweet_line_corpus.txt')
	data = FH.read()
	FH.close()

	# get tweets (have keyword)
	hits = []
	tweets = data.split('\n')
	for tweet in tweets:
		if keyword in tweet:
			hits.append(tweet)
	if hits != []:
		# シードを含むツイートが存在すればその中からランダムに選択する
		return hits[random.randint(0, len(hits) - 1)]
	else:
		# 存在しなければ全ツイートからランダムに返す
		return tweets[random.randint(0, len(tweets) - 1)]

#
# リプライツイートからシードを抽出する
# param  リプライツイート
# return 抽出したシード
#
def morph(sentence):
	# この品詞順でリプライツイートからシードを決定する
	priority=[u'固有地名',u'固有商品',u'固有一般',u'名詞サ変',u'名詞ザ変',u'一般名詞',u'固有組織',u'接続詞',u'助詞']
	url = 'http://10.243.251.70/jmat/morph?query=%s'%urllib.quote(sentence)
	response = urllib2.urlopen(url)
	html = response.read()
	dic=json.loads(html)

	count={}

	for mor in dic["morphs"]:
		count.setdefault(mor["pos"],[])
		count[mor["pos"]].append(mor["norm_surface"])

	for pri in priority:
	    if pri in count.keys():
		return count[pri][0]

#
# 進化状態を受け取る
# param
# return 進化状態(0:つぼ, 1:きのこ, 2:さそり)
#
def get_grade(bot_name):
    url = 'http://10.243.251.70/tweet/get_reply?bot_name=%s'%bot_name
    response = urllib2.urlopen(url)
    html = response.read()
    dic=json.loads(html)
    return dic["grade"]
