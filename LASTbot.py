# -*- coding: utf-8 -*-
import requests
import json
import chatBotLib
class API:
  def __init__(self, base):
    self.base = base

  def basic_auth(self, user, passwd):
    self.user = user
    self.passwd = passwd

  def get(self, method, query):
    return requests.get(self.base+method, params=query).json()

  def post(self, method, query):
    headers = { 'content-type':'application/json' }
    return requests.post(self.base+method, json.dumps(query), headers=headers).json()

  def sentences(self, query):
    return self.get('/jmat/sentence', {'query':query})

  def morphs(self, query):
    return self.get('/jmat/morph', {'query':query})

  def markov_chain(self, surface, pos):
    return self.get('/tk/markov', {'surface':surface, 'pos':pos})

  def search_tweet(self, query):
    return self.get('/search/tweet', {'query':query})

  def get_reply(self, bot_name):
    return self.get('/tweet/get_reply', {'bot_name':bot_name})

  def simple_tweet(self, query):
    self.get('/search/reply', query)

  def send_reply(self, bot_name, replies):
    return self.post('/tweet/send_reply', {'bot_name':bot_name , 'replies':replies})

  def rewrite(self, rule_file, morphs):
    return self.post('/tk/rewrite', {'rule':rule_file , 'morphs':morphs})

  def rewrite_input(self, message):
    morphs = []
    text = ''
    dic = self.morphs(message)
    for d in dic['morphs']:
      text += d['norm_surface']
      text += (':')
      text += d['pos']
      morphs.append(text)
      text = ''
    return morphs

  def rewrite_output(self, rr):
    dic = rr
    st = ''
    for d in dic['morphs']:
      s = d.split(':')
      if 'BOS' in s[1] or "EOS" in s[1]:
        continue
      st += s[0]
    return st

  def trigger(self, rule_file, morphs):
    return self.post('/tk/trigger', {'rule':rule_file, 'morphs':morphs})

  def make_reply(self, rule_rewrite, rule_trigger, mention_id, user_name, text):
    morphs = api.rewrite_input(text)
    messages = api.trigger(rule_trigger, morphs)
    if len(messages['texts']) != 0:
        message = messages['texts'][0]
    else:
        message = 'わかりません'
    if message == '':
        # リプライがシナリオのルール以外
        seed = chatBotLib.morph(text)
        message = chatBotLib.getKeywordTweet(seed)
        # 形態素列の書き換え
        morphs = api.rewrite_input(message)
        rr = api.rewrite(rule_rewrite, morphs)
        message = api.rewrite_output(rr)

    return { 'mention_id':mention_id , 'user_name':user_name, 'message':message }


# main
api = API('http://10.243.251.70')
bot_name = 'js_tubot05'
rule_rewrite0 = 'rewrite_c00.txt'
rule_trigger0 = 'scenario_c00.txt'
rule_rewrite12 = 'rewrite_c05.txt'
rule_trigger12 = 'scenario_c05.txt'

# リプライの取得
replies = []
for x in api.get_reply(bot_name).get('replies'):
    grade = chatBotLib.get_grade(bot_name)
    rule_rewrite = ''
    rule_trigger = ''
    if grade == 0:
        rule_rewrite = rule_rewrite0
        rule_trigger = rule_trigger0
    else:
        rule_rewrite = rule_rewrite12
        rule_trigger = rule_trigger12
    replies.append( api.make_reply(rule_rewrite, rule_trigger, x.get('mention_id'), x.get('user_name'), x.get('text')) )

# リプライの送信
api.send_reply( bot_name, replies)
