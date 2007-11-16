#!/usr/bin/env python
''' $ python when.py [-h|--help] [-f "format"] [date]
	Example dates:
		today
		ToDaY
		yesterday
		tomorrow
		1 day 3 weeks 4 hours ago
		now+ 42 minutes 1 second
		5 years ago
		monday
		NoW
		now
		3 January
		last thursDaY
		neXt sunday
		jan 3 4:20
		jan 3 4:20pm
		next friday 4:20 p/m/
		next friday 4:20 p.m.
	Output format is ISO [%Y-%m-%d %H:%M:%S] by default. you can specify your own with the -f flag.
	I'm just a program. I may be 100 lines of python, but I can still be confused very easily.
		When I do get confused, I usually calmly tell you through sys.stderr, then return a [probably] crap date.
'''
import sys, string, re, time

chunkify = chunk = lambda L, n=2: [L[i : (i + n)] for i in range(0, len(L), n)]

ISO_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def anydatetime(s, in_US=True):
	''' take a string supposedly representing a date and/or time in no particular format,
		and return the date and time in ISO format.
		'yesterday', and 'tomorrow' [capitalized or not] are special days which can only be accompanied by times.
			today is assumed if you only specify a time.
		'ago' is a keyword which must be preceded by alternations of numbers and strings in
			['days', 'day', 'months', 'month', 'years', 'year', 'weeks', 'week', 'hour', 'hours', 'minutes', 'minute', 'seconds', 'second']
			eg. '1 month 2 weeks 1 day ago', '2 years 1 day ago 2:10:40', '20 minutes ago'
		'now+' is similar to 'ago', but it must come before the alternations of numbers and strings.
		'next' and 'last' are keywords for absolute mode which add or subtract 7 to/from the date:
			'next tuesday'
			'last thursday'
		i tried to read your mind, so, pinch of salt, and all that.
		if you do NOT want me to assume that the month comes before the day before the year, specify in_US=False.
			that variable is only used if s does not contain a month spelled out.
	'''
	assert isinstance(s, (str, unicode)), "input s neither str, unicode"
	bad_tokens = None
	s = re.sub('[^\w\s\:\+]+', ' ', s).lower()	# strip out commas, hyphens, slashes, periods, etc.
	if s.endswith('ago') or s.startswith('now+'):
		# relative time
		tokens = s.split(' ')
		while '' in tokens:
			tokens.remove('')
		now = time.time()
		levels = {'second':1, 'minute':60, 'hour':3600, 'day':86400, 'week':604800, 'month':2592000, 'year':31556926}
		if s.endswith('ago'):
			tokens = tokens[:-1]
			direction = -1
		else:
			tokens = tokens[1:]
			direction = 1
		for n, level in chunkify(tokens, 2):
			if level.endswith('s'):
				level = level[:-1]
			if n.isdigit() and (level in levels):
				now += levels[level] * int(n) * direction
		ret = time.strftime(ISO_DATETIME_FORMAT, time.localtime(now))
	elif s in ['now', '']:
		ret = time.strftime(ISO_DATETIME_FORMAT)
	else:
		# absolute time
		date = {'Y':time.strftime('%Y'), 'm':time.strftime('%m'), 'd':time.strftime('%d'), 'H':'00', 'M':'00', 'S':'00'}
		long_months = [None, 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
		short_months = [None] + [m[:3] for m in long_months[1:]]
		long_days = [None, 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
		short_days = [None] + [d[:3] for d in long_days[1:]]
		days_in_month = dict(zip(range(1, 13), [31, (28 + int(0 == (int(date['Y']) % 4))), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]))
		pm = False
		if 'am' in s:
			s = s.replace('am', '')
		elif 'pm' in s:
			pm = True
			s = s.replace('pm', '')
		tokens = re.split('[^\w\:]+', s)
		day = None
		month = None
		uneaten_tokens = []
		bad_tokens = []
		for i, token in enumerate(tokens):
			if token in long_months:
				date['m'] = str(long_months.index(token)).zfill(2)
				month = token
			elif token in short_months:
				date['m'] = str(short_months.index(token)).zfill(2)
				month = token
			elif token in long_days:
				day = token
				date['d'] = str(long_days.index(token) + int(date['d']) - long_days.index(time.strftime('%A').lower())).zfill(2)
			elif token in short_days:
				day = token
				date['d'] = str(short_days.index(token) + int(date['d']) - short_days.index(time.strftime('%a').lower())).zfill(2)
			elif token == 'next':
				date['d'] = str(int(date['d']) + 7)
			elif token == 'last':
				date['d'] = str(int(date['d']) - 7)
			elif token == 'today':
				pass
			elif token == 'yesterday':
				date['d'] = str(int(date['d']) - 1).zfill(2)
			elif token == 'tomorrow':
				date['d'] = str(int(date['d']) + 1).zfill(2)
			elif (len(token) == 4) and token.isdigit():
				date['Y'] = token
			elif re.match('(\d{1,2}\:){1,2}\d{1,2}', token):
				token_parts = token.split(':')
				date['H'] = token_parts[0].zfill(2)
				date['M'] = token_parts[1].zfill(2)
				if len(token_parts) > 2:
					date['S'] = token_parts[2].zfill(2)
			elif token.isdigit() and (len(token) < 3):
				uneaten_tokens.append(token)
			else:
				bad_tokens.append(token)
		# look for day, month in case specified numerically; they're probably next to each other, and the only 2-digit tokens in uneaten_tokens
		if len(uneaten_tokens) == 1:
			token = uneaten_tokens[0]
			if (month is None) and (1 <= int(token) <= 12):
				date['m'] = token
			elif (day is None) and (1 <= int(token) <= 31):
				date['d'] = token
		elif (len(uneaten_tokens) == 2) and (month is None) and (day is None):
			if 12 < int(uneaten_tokens[0]) < 32:
				date['d'] = uneaten_tokens[0]
				date['m'] = uneaten_tokens[1]
			elif 12 < int(uneaten_tokens[1]) < 32:
				date['m'] = uneaten_tokens[0]
				date['d'] = uneaten_tokens[1]
			elif in_US:
				date['m'] = uneaten_tokens[0]
				date['d'] = uneaten_tokens[1]
			else:
				date['d'] = uneaten_tokens[0]
				date['m'] = uneaten_tokens[1]
		if pm and (int(date['H']) < 13):
			date['H'] = str(int(date['H']) + 12)
		if (int(date['d']) < 0):
			# day was last month... recursion!
			# XXX buggy
			date['m'], date['d'] = re.split('[\-\s]', anydatetime('%d days %d months ago' % (
				(abs(int(date['d'])) + int(time.strftime('%d'))),
				(int(time.strftime('%m')) - int(date['m'])),
			)))[1:3]
		elif (int(date['d']) > days_in_month[int(date['m'])]):
			# day is in next month... recursion!
			# XXX buggy
			date['m'], date['d'] = re.split('[\-\s]', anydatetime('now+ %d days %d months' % (
				(int(date['d']) - int(time.strftime('%d'))),
				(int(date['m']) - int(time.strftime('%m'))),
			)))[1:3]
		#if bad_tokens:
		#	print >> sys.stderr, 'unparsable tokens:', bad_tokens
		result = ISO_DATETIME_FORMAT
		for k, v in date.iteritems():
			result = result.replace('%' + k, v)
		ret = result
	return bad_tokens, time.strptime(ret, ISO_DATETIME_FORMAT)
