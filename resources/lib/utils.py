# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

from resources.lib import routing
import base64
import os
import requests

from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

try:
    from xbmcvfs import translatePath
except ImportError:
    from xbmc import translatePath

import sys
if sys.version_info[0] == 2:
	from urllib import quote
else:
	from urllib.parse import quote

plugin = None

addon = xbmcaddon.Addon()
home = addon.getAddonInfo('path')
icon = addon.getAddonInfo('icon')
name = addon.getAddonInfo('name')
version = addon.getAddonInfo('version')
profile = addon.getAddonInfo('profile')

icon_img = 'icon.png'
fanart_img = 'fanart.png'
previous_page_img = 'previouspage.png'
next_page_img = 'nextpage.png'

last_query_file = 'last_query.txt'
addon_data = 'special://home/userdata/addon_data/plugin.image.k-viewer'
last_query_location = translatePath(os.path.join(addon_data, last_query_file))

if not os.path.exists(translatePath(addon_data)):
	os.makedirs(translatePath(addon_data)) # create addon data folder if not exists

def do_request(url):
	try:
		response = requests.get(url)
		if response.status_code == 200:
			return response
		return None
	except Exception as e:
		return None

def localStr(id):
	return addon.getLocalizedString(id)

def get_setting(key, converter=str):
	value = addon.getSetting(id=key)
	if converter is str: return str(value)
	elif converter is bool: return value == 'true'
	elif converter is int: return int(value)
	elif converter is float: return float(value)
	else: return None

def set_setting(key, val):
	return addon.setSetting(id=key, value=val)

def read_file(filename, mode = 'r'):
	with open(filename, mode) as f:
		return f.read()

def write_file(filename, content, mode = 'w'):
	with open(filename, mode) as f:
		f.write(content)

def datapath(filename):
	return translatePath(os.path.join(addon_data, filename))

def read_query():
	if not os.path.exists(last_query_location):
		return ''
	else:
		return read_file(last_query_location)

def save_query(query):
	write_file(last_query_location, query)

def base64_encode_url(value):
    encoded = str(base64.b64encode(bytes(value, "utf-8")), 'utf-8')
    return encoded.replace('=', '').replace('+', '-').replace('/', '_')

def base64_encode(value):
	encoded = str(base64.b64encode(bytes(value, "utf-8")), 'utf-8')
	return encoded

def base64_decode_url(data):
    value = data.replace('-', '+').replace('_', '/')
    value += '=' * (len(value) % 4)
    return str(base64.b64decode(value), 'utf-8') # urlsafe_

def base64_decode(data):
	decoded = str(base64.b64decode(data), 'utf-8')
	return decoded

def keyboard(placeholder, title):
	kb = xbmc.Keyboard(placeholder, title)
	kb.doModal()
	if kb.isConfirmed(): return kb.getText()
	else: return None

def bold(text):
	# return bold text
	return '[B]' + text + '[/B]'

def colorful(text, color = 'white'):
	# return colored text
	# i.e. crimson, palegreen, red, darkgray, lightskyblue, turquoise, sienna ...
	return '[COLOR ' + color + ']' + text + '[/COLOR]'

def img(file):
	# return link or local path for image
	if 'http' not in file.lower():
		return home + '/resources/media/' + file
	else:
		return file

def log(itemOrMessage, opt_label = ''):
	# log message
	xbmc.log('[COLOR blue]' + opt_label + repr(itemOrMessage) + '[/COLOR]', level=xbmc.LOGDEBUG)

def refresh():
	xbmc.executebuiltin('Container.Refresh()')

def update(path):
	xbmc.executebuiltin('Container.Update(%s)' % path)

def notify(text, icon = icon, time = 3000):
	# create notification
	dialog = xbmcgui.Dialog()
	dialog.notification(name, text, icon, time)
	del dialog

def current_view_id():
	win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	return str(win.getFocusId())

def set_content(type):
	xbmcplugin.setContent(plugin.handle, type)

def set_view(name):
	# update container content and view type
	xbmcplugin.setContent(plugin.handle, 'albums')
	# ref: https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary/xml
	views_dict = {
		'list': 50,
		'poster': 51,
		'iconwall': 52,
		'shift': 53,
		'infowall': 54,
		'widelist': 55,
		'wall': 500,
		'banner': 501,
		'fanart': 502
	}

	#for i in range(10): # assert view mode is set
	xbmc.executebuiltin('Container.SetViewMode(%s)' % (views_dict[name]))
	#	xbmc.sleep(10)

def youtube_url(id):
	return 'plugin://plugin.video.youtube/play/?video_id=' + id + '&incognito=true'

def elementum_url(type, title, year = '', id = ''):
	# ref: https://github.com/elgatito/elementum/blob/master/api/routes.go
	title = title.replace(' ', '+')
	query = "%s+%s" % (title, year)
	if type == 'context':
		url = "plugin://plugin.video.elementum" + quote("/context/media/%s/%s/play" % ('movie', query))
	elif type == 'context_query':
		url = "plugin://plugin.video.elementum/context/media/query/%s/play" % (quote(query))
	elif type == 'movie':
		url = "plugin://plugin.video.elementum" + quote("/movie/%s/play/%s" % (id, query))
	elif type == 'tv':
		url = "plugin://plugin.video.elementum" + quote("/show/%s/play" % (id))
	elif type == 'search':
		url = "plugin://plugin.video.elementum/search?q=" + quote(query)
	return url

def play(url):
	# play url
	xbmcplugin.setResolvedUrl(plugin.handle, True, xbmcgui.ListItem(path=url))
	#xbmc.executebuiltin("PlayMedia(%s)" % url)
	#xbmc.executebuiltin('RunPlugin(%s)' % url)
	#xbmc.executebuiltin('ShowPicture(%s)' % (url))
	#xbmc.Player().play(url)

def createFolder(function, label, arguments_list, image = icon_img, plot = 'aa', thumb = icon_img):
	# create folder linked to some function and given arguments
	li = ListItem(bold(label))
	li.setArt({
		'icon': img(thumb), 'thumb': img(thumb),
		'poster': img(image), 'banner': img(image)
	})
	#li.setInfo(type="pictures", infoLabels = {
	#	"PictureCaption": bold(plot)
	#})
	li.setProperty("fanart_image", img(fanart_img))
	addDirectoryItem(plugin.handle, plugin.url_for(function, *arguments_list), li, True)

def createWelcomeItem(message, plot, entrypoint_function):
	# create first item of addon
	welcomeItem = ListItem(bold(message))
	#welcomeItem.setInfo(type="pictures", infoLabels = {
	#	"plot": bold(plot)
	#})
	welcomeItem.setArt({'icon': img(icon_img)})
	welcomeItem.setProperty("fanart_image", img(fanart_img))
	addDirectoryItem(plugin.handle, plugin.url_for(entrypoint_function), welcomeItem, True)

def createItem(url, label, image, **kwargs):
	# create playable item
	li = ListItem(label)
	li.setProperty('IsPlayable', 'true')
	#li.setContentLookup(False)
	li.setInfo(type='pictures', infoLabels={
		'title': label,
		#'mediatype': 'image',
		'picturepath': url,
	})
	#infotag = li.getPictureInfoTag()
	
	#li.setInfo(type="image", infoLabels = {
	#	"title": label,
	#	#"mediatype": kwargs['mediatype']
	#})
	li.setArt({
		'thumb': image,
		#"fanart": GLOBAL_FANART
	})
	#li.setProperty("fanart_image", kwargs['fanart'])
	
	#CM_items = []
	# context menu for similar content
	#similar_link = plugin.base_url + '/similar/%s/%s/1' % (kwargs['id'], kwargs['mediatype'])
	#similar_item = ('Conteúdo similar', 'Container.Update(%s)' % (similar_link))
	#CM_items.append(similar_item)
	# context menu for original title search
	#title_item = ('Buscar com título original', 'RunPlugin(%s)' % (kwargs['real_title_search']))
	#CM_items.append(title_item)
	# add context menu to ListItem
	#li.addContextMenuItems(CM_items)
	addDirectoryItem(plugin.handle, url, li)

def endDirectory(cache = False):
	endOfDirectory(plugin.handle, succeeded=True, cacheToDisc=cache)

