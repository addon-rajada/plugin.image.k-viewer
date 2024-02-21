# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

import requests
import sys
import os
from resources.lib import providers, routing, utils

from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

plugin = routing.Plugin()

@plugin.route('/')
def index():
	# search
	utils.createFolder(input_query, utils.localStr(32000), [])
	# comics
	utils.createFolder(index, utils.localStr(32008), [])
	utils.createFolder(popular, utils.localStr(32001), ['hq', 1])
	utils.createFolder(recommended_comics, utils.localStr(32003), [])
	utils.createFolder(search, utils.localStr(32005), ['dc',1])
	utils.createFolder(search, utils.localStr(32004), ['marvel',1])
	# mangas
	utils.createFolder(index, utils.localStr(32009), [])
	utils.createFolder(popular, utils.localStr(32002), ['manga', 1])
	utils.createFolder(recommended_mangas, utils.localStr(32003), [])
	utils.endDirectory()

@plugin.route('/recommended_comics')
def recommended_comics():
	utils.createFolder(search, "Jericho", ['jericho',1])
	utils.createFolder(search, "X-Men", ['x-men',1])
	utils.createFolder(search, "Superman", ['superman',1])
	utils.createFolder(search, "batman", ['batman',1])
	utils.createFolder(search, "Conan", ['conan',1])
	utils.createFolder(search, "The Boys", ['the boys',1])
	utils.createFolder(search, "The Walking Dead", ['the walking dead',1])
	utils.endDirectory()

@plugin.route('/recommended_mangas')
def recommended_mangas():
	utils.createFolder(search, "One Piece", ['one piece',1])
	utils.createFolder(search, "Naruto", ['naruto',1])
	utils.createFolder(search, "Dragon Ball", ['dragon ball',1])
	utils.createFolder(search, "Death Note", ['death note',1])
	utils.createFolder(search, "akira", ['akira',1])
	utils.endDirectory()

@plugin.route('/input_query')
def input_query():
	kb = xbmc.Keyboard('', utils.localStr(32000))
	kb.doModal()
	if kb.isConfirmed():
	    search(kb.getText(), 1)
	else:
	    #index()
		None


@plugin.route('/show_image/<url>')
def show_image(url):
	print('show image', url)
	utils.play(utils.base64_decode_url(url))

@plugin.route('/search/<query>/<page>')
def search(query, page):
	for result in providers.search(query, page):
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link']],
							image = result['image'],
							plot = result['plot'])
	if int(page) > 1:
		utils.createFolder(search, utils.localStr(32007), [query, int(page) - 1], 'previouspage.png', "", 'previouspage.png')
	utils.createFolder(search, utils.localStr(32006), [query, int(page) + 1], 'nextpage.png', "", 'nextpage.png')
	utils.endDirectory()

@plugin.route('/popular/<type>/<page>')
def popular(type, page):
	for result in providers.popular(type, page):
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link']],
							image = result['image'],
							plot = result['plot'])
	if int(page) > 1:
		utils.createFolder(popular, utils.localStr(32007), [type, int(page) - 1], 'previouspage.png', "", 'previouspage.png')
	utils.createFolder(popular, utils.localStr(32006), [type, int(page) + 1], 'nextpage.png', "", 'nextpage.png')
	utils.endDirectory()


@plugin.route('/chapters/<provider>/<url>')
def list_chapters(provider, url):
	for r in providers.do_list_chapters(provider, url):
		utils.createFolder(list_pages,
							r['title'],
							[r['provider'], r['link']],
							plot = r['plot'])
	utils.endDirectory()

@plugin.route('/pages/<provider>/<url>')
def list_pages(provider, url):
	for r in providers.do_list_pages(provider, url):
		img_url = plugin.url_for(show_image, r['link_b64'])
		print('pageurl', url)
		#utils.createItem(img_url, r['title'], r['link'])
		utils.createItem(r['link'], r['title'], r['link'])
		
		#li = ListItem(r['title'])
		#li.setProperty('IsPlayable', 'true')
		#li.setInfo('pictures', {'title': label})
		#li.setArt({
      	#	"thumb":r['link'],
        #	#"fanart": GLOBAL_FANART
        #})
		#addDirectoryItem(plugin.handle, r['link'], li)
	utils.endDirectory()

if __name__ == '__main__':
	utils.plugin = plugin
	utils.set_content('images')
	utils.log('init')
	plugin.run()