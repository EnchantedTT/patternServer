from pattern.en import parse, parsetree, wordnet, NOUN, Sentence
import sys
import json
from flask import Flask, request, jsonify
from flask_json import FlaskJSON, JsonError, json_response, as_json
import redis
import features
import pickle
import logging
import settings

app = Flask(__name__)
FlaskJSON(app)

LOGGER = logging.getLogger("pattern.server")

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
	result = dict()
	try:
		data = request.get_json(force=True)
		value = data['text']
		pss, ss = parseSentence(value)
		errors, fs = features.getCountsFeatures(pss, ss)
		result['errors'] = errors
		result['features'] = fs
	except Exception as e:
		LOGGER.info("Count Server: " + str(type(e)))
		raise JsonError(description='Invalid Input.')
	return jsonify(result)

@app.route("/article", methods=['POST'])
def getArticle():
	result = dict()
	try:
		data = request.get_json(force=True)
		value = data['text']
		pss, ss = parseSentence(value)
		errors, fs = features.getArticleFeatures(pss, ss)
		result['errors'] = errors
		result['features'] = fs
	except Exception as e:
		LOGGER.info("Article Server: " + str(type(e)))
		raise JsonError(description='Invalid Input.')
	return jsonify(result)

if __name__ == "__main__":
	app.run(host='127.0.0.1', port=50110, threaded=True)
