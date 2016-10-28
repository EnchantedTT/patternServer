from pattern.en import parse, parsetree, wordnet, NOUN, Sentence
import sys
import json
from flask import Flask, request, jsonify
from flask_json import FlaskJSON, JsonError, json_response, as_json
import redis
import features

app = Flask(__name__)
FlaskJSON(app)

pool = redis.ConnectionPool(host='0.0.0.0', port=6379)
sentCache = redis.Redis(connection_pool=pool)

def parseSentence(data):
	data = json.dumps(data, indent=4)
	sentences = json.loads(data)
	parsedSents = []
	for sent in sentences:
		text = ' '.join(w['w'] for w in sent)
		if sentCache.get(text):
			parsedSents.append(Sentence(sentCache.get(text)))
		else:
			s = parsetree(text, relations=True, lemmata=True)
			if len(s) != 1:
				s = None
			else:
				s = s[0]
				if s.stop != len(sent):
					s = None
			sentCache.set(text, repr(s), ex=3)
			parsedSents.append(s)
	return parsedSents, sentences

@app.route("/counts", methods=['POST'])
def getCounts():
	data = request.get_json(force=True)
	result = dict()
	try:
		value = data['text']
		pss, ss = parseSentence(value)
		print len(pss), len(ss)
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
		features.getArticleFeatures(pss, ss)
	except(KeyError, TypeError, ValueError):
		raise JsonError(description='Invalid value.')
	return jsonify(result)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5011)