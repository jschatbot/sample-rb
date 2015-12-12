#!/usr/bin/env ruby
# -*- coding: utf-8; mode: ruby -*-

require 'net/https'
require 'uri'
require 'json'
require 'optparse'

class API

  def initialize(base, proxy_host=nil, proxy_port=nil)
    @base = base
    @proxy_host = proxy_host
    @proxy_port = proxy_port
  end

  def basic_auth(user, passwd)
    @ba_user = user
    @ba_passwd = passwd
  end

  def get(method, params)
    params = URI.encode_www_form(params)
    uri = URI.parse(@base + method + '?' + params)
    req = Net::HTTP::Get.new(uri.request_uri)
    send_request(uri, req)
  end

  def post(method, body)
    uri = URI.parse(@base + method)
    req = Net::HTTP::Post.new(uri.request_uri,
                              initheader = {'Content-Type' =>'application/json', 'charset' => 'UTF-8'})
    req.body = JSON.generate(body)
    send_request(uri, req)
  end

  def send_request(uri, req)
    req.basic_auth(@ba_user, @ba_passwd) if @ba_user
    http = Net::HTTP::Proxy(@proxy_host, @proxy_port).new(uri.host, uri.port)
    http.open_timeout = 5
    http.read_timeout = 120
    http.verify_mode = OpenSSL::SSL::VERIFY_NONE
    http.use_ssl = true
    res = nil
    http.start { res = http.request(req) }
    case res
    when Net::HTTPSuccess
      JSON.parse(res.body)
    else
      res.value
    end
  end

  def sentences(s)
    get('/jmat/sentence', { query: s })['sentences']
  end

  def morphs(s)
    get('/jmat/morph', { query: s })['morphs']
  end

  def markov_chain(seed)
    get('/tk/markov',
        { surface: seed['norm_surface'], pos: seed['pos'] })['morphs']
  end

  def rewrite(morphs)
    post('/tk/rewrite', { rule: 'test_rule.txt', morphs: morphs })['morphs']
  end

  def trigger(morphs)
    post('/tk/trigger', { rule: 'test_script.txt', morphs: morphs })['texts']
  end

  def search_tweet(query)
    get('/search/tweet', { query: query, limit: 3 })['texts']
  end

  def search_reply(query)
    get('/search/reply', { query: query, limit: 3 })['texts']
  end

  def get_reply(name)
    get('/tweet/get_reply', { bot_name: name })
  end

  def send_tweet(name, message)
    post('/tweet/simple',
         { bot_name: name, message: message })['result'] == 'true'
  end

  def send_reply(name, mention_id, user_name, message)
    post('/tweet/send_reply',
         { bot_name: name,
           replies: [ { mention_id: mention_id, user_name: user_name,
                        message: message } ] })[0] == 'true'
  end
end

def to_chainform(morphs)
  morphs.map {|m| m['norm_surface'] + ':' + m['pos'] }
end

def to_string(chain)
  chain[1...-1].map {|m| m.split(/:/)[0] }.join
end

def build_tweet(mention)
  seeds = []
  mentions = []
  $api.sentences(mention).each do |sent|
    morphs = $api.morphs(sent)
    seeds += morphs.select {|m| m['pos'] =~ /[^代]名詞/ }
    mentions.push(to_chainform(morphs))
  end

  texts = []
  5.times do
    ss = seeds.empty? ? [{ 'norm_surface' => 'BOS', 'pos' => 'BOS' }] : seeds
    ss.each do |s|
      c = $api.markov_chain(s)
      texts.push(to_string($api.rewrite(c))) unless c.empty?
    end
  end
  mentions.each {|m| $api.trigger(m).each {|t| texts.push(t) } }
  seeds.each do |s|
    $api.search_tweet(s['norm_surface']).map do |t|
      texts.push($api.sentences(t.chomp).map do |sent|
                   to_string($api.rewrite(to_chainform($api.morphs(sent))))
                  end.join(' '))
    end
    $api.search_reply(s['norm_surface']).map do |t|
      texts.push($api.sentences(t.chomp).map do |sent|
                   to_string($api.rewrite(to_chainform($api.morphs(sent))))
                  end.join(' '))
    end
  end
  texts.sample
end

$api = API.new('https://52.68.75.108/') # 社外
$api.basic_auth('secret', 'js2015cps')
  
OptionParser.new do |opt|
  opt.on('-t BOT_NAME') {|v| $name = v }
  opt.parse!(ARGV)
end

if $name
  rs = $api.get_reply($name)
  STDERR.puts "grade: #{rs['grade']}"
  rs['replies'].each do |r|
    t = build_tweet(r['text'].rstrip)
    $api.send_reply($name, r['mention_id'], r['user_name'], t)
  end
else
  ARGF.each do |line|
    puts build_tweet(line.rstrip)
  end
end
