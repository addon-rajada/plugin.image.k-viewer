import os
import json
import requests
from resources.lib.parser.ehp import *
from resources.lib import utils
import xml.etree.ElementTree as ET

from concurrent.futures import ThreadPoolExecutor, as_completed

import sys
if sys.version_info[0] == 2:
	from urllib import quote
else:
	from urllib.parse import quote

def load_file(path):
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

all_providers = load_file(os.path.join(os.path.dirname(__file__), '..', 'providers.json'))

def do_request(type, url):
	try:
		if type == 'get':
			resp = requests.get(url, timeout=10)
		elif type == 'post':
			resp = requests.post(url, timeout=10)
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


def do_search(provider, query): # page = ''
	c = do_request(provider['search']['request']['type'], provider['search']['request']['url'].replace('{query}', quote(query)))
	if c == None: return []
	dom = Html().feed(c.text)
	a = eval('dom.' + provider['search']['rows'])
	result = []
	for item in a: # must be item
		title = eval(provider['search']['title'])
		title = '[COLOR %s][%s][%s][/COLOR] %s' % (provider['color'], provider['name'], provider['lang'], title)
		result.append({
			'priority': provider['priority'],
			'provider': provider['name'],
			'title': title,
			'image': eval(provider['search']['image']),
			'link': utils.base64_encode_url(eval(provider['search']['link'])),
			'plot': try_eval(item, provider['search'], 'plot')
		})
		#print(str(item), result)
	return result

def do_list_popular(type):
	result = []
	for p in all_providers:
		if p['type'] == type and 'popular' in p:
			c = do_request(p['popular']['request']['type'],p['popular']['request']['url'])
			if c == None: continue
			dom = Html().feed(c.text)
			a = eval('dom.' + p['popular']['rows'])
			for item in a: # must be item
				title = try_eval(item, p['popular'], 'title')
				title = '[COLOR %s][%s][%s][/COLOR] %s' % (p['color'], p['name'], p['lang'], title)
				result.append({
					'priority': p['priority'],
					'provider': p['name'],
					'title': title,
					'image': try_eval(item, p['popular'], 'image'),
					'link': utils.base64_encode_url(eval(p['popular']['link'])),
					'plot': try_eval(item, p['popular'], 'plot')
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
				title = try_eval(item, p['chapters'], 'mutate_title', title, "'{value}'.replace('{title}', default_return)")

				result.append({
					'priority': p['priority'],
					'provider': p['name'],
					'title': title,
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
					if p['pages']['type'] == 'tag_attrib_from_rows':
						attrs = ET.fromstring(str(item)).attrib
						#print(item, attrs)

						# process title
						title = attrs[p['pages']['title']]
						if 'mutate_title' in p['pages']:
							title = eval(p['pages']['mutate_title'].replace('{title}', title))

						link = attrs[p['pages']['link']]

						partial_result.append({
							'title': title,
							'link': link.strip()
						})
				except ET.ParseError:
					print('parser error', str(item))
					continue
			if 'reverse' in p['pages'] and p['pages']['reverse'] == 'true':
				partial_result.reverse()
			result.extend(partial_result)
	return result



def search(query):
	results = []
	
	#for p in all_providers:
	#	s = do_search(p, query)
	#	results.extend(s)

	num_providers = len(all_providers)
	workers = num_providers if (num_providers > 0 and num_providers <= 16) else 16
	with ThreadPoolExecutor(max_workers = workers) as executor:
		futures = [executor.submit(do_search, provider = x, query = query) for x in all_providers]
		for f in as_completed(futures):
			pool_result = f.result()
			results.extend(pool_result)

	return sorted(results, key = lambda x: x['priority'])