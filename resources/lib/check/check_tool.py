# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

import os, sys, json, requests, base64, re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from ehp_mod import *

if sys.version_info[0] == 2: from urllib import quote, unquote
else: from urllib.parse import quote, unquote

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class utils:

	icon_img = 'icon.png'

	@staticmethod
	def base64_encode_url(value):
		encoded = str(base64.b64encode(bytes(value, "utf-8")), 'utf-8')
		return encoded.replace('=', '').replace('+', '-').replace('/', '_')

	@staticmethod
	def base64_decode_url(data):
	    value = data.replace('-', '+').replace('_', '/')
	    value += '=' * (len(value) % 4)
	    return str(base64.b64decode(value), 'utf-8') # urlsafe_

	@staticmethod
	def get_setting(key, converter=str):
		if key == 'timeout': return 4
		elif key == 'custom_gui': return True
		elif key == 'provider_prefix': return True
		elif key == 'lang_prefix': return True
		return None

	@staticmethod
	def do_request(type, url, timeout = 4, headers = {}, depth = 0):
		print(type, 'request to', url)
		try:
			if type == 'get':
				resp = requests.get(url, timeout=timeout, headers=headers)
			elif type == 'post':
				resp = requests.post(url, timeout=timeout, headers=headers)
			return resp
		except requests.exceptions.Timeout:
			print('timeout error. depth:', depth)
			if depth == 1: return None # 1 retries
			else:
				depth += 1
				return utils.do_request(type, url, 2*timeout, headers, depth)
		except requests.exceptions.ConnectionError:
			print('connection error. depth:', depth)
			if depth == 3: return None # 3 retries
			else:
				depth += 1
				return utils.do_request(type, url, timeout, headers, depth)

def _load_file(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as file:
            providers = json.load(file)
        #for provider in providers: print(provider)
        return providers
    except Exception as e:
        import traceback
        print("Failed importing providers from %s: %s" % (path, repr(e)))

all_providers = _load_file(os.path.join(os.path.dirname(__file__), '..', '..', 'providers.json'))

def provider_by_name(name):
	for p in all_providers:
		if p['name'] == name:
			return p
	return None

def has_pagination(request_obj):
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

def try_eval(item, object, key, default_return = 'nothing to eval', pre_function = None):
	if (key in object and object[key] != ""):
		if pre_function != None:
			primary_eval = eval(pre_function.replace('{value}', object[key]))
			return eval(primary_eval)
		return eval(object[key])
	else:
		return default_return

def json_process(resp, provider, req_obj):
	result = []
	try: rows = eval("%s%s" % ('resp.json()', provider[req_obj]['rows']))
	except: rows = []

	for item in rows:
		# process image
		try: image = eval("%s%s" % ('item', provider[req_obj]['image']))
		except: image = utils.icon_img
		try: image_auxiliar = eval("%s%s" % ('item', provider[req_obj]['image_auxiliar']))
		except: image_auxiliar = ''
		for key, value in provider[req_obj].items():
			if key.startswith('mutate_image'):
				try: image = eval(value.replace('{image}',repr(image)).replace('{image_auxiliar}',repr(image_auxiliar)))
				except: pass
		# process title
		try: title = eval("%s%s" % ('item', provider[req_obj]['title']))
		except: title = ''
		if 'exclude_title_with_words' in provider[req_obj]:
			if any(w in title for w in provider[req_obj]['exclude_title_with_words'].split('|')):
				continue
		if 'mutate_title' in provider[req_obj]:
			title = eval(provider[req_obj]['mutate_title'].replace('{title}', repr(title)))
		provider_prefix = ('[%s]' % provider['name']) if utils.get_setting('provider_prefix', bool) else ''
		lang_prefix = ('[%s]' % provider['lang']) if utils.get_setting('lang_prefix', bool) else ''
		title = '[COLOR %s]%s%s[/COLOR] %s'%(provider['color'],provider_prefix,lang_prefix,title)
		# process link
		try: link = eval("%s%s" % ('item', provider[req_obj]['link']))
		except: link = ''
		if 'mutate_link' in provider[req_obj]:
			link = eval(provider[req_obj]['mutate_link'].replace('{link}',repr(link)))
		# new result
		result.append({
			'priority': provider['priority'],
			'provider': provider['name'],
			'title': unquote(title),
			'image': image,
			'link': utils.base64_encode_url(link),
			'plot': ''
		})
	return result

def process_request(provider, page, req_obj, query = ''):
	result = []

	# process url
	url = provider[req_obj]['request']['url']
	url = url.replace('{query}', quote(query))

	# process page
	if int(page) > 1 and not has_pagination(provider[req_obj]['request']):
		return result
	if 'page_multiplier' in provider[req_obj]['request']:
		page = eval(provider[req_obj]['request']['page_multiplier'])
	url = url.replace('{page}', str(page))

	# request
	resp = utils.do_request(provider[req_obj]['request']['type'], url)
	if resp == None: return result

	# json parser
	if parser_type(provider[req_obj]) == 'json':
		result = json_process(resp, provider, req_obj)

	# html parser
	elif parser_type(provider[req_obj]) == 'html':
		dom = Html().feed(resp.text)
		try: rows = eval(provider[req_obj]['rows'])
		except: rows = []

		for item in rows:
			# process image
			try: image = eval(provider[req_obj]['image'])
			except: image = utils.icon_img

			# process title
			try: title = eval(provider[req_obj]['title'])
			except: title = ''
			if 'mutate_title' in provider[req_obj]:
				title = eval(provider[req_obj]['mutate_title'].replace('{title}', title))
			provider_prefix = ('[%s]' % provider['name']) if utils.get_setting('provider_prefix', bool) else ''
			lang_prefix = ('[%s]' % provider['lang']) if utils.get_setting('lang_prefix', bool) else ''
			title = '[COLOR %s]%s%s[/COLOR] %s'%(provider['color'],provider_prefix,lang_prefix,title)

			# process link
			try: link = eval(provider[req_obj]['link'])
			except: link = ''
			
			# new result
			result.append({
				'priority': provider['priority'],
				'provider': provider['name'],
				'title': unquote(title),
				'image': image,
				'link': utils.base64_encode_url(link),
				'plot': '' #try_eval(item, provider['search'], 'plot')
			})

	return result


def do_list_chapters(provider, url, page):
	result = []
	url = utils.base64_decode_url(url)
	#print('url --- ',url)
	p = provider_by_name(provider)
	# process page
	if 'page_multiplier' in p['chapters']['request']:
		page = eval(p['chapters']['request']['page_multiplier'])
	url = url.replace('{page}', str(page))
	# request
	resp = utils.do_request(p['chapters']['request']['type'], url)
	if resp == None: return result

	# json parser
	if parser_type(p['chapters']) == 'json':
		result = json_process(resp, p, 'chapters')

	# html parser
	elif parser_type(p['chapters']) == 'html':
		# process rows
		dom = Html().feed(resp.text)
		try: rows = eval(p['chapters']['rows'])
		except: rows = []
		for item in rows:
			# process title
			title = try_eval(item, p['chapters'], 'title')
			if 'mutate_title' in p['chapters']:
				title = eval(p['chapters']['mutate_title'].replace('{title}', title))
			title = try_eval(item, p['chapters'], 'mutate_title', title, "\"{value}\".replace('{title}', default_return)")
			# process image
			try: image = eval(p['chapters']['image'])
			except: image = utils.icon_img
			# process link
			link = eval(p['chapters']['link'])
			if not link.startswith('http'): continue
			# new result
			result.append({
				'priority': p['priority'],
				'provider': p['name'],
				'title': unquote(title),
				'image': image,
				'link': utils.base64_encode_url(link),
				'plot': '' #try_eval(item, p['chapters'], 'plot')
			})

	# reverse
	if 'reverse' in p['chapters'] and p['chapters']['reverse'] == 'true':
		result.reverse()

	return result

def fix_blogspot_url(index, url):
	# ref: https://gist.github.com/Sauerstoffdioxid/2a0206da9f44dde1fdfce290f38d2703
	# s0-Ic42
	# s0-g
	if ('bp.blogspot.com' not in url) and ('googleusercontent.com' not in url):
		return index, url
	s = url.split('=')
	if len(s) > 1:
		new_url = s[0]
		xml = utils.do_request('get', new_url + '=g')
		match = re.findall(r'(http.*googleusercontent.com.*)"\stiler_version_number', xml.text)
		try: new_url = match[0].split('/')
		except: return index, url
		new_url.insert(7, 's1000')
		return index, '/'.join(new_url)
	return index, url

def get_headers(provider_name, obj):
	p = provider_by_name(provider_name)
	custom_headers = {}
	if 'headers' in p[obj]['request']:
		custom_headers = p[obj]['request']['headers']
	return custom_headers

def do_list_pages(provider_name, url):
	result = []
	url = utils.base64_decode_url(url)
	p = provider_by_name(provider_name)
	# request
	custom_headers = get_headers(provider_name, 'pages')
	resp = utils.do_request(p['pages']['request']['type'], url, headers = custom_headers)
	if resp == None: return result

	# json parser
	if parser_type(p['pages']) == 'json':
		result = json_process(resp, p, 'pages')

	# html parser
	elif parser_type(p['pages']) == 'html':
		# process rows
		dom = Html().feed(resp.text)
		try: rows = eval(p['pages']['rows'])
		except: rows = []
		for item in rows:
			try:
				#if p['pages']['type'] == 'tag_attrib_from_rows':
					#attrs = ET.fromstring(str(item)).attrib
					#print(item, attrs)
				# process title
				try: title = eval(p['pages']['title'])
				except: title = ''
				if 'mutate_title' in p['pages']:
					try: title = eval(p['pages']['mutate_title'].replace('{title}', title))
					except: pass
				# process link
				try: link = eval(p['pages']['link'])
				except: link = ''
				if 'mutate_link' in p['pages']:
					try: link = eval(p['pages']['mutate_link'].replace('{link}', link))
					except: pass
				try: link = link.replace('http://','https://') # force https
				except: pass
				# new result
				result.append({
					'title': unquote(title),
					'link': utils.base64_encode_url(link.strip())
				})
			except ET.ParseError:
				print('parser error', str(item))
				continue

	# blogspot url fix
	use_custom_gui = utils.get_setting('custom_gui', bool)
	if not use_custom_gui:
		num_pages = len(result)
		workers = num_pages if (num_pages > 0 and num_pages <= 16) else 16
		with ThreadPoolExecutor(max_workers = workers) as executor:
			futures = [executor.submit(fix_blogspot_url, index = result.index(x), url = utils.base64_decode_url(x['link'])) for x in result]
			for f in as_completed(futures):
				index, new_url = f.result()
				#print('blogspot fix - before (%s) after (%s)' % (utils.base64_decode_url(result[index]['link']), new_url))
				result[index]['link'] = utils.base64_encode_url(new_url)
	# reverse
	if 'reverse' in p['pages'] and p['pages']['reverse'] == 'true':
		result.reverse()
	return result


def get_arg(arg, default):
	opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
	args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
	all = zip(opts, args)
	for i in all:
		if i[0] == arg:
			return i[1]
	if default == 'exit_if_missing':
		print('Missing', arg, 'flag')
		exit()
	return default

if __name__ == '__main__':

	# args
	print(sys.argv)
	provider_name = get_arg('-n', 'exit_if_missing')
	keyword = get_arg('-k', 'exit_if_missing')
	query = quote(get_arg('-q', ''))
	result_page = get_arg('-pr', 1)
	chapter_page = get_arg('-pc', 1)

	# results
	provider = provider_by_name(provider_name)
	results = process_request(provider, result_page, keyword, query)
	print('#'*50)
	for r in results:
		print(f"{bcolors.WARNING}{r['title']}{bcolors.ENDC}")
		print(r['image'])
		print(utils.base64_decode_url(r['link']))
		print('-'*50)

	# chapters
	check_chap = input('Want to check chapters from first result? [Y][n] ')
	chapters = []
	if check_chap == 'Y':
		chapters = do_list_chapters(provider_name, results[0]['link'], chapter_page)
		print('#'*50)
		print('Total chapters', len(chapters))
		print('Showing first 5 chapters')
		for chap in chapters[:5]:
			print(chap['title'])
			print(chap['image'])
			print(utils.base64_decode_url(chap['link']))
			print('-'*50)

	# pages
	if len(chapters) < 1:
		print('empty chapters array. exiting')
		exit()
	check_pages = input('Want to check pages from first chapter? [Y][n] ')
	if check_pages == 'Y':
		pages = do_list_pages(provider_name, chapters[0]['link'])
		print('#'*50)
		print('Total pages', len(pages))
		print('Showing first 5 pages')
		for p in pages[:5]:
			print(p['title'])
			print(utils.base64_decode_url(p['link']))
			print('-'*50)
