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
	utils.createFolder(popular, utils.localStr(32001), ['hq'])
	utils.createFolder(recommended_comics, utils.localStr(32003), [])
	utils.createFolder(search, utils.localStr(32005), ['dc'])
	utils.createFolder(search, utils.localStr(32004), ['marvel'])
	# mangas
	utils.createFolder(index, utils.localStr(32009), [])
	utils.createFolder(popular, utils.localStr(32002), ['manga'])
	utils.createFolder(recommended_mangas, utils.localStr(32003), [])
	utils.endDirectory()

@plugin.route('/recommended_comics')
def recommended_comics():
	utils.createFolder(search, "Jericho", ['jericho'])
	utils.createFolder(search, "X-Men", ['x-men'])
	utils.createFolder(search, "Superman", ['superman'])
	utils.createFolder(search, "batman", ['batman'])
	utils.createFolder(search, "Conan", ['conan'])
	utils.createFolder(search, "The Boys", ['the boys'])
	utils.createFolder(search, "The Walking Dead", ['the walking dead'])
	utils.endDirectory()

@plugin.route('/recommended_mangas')
def recommended_mangas():
	utils.createFolder(search, "One Piece", ['one piece'])
	utils.createFolder(search, "Naruto", ['naruto'])
	utils.createFolder(search, "Dragon Ball", ['dragon ball'])
	utils.createFolder(search, "Death Note", ['death note'])
	utils.createFolder(search, "akira", ['akira'])
	utils.endDirectory()

@plugin.route('/input_query')
def input_query():
	kb = xbmc.Keyboard('', utils.localStr(32000))
	kb.doModal()
	if kb.isConfirmed():
	    search(kb.getText())
	else:
	    #index()
		None

@plugin.route('/search/<query>')
def search(query):
	for result in providers.search(query):
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link']],
							image = result['image'],
							plot = result['plot'])
	utils.endDirectory()

@plugin.route('/popular/<type>')
def popular(type):
	for result in providers.do_list_popular(type):
		utils.createFolder(list_chapters,
							result['title'],
							[result['provider'], result['link']],
							image = result['image'],
							plot = result['plot'])
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
		#utils.createItem(r['link'], r['title'], image = r['link'])
		li = ListItem(r['title'])
		#li.setInfo('pictures', {'title': r['title']})
		li.setArt({
      		"thumb":r['link'],
        	#"fanart": GLOBAL_FANART
        })
		addDirectoryItem(plugin.handle, r['link'], li)
	utils.endDirectory()

if __name__ == '__main__':
	utils.plugin = plugin
	utils.set_content('images')
	utils.log('init')
	plugin.run()