# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

from resources.lib import providers, routing, utils, windows

FIRST_PAGE = 1

plugin = routing.Plugin()

@plugin.route('/')
def index():
	# search
	utils.createFolder(input_query, utils.localStr(32000), [], image=utils.search_img, thumb=utils.search_img)
	# comics
	utils.createFolder(index, utils.localStr(32008), [], image=utils.comics_img, thumb=utils.comics_img) # separator
	utils.createFolder(popular, utils.localStr(32001), ['hq', FIRST_PAGE], image=utils.popular_img, thumb=utils.popular_img)
	utils.createFolder(recommended_comics, utils.localStr(32003), [], image=utils.recommended_img, thumb=utils.recommended_img)
	utils.createFolder(specific_keyword, utils.localStr(32004), ['hq','marvel',FIRST_PAGE], image=utils.marvel_img, thumb=utils.marvel_img)
	utils.createFolder(specific_keyword, utils.localStr(32005), ['hq','dc',FIRST_PAGE], image=utils.dc_img, thumb=utils.dc_img)
	utils.createFolder(specific_keyword, utils.localStr(32010), ['hq','darkhorse',FIRST_PAGE], image=utils.darkhorse_img, thumb=utils.darkhorse_img)
	# mangas
	utils.createFolder(index, utils.localStr(32009), [], image=utils.mangas_img, thumb=utils.mangas_img) # separator
	utils.createFolder(popular, utils.localStr(32002), ['manga', FIRST_PAGE], image=utils.popular_img, thumb=utils.popular_img)
	utils.createFolder(recommended_mangas, utils.localStr(32003), [], image=utils.recommended_img, thumb=utils.recommended_img)
	utils.endDirectory()

@plugin.route('/recommended_comics')
def recommended_comics():
	for i in sorted(utils.localStr(32011).split('|')):
		utils.createFolder(search, i, [i, FIRST_PAGE])
	utils.endDirectory()


@plugin.route('/recommended_mangas')
def recommended_mangas():
	for i in sorted(utils.localStr(32012).split('|')):
		utils.createFolder(search, i, [i, FIRST_PAGE])
	utils.endDirectory()

@plugin.route('/input_query')
def input_query():
	text = utils.keyboard(utils.read_query(), utils.localStr(32000))
	if text != None:
		utils.save_query(text)
		search(text, FIRST_PAGE)
	else: index()


@plugin.route('/search/<query>/<page>')
def search(query, page):
	results = providers.search(query, page)
	for result in results:
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link'], FIRST_PAGE],
							image = result['image'],
							plot = result['plot'])
	if int(page) > 1 and utils.get_setting('previous_page_item', bool):
		utils.createFolder(search, utils.localStr(32007), [query, int(page) - 1], utils.previous_page_img, "", utils.previous_page_img)
	if len(results) > 0:
		utils.createFolder(search, utils.localStr(32006), [query, int(page) + 1], utils.next_page_img, "", utils.next_page_img)
	utils.endDirectory(cache=True)

@plugin.route('/popular/<type>/<page>')
def popular(type, page):
	results = providers.popular(type, page)
	for result in results:
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link'], FIRST_PAGE],
							image = result['image'],
							plot = result['plot'])
	if int(page) > 1 and utils.get_setting('previous_page_item', bool):
		utils.createFolder(popular, utils.localStr(32007), [type, int(page) - 1], utils.previous_page_img, "", utils.previous_page_img)
	if len(results) > 0:
		utils.createFolder(popular, utils.localStr(32006), [type, int(page) + 1], utils.next_page_img, "", utils.next_page_img)
	utils.endDirectory(cache=True)

@plugin.route('/specific_keyword/<type>/<keyword>/<page>')
def specific_keyword(type, keyword, page):
	results = providers.by_keyword(type, keyword, page)
	for result in results:
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link'], FIRST_PAGE],
							image = result['image'],
							plot = result['plot'])
	if int(page) > 1 and utils.get_setting('previous_page_item', bool):
		utils.createFolder(specific_keyword, utils.localStr(32007), [type, keyword, int(page) - 1], utils.previous_page_img, "", utils.previous_page_img)
	if len(results) > 0:
		utils.createFolder(specific_keyword, utils.localStr(32006), [type, keyword, int(page) + 1], utils.next_page_img, "", utils.next_page_img)
	utils.endDirectory(cache=True)

@plugin.route('/chapters/<provider_name>/<url>/<page>')
def list_chapters(provider_name, url, page):
	results = providers.do_list_chapters(provider_name, url, page)
	for r in results:
		utils.createFolder(list_pages,
							r['title'],
							[r['provider'], r['link'], utils.base64_encode(r['title'])],
							plot = r['plot'],
							image = r['image'],
							thumb = r['image'])
	if int(page) > 1 and utils.get_setting('previous_page_item', bool):
		utils.createFolder(list_chapters, utils.localStr(32007), [provider_name, url, int(page) - 1], utils.previous_page_img, "", utils.previous_page_img)
	
	pagination = providers.has_pagination(providers.provider_by_name(provider_name)['chapters']['request'])
	if len(results) > 0 and pagination:
		utils.createFolder(list_chapters, utils.localStr(32006), [provider_name, url, int(page) + 1], utils.next_page_img, "", utils.next_page_img)

	utils.endDirectory(cache=True)

@plugin.route('/pages/<provider_name>/<url>/<chapter_title>')
@plugin.route('/pages/<provider_name>/<url>')
def list_pages(provider_name, url, chapter_title = ''):
	use_custom_gui = utils.get_setting('custom_gui', bool)
	results = providers.do_list_pages(provider_name, url)
	if not use_custom_gui:
		for r in results:
			link = utils.base64_decode_url(r['link'])
			utils.createItem(link, r['title'], link)
		utils.endDirectory()
	else:
		window = windows.PagesWindow(title = utils.base64_decode(chapter_title),
									 pages = results,
									 headers = providers.get_headers(provider_name, 'pages') )
		window.doModal()
		del window

if __name__ == '__main__':
	utils.plugin = plugin
	utils.set_content('images')
	utils.log('init')
	plugin.run()
