import os
import json
import requests
from resources.lib.parser.ehp import *
from resources.lib import utils
import xml.etree.ElementTree as ET

from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
if sys.version_info[0] == 2:
	from urllib import quote, unquote
else:
	from urllib.parse import quote, unquote

def _load_file(path):
    if not os.path.exists(path):
        print('erro')
        return

    try:
        with open(path, encoding="utf-8") as file:
            providers = json.load(file)
        for provider in providers:
            print(provider)
        return providers
    except Exception as e:
        import traceback
        print("Failed importing providers from %s: %s" % (path, repr(e)))

all_providers = _load_file(os.path.join(os.path.dirname(__file__), '..', 'providers.json'))

def _has_pagination(request_obj):
	if 'pagination' not in request_obj:
		return False
	elif 'pagination' in request_obj:
		if request_obj['pagination'] == 'false':
			return False
		elif request_obj['pagination'] == 'true':
			return True

def parser_type(parser_obj):
	if 'type' in parser_obj:
		return parser_obj['type']
	else:
		return 'html'

def do_request(type, url, timeout = 15):
	try:
		if type == 'get':
			resp = requests.get(url, timeout=timeout)
		elif type == 'post':
			resp = requests.post(url, timeout=timeout)
		return resp

	except requests.exceptions.Timeout:
		print('timeout error')
		return None


def try_eval(item, object, key, default_return = 'nothing to eval', pre_function = None):
	if (key in object and object[key] != ""):
		if pre_function != None:
			primary_eval = eval(pre_function.replace('{value}', object[key]))
			return eval(primary_eval)
		return eval(object[key])
	else:
		return default_return

def process_request(provider, page, query = None):
	pass

def do_search(provider, query, page):
	result = []
	url = provider['search']['request']['url']
	url = url.replace('{query}', quote(query))
	
	if int(page) > 1 and not _has_pagination(provider['search']['request']):
		return []
	if 'page_multiplier' in provider['search']['request']:
		page = eval(provider['search']['request']['page_multiplier'])
	url = url.replace('{page}', str(page))

	c = do_request(provider['search']['request']['type'], url)
	if c == None: return []

	if parser_type(provider['search']) == 'json':
		rows = eval("%s%s" % ('c.json()', provider['search']['rows']))
		for item in rows:
			try: title = eval("%s%s" % ('item', provider['search']['title']))
			except: title = 'No title'

			try: image = eval("%s%s" % ('item', provider['search']['image']))
			except: image = ''

			if 'exclude_title_with_words' in provider['search']:
				if any(w in title for w in provider['search']['exclude_title_with_words'].split('|')):
					continue

			title = '[COLOR %s][%s][%s][/COLOR] %s' % (provider['color'],
														provider['name'],
														provider['lang'],
														title)

			link = eval("%s%s" % ('item', provider['search']['link']))

			if 'mutate_link' in provider['search']:
				link = eval(provider['search']['mutate_link'].replace('{link}',repr(link)))

			result.append({
				'priority': provider['priority'],
				'provider': provider['name'],
				'title': unquote(title),
				'image': image,
				'link': utils.base64_encode_url(link),
				'plot': ''
			})

	elif parser_type(provider['search']) == 'html':
		dom = Html().feed(c.text)
		a = eval('dom.' + provider['search']['rows'])
	
		for item in a: # must be item
			title = eval(provider['search']['title'])
			title = '[COLOR %s][%s][%s][/COLOR] %s' % (provider['color'], provider['name'], provider['lang'], title)
			result.append({
				'priority': provider['priority'],
				'provider': provider['name'],
				'title': unquote(title),
				'image': eval(provider['search']['image']),
				'link': utils.base64_encode_url(eval(provider['search']['link'])),
				'plot': try_eval(item, provider['search'], 'plot')
			})
			#print(str(item), result)

	return result



def do_list_popular(provider, page):
	result = []
	url = provider['popular']['request']['url'].replace('{page}', str(page))
	if int(page) > 1 and not _has_pagination(provider['popular']['request']):
		return []
	c = do_request(provider['popular']['request']['type'], url)
	if c == None: return []

	if parser_type(provider['popular']) == 'json':
		rows = eval("%s%s" % ('c.json()', provider['popular']['rows']))
		for item in rows:
			title = eval("%s%s" % ('item', provider['popular']['title']))

			if 'exclude_title_with_words' in provider['popular']:
				if any(w in title for w in provider['popular']['exclude_title_with_words'].split('|')):
					continue
					

			title = '[COLOR %s][%s][%s][/COLOR] %s' % (provider['color'],
														provider['name'],
														provider['lang'],
														title)

			try: image = eval("%s%s" % ('item', provider['search']['image']))
			except: image = ''

			link = eval("%s%s" % ('item', provider['popular']['link']))

			if 'mutate_link' in provider['popular']:
				link = eval(provider['popular']['mutate_link'].replace('{link}',repr(link)))

			result.append({
				'priority': provider['priority'],
				'provider': provider['name'],
				'title': unquote(title),
				'image': image,
				'link': utils.base64_encode_url(link),
				'plot': ''
			})


	elif parser_type(provider['popular']) == 'html':
		dom = Html().feed(c.text)
		a = eval('dom.' + provider['popular']['rows'])
		for item in a: # must be item
			title = try_eval(item, provider['popular'], 'title')
			title = '[COLOR %s][%s][%s][/COLOR] %s' % (provider['color'],
														provider['name'],
														provider['lang'],
														title)
			result.append({
				'priority': provider['priority'],
				'provider': provider['name'],
				'title': unquote(title),
				'image': try_eval(item, provider['popular'], 'image'),
				'link': utils.base64_encode_url(eval(provider['popular']['link'])),
				'plot': try_eval(item, provider['popular'], 'plot')
			})
			#print(str(item), result)

	return result

def do_list_chapters(provider, url):
	result = []
	url = utils.base64_decode_url(url)
	print('url --- ',url)
	for p in all_providers:
		if p['name'] == provider:
			cc = do_request(p['chapters']['request']['type'], url)
			if cc == None: continue
			dom = Html().feed(cc.text)
			b = eval('dom.' + p['chapters']['rows'])
			for item in b:

				title = try_eval(item, p['chapters'], 'title')
				#if 'mutate_title' in p['chapters']:
				#	title = eval(p['chapters']['mutate_title'].replace('{title}', title))
				title = try_eval(item, p['chapters'], 'mutate_title', title, "\"{value}\".replace('{title}', default_return)")

				result.append({
					'priority': p['priority'],
					'provider': p['name'],
					'title': unquote(title),
					'link': utils.base64_encode_url(try_eval(item, p['chapters'], 'link')),
					'plot': try_eval(item, p['chapters'], 'plot')
				})
			if 'reverse' in p['chapters'] and p['chapters']['reverse'] == 'true':
				result.reverse()
	return result


def do_list_pages(provider, url):
	result = []
	url = utils.base64_decode_url(url)
	print('url --- ',url)
	for p in all_providers:
		if p['name'] == provider:
			partial_result = []
			cc = do_request(p['chapters']['request']['type'], url)
			if cc == None: continue
			dom = Html().feed(cc.text)
			b = eval('dom.' + p['pages']['rows'])
			for item in b:
				try:
					#if p['pages']['type'] == 'tag_attrib_from_rows':
						#attrs = ET.fromstring(str(item)).attrib
						#print(item, attrs)

					# process title
					#title = attrs[p['pages']['title']]
					title = try_eval(item, p['pages'], 'title')
					if 'mutate_title' in p['pages']:
						title = eval(p['pages']['mutate_title'].replace('{title}', title))

					#link = attrs[p['pages']['link']]
					link = try_eval(item, p['pages'], 'link')
					link = try_eval(item, p['pages'], 'mutate_link', link, "\"{value}\".replace('{link}', default_return)")

					partial_result.append({
						'title': unquote(title),
						'link_b64': utils.base64_encode_url(link.strip()),
						'link': link.strip()
					})
				except ET.ParseError:
					print('parser error', str(item))
					continue
			if 'reverse' in p['pages'] and p['pages']['reverse'] == 'true':
				partial_result.reverse()
			result.extend(partial_result)
	return result


def popular(type, page):
	results = []

	providers = [p for p in all_providers if p['type'] == type and 'popular' in p]
	num_providers = len(providers)
	workers = num_providers if (num_providers > 0 and num_providers <= 16) else 16

	with ThreadPoolExecutor(max_workers = workers) as executor:
		futures = [executor.submit(do_list_popular, provider = x, page = page) for x in providers]
		for f in as_completed(futures):
			pool_result = f.result()
			results.extend(pool_result)

	return sorted(results, key = lambda x: x['priority'])

def search(query, page):
	results = []
	
	#for p in all_providers:
	#	s = do_search(p, query)
	#	results.extend(s)

	num_providers = len(all_providers)
	workers = num_providers if (num_providers > 0 and num_providers <= 16) else 16
	with ThreadPoolExecutor(max_workers = workers) as executor:
		futures = [executor.submit(do_search, provider = x, query = query, page = page) for x in all_providers]
		for f in as_completed(futures):
			pool_result = f.result()
			results.extend(pool_result)

	return sorted(results, key = lambda x: x['priority'])
