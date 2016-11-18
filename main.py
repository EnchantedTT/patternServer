from pattern.en import parse, parsetree, wordnet, NOUN, Sentence
import sys
import json
from flask import Flask, request, jsonify
from flask_json import FlaskJSON, JsonError, json_response, as_json
import redis
import features
import pickle

app = Flask(__name__)
FlaskJSON(app)

pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
sentCache = redis.Redis(connection_pool=pool)

#parse sentence with pattern, get parsed sentences in cache if not None
def parseSentence(data):
	data = json.dumps(data, indent=4)
	sentences = json.loads(data)
	parsedSents = []
	for sent in sentences:
		text = ' '.join(w['w'] for w in sent)
		cache_key = 'PATTERN' + '_'.join(w['w'] for w in sent)
		if sentCache.get(cache_key):
			#print "cache!"
			parsedSents.append(pickle.loads(sentCache.get(cache_key)))
		else:
			s = parsetree(text, relations=True, lemmata=True)
			if len(s) != 1:
				s = None
			else:
				s = s[0]
				if s.stop != len(sent):
					s = None
			sentCache.set(cache_key, pickle.dumps(s), ex=180)
			parsedSents.append(s)
	return parsedSents, sentences
'''
#parse sentence with pattern, get parsed sentences in cache if not None
def parseSentence(data):
	data = json.dumps(data, indent=4)
	sentences = json.loads(data)
	parsedSents = []
	for sent in sentences:
		text = ' '.join(w['w'] for w in sent)
		s = parsetree(text, relations=True, lemmata=True)
		if len(s) != 1:
			s = None
		else:
			s = s[0]
			if s.stop != len(sent):
				s = None
		parsedSents.append(s)
	return parsedSents, sentences
'''

@app.route("/counts", methods=['POST'])
def getCounts():
	data = request.get_json(force=True)
	result = dict()
	try:
		value = data['text']
		pss, ss = parseSentence(value)
		errors, fs = features.getCountsFeatures(pss, ss)
		result['errors'] = errors
		result['features'] = fs
	except(KeyError, TypeError, ValueError):
		raise JsonError(description='Invalid value.')
	return jsonify(result)

@app.route("/article", methods=['POST'])
def getArticle():
	data = request.get_json(force=True)
	result = dict()
	try:
		value = data['text']
		pss, ss = parseSentence(value)
		errors, fs = features.getArticleFeatures(pss, ss)
		result['errors'] = errors
		result['features'] = fs
	except(KeyError, TypeError, ValueError):
		raise JsonError(description='Invalid value.')
	return jsonify(result)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5011, threaded=True)