import os
import logging.config

redis_conf = {
	'host' : 'localhost',
	'port' : 6379,
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING = {
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': {
		'verbose': {
			'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
		},
		'simple': {
			'format': '%(asctime)s %(message)s'
		},
	},
	'handlers': {
		'console':{
			'level':'DEBUG',
			'class':'logging.StreamHandler',
			'formatter': 'simple'
		},
		'file': {
			'level': 'DEBUG',
			'class': 'logging.FileHandler',
			'filename': BASE_DIR + '/records.log',
			'formatter': 'simple',
		},
	},
	'loggers': {
		'pattern.server': {
			'handlers': ['console', 'file'],
			'level': 'DEBUG',
		},
	}
}

logging.config.dictConfig(LOGGING)