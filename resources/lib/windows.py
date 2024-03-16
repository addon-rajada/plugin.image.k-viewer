# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

import pyxbmct
from resources.lib import utils, image
from uuid import uuid4
import os

dimensions = {
	'w': 1280,
	'h': 720,
	'rows': 10,
	'columns': 10,
}

controlInfo = { # row, column, rowspan, columnspan, pad_x, pad_y
	
	'image': [0, 2, 10, 6],
	'fade_label': [0, 0, 1, 2],
	'sector_label': [1, 0, 1, 2, 5, 0],
	'list': [2, 0, 8, 2],
	
	'next_button': [1, 8, 1, 2],
	'previous_button': [2, 8, 1, 2],

	'stretch_button': [4, 8, 1, 2],
	'scale_up_button': [5, 8, 1, 1],
	'scale_down_button': [5, 9, 1, 1],

	'move_up_button': [6, 8, 1, 1],
	'move_down_button': [6, 9, 1, 1],

	'close_button': [9, 8, 1, 2],
}

MODE_STRETCH = 0
MODE_SCALE_UP = 1
MODE_SCALE_DOWN = 2

ACTION_0 = 58
ACTION_1 = 59
ACTION_2 = 60
ACTION_3 = 61
ACTION_4 = 62
ACTION_5 = 63
ACTION_6 = 64
ACTION_7 = 65
ACTION_8 = 66
ACTION_9 = 67

class PagesWindow(pyxbmct.AddonDialogWindow):

	def __init__(self, title = '', pages = []):
		super(PagesWindow, self).__init__(title)
		self.setGeometry(dimensions['w'], dimensions['h'], dimensions['rows'], dimensions['columns'])
		# pages
		if len(pages) == 0:
			utils.notify('No Pages')
			self.close()
			return
		self.pages = []
		for item in pages:
			self.pages.append({
				'name': item['title'],
				'url': utils.base64_decode_url(item['link'])
			})
		self.current_page = 0
		# auxiliar variables
		self.image_mode = MODE_SCALE_DOWN
		self.move_index = 0 # page top
		self.fade_label = None
		self.current_image = None
		self.original_uuid = None # use UUID instead fixed/image name because Kodi cache behaviour
		self.rotated_uuid = None
		self.cut_uuid = None
		self.sector_label = None
		# list
		self.list = pyxbmct.List()
		self.placeControl(self.list, *controlInfo['list'])
		self.list.addItems(['Page %s' % str(int(index) + 1) for index, item in enumerate(self.pages)])
		self.connect(self.list, self.selected_page)
		# close button
		self.button = pyxbmct.Button('Close')
		self.placeControl(self.button, *controlInfo['close_button'])
		self.connect(self.button, self.close)
		self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
		self.connect(ACTION_0, self.close)
		# image mode buttons
		self.btn_stretch = pyxbmct.Button('Stretch')
		self.btn_up = pyxbmct.Button('Scale Up')
		self.btn_down = pyxbmct.Button('Scale Down')
		self.placeControl(self.btn_stretch, *controlInfo['stretch_button'])
		self.placeControl(self.btn_up, *controlInfo['scale_up_button'])
		self.placeControl(self.btn_down, *controlInfo['scale_down_button'])
		self.connect(self.btn_stretch, lambda: self.set_image_mode(MODE_STRETCH))
		self.connect(ACTION_1, lambda: self.set_image_mode(MODE_STRETCH))
		self.connect(self.btn_up, lambda: self.set_image_mode(MODE_SCALE_UP))
		self.connect(ACTION_2, lambda: self.set_image_mode(MODE_SCALE_UP))
		self.connect(self.btn_down, lambda: self.set_image_mode(MODE_SCALE_DOWN))
		self.connect(ACTION_3, lambda: self.set_image_mode(MODE_SCALE_DOWN))
		# move up button
		self.btn_mv_up = pyxbmct.Button('Move Up')
		self.placeControl(self.btn_mv_up, *controlInfo['move_up_button'])
		self.connect(self.btn_mv_up, lambda: self.move(self.move_index - 1))
		self.connect(ACTION_6, lambda: self.move(self.move_index - 1))
		#self.connect(pyxbmct.ACTION_MOVE_UP, lambda: self.move(self.move_index - 1))
		#self.connect(pyxbmct.ACTION_MOUSE_WHEEL_UP, lambda: self.move(self.move_index - 1))
		# move down button
		self.btn_mv_down = pyxbmct.Button('Move Down')
		self.placeControl(self.btn_mv_down, *controlInfo['move_down_button'])
		self.connect(self.btn_mv_down, lambda: self.move(self.move_index + 1))
		self.connect(ACTION_9, lambda: self.move(self.move_index + 1))
		#self.connect(pyxbmct.ACTION_MOVE_DOWN, lambda: self.move(self.move_index + 1))
		#self.connect(pyxbmct.ACTION_MOUSE_WHEEL_DOWN, lambda: self.move(self.move_index + 1))
		# next button
		self.btn_next = pyxbmct.Button('Next Page')
		self.placeControl(self.btn_next, *controlInfo['next_button'])
		self.connect(self.btn_next, lambda: self.update_page(self.current_page + 1))
		self.connect(ACTION_5, lambda: self.update_page(self.current_page + 1))
		#self.connect(pyxbmct.ACTION_MOVE_RIGHT, lambda: self.update_page(self.current_page + 1))
		# previous button
		self.btn_previous = pyxbmct.Button('Previous Page')
		self.placeControl(self.btn_previous, *controlInfo['previous_button'])
		self.connect(self.btn_previous, lambda: self.update_page(self.current_page - 1))
		self.connect(ACTION_4, lambda: self.update_page(self.current_page - 1))
		#self.connect(pyxbmct.ACTION_MOVE_LEFT, lambda: self.update_page(self.current_page - 1))

		# show first image
		self.update_page(self.current_page)
		# navigation
		self.setControlsNavigation()
		# initial focus
		self.setFocus(self.btn_next)
		# animations
		self.setControlsAnimations()

	def setControlsNavigation(self):
		# list
		self.list.controlRight(self.btn_next)
		# image
		self.current_image.controlLeft(self.list)
		self.current_image.controlRight(self.btn_next)
		# next
		self.btn_next.controlDown(self.btn_previous)
		self.btn_next.controlUp(self.button)
		self.btn_next.controlLeft(self.list)
		# previous
		self.btn_previous.controlUp(self.btn_next)
		self.btn_previous.controlDown(self.btn_stretch)
		self.btn_previous.controlLeft(self.list)
		# stretch
		self.btn_stretch.controlUp(self.btn_previous)
		self.btn_stretch.controlDown(self.btn_up)
		self.btn_stretch.controlLeft(self.list)
		# scale up
		self.btn_up.controlUp(self.btn_stretch)
		self.btn_up.controlDown(self.btn_mv_up)
		self.btn_up.controlRight(self.btn_down)
		self.btn_up.controlLeft(self.list)
		# scale down
		self.btn_down.controlUp(self.btn_stretch)
		self.btn_down.controlDown(self.btn_mv_down)
		self.btn_down.controlLeft(self.btn_up)
		# move up
		self.btn_mv_up.controlUp(self.btn_up)
		self.btn_mv_up.controlDown(self.button)
		self.btn_mv_up.controlRight(self.btn_mv_down)
		self.btn_mv_up.controlLeft(self.list)
		# move down
		self.btn_mv_down.controlUp(self.btn_down)
		self.btn_mv_down.controlDown(self.button)
		self.btn_mv_down.controlLeft(self.btn_mv_up)
		# close button
		self.button.controlUp(self.btn_mv_up)
		self.button.controlDown(self.btn_next)
		self.button.controlLeft(self.list)

	def update_page(self, index):
		if index != -1 and index < len(self.pages):
			if index != self.current_page: self.move_index = 0 # reset zoom sector if another page
			self.current_page = index
		# label
		if self.fade_label != None:
			self.fade_label.setVisible(False)
		self.fade_label = pyxbmct.FadeLabel(_alignment = pyxbmct.ALIGN_CENTER_Y, font = 'font11')
		self.placeControl(self.fade_label, *controlInfo['fade_label'])
		self.fade_label.addLabel(5*' ' + 'Filename:[CR]' + 8*' ' + self.pages[self.current_page]['name'])
		# sector label
		if self.sector_label != None:
			self.sector_label.setVisible(False)
		label = 5*' ' + 'Zoom sector:[CR]' + 8*' '
		color = '0xFF349A2C' # green
		if self.image_mode != MODE_SCALE_UP:
			label += 'Not at Scale Up Mode'
			color = '0xFFDCD836' # yellow
		elif not image.pil_imported:
			label += 'PIL not supported'
			color = '0xFFE14C34' # red
		else: label += '%s/%s' % (self.move_index + 1, image.TOTAL_SECTORS)
		self.sector_label = pyxbmct.Label(label, alignment = pyxbmct.ALIGN_LEFT, font = 'font9', textColor = color)
		self.placeControl(self.sector_label, *controlInfo['sector_label'])
		# image
		if self.current_image != None:
			self.current_image.setVisible(False)
		current_url = self.pages[self.current_page]['url']
		fixed_image_mode = self.image_mode
		
		image_response = utils.do_request(current_url)
		if image_response != None:
			self.remove_and_update_uuid('original')
			self.remove_and_update_uuid('rotated')
			self.remove_and_update_uuid('cut')
			utils.write_file(utils.datapath(self.original_uuid), image_response.content, 'wb')

			pil_obj = image.PageImage(utils.datapath(self.original_uuid))
			if self.image_mode == MODE_SCALE_UP and pil_obj.cut(utils.datapath(self.cut_uuid), self.move_index):
				fixed_image_mode = MODE_SCALE_DOWN # at scale up mode with cut image, we actually use scale down mode
				to_show = utils.datapath(self.cut_uuid)
			else:
				to_show = utils.datapath(self.original_uuid)
		else:
			to_show = current_url # use URL instead local file if response is None
		
		self.current_image = pyxbmct.Image(to_show, aspectRatio=fixed_image_mode)
		self.current_image.setImage(to_show, useCache=False)
		self.placeControl(self.current_image, *controlInfo['image'])

		self.setControlsAnimations()

	def set_image_mode(self, mode):
		self.image_mode = mode
		self.update_page(-1)

	def move(self, index):
		if index >= 0 and index < image.TOTAL_SECTORS and self.image_mode == MODE_SCALE_UP:
			self.move_index = index
			self.update_page(-1)

	def remove_and_update_uuid(self, option):
		if option == 'original':
			self.remove_uuid(self.original_uuid)
			self.original_uuid = str(uuid4()) + '.png'
		elif option == 'rotated':
			self.remove_uuid(self.rotated_uuid)
			self.rotated_uuid = str(uuid4()) + '.png'
		elif option == 'cut':
			self.remove_uuid(self.cut_uuid)
			self.cut_uuid = str(uuid4()) + '.png'

	def remove_uuid(self, uuid):
		if uuid != None and os.path.exists(utils.datapath(uuid)):
			os.remove(utils.datapath(uuid))

	def selected_page(self):
		current_pos = self.list.getSelectedPosition()
		self.update_page(current_pos)
		current_item = self.list.getListItem(current_pos)
		#utils.notify('%s - %s' % (str(current_pos), current_item.getLabel()))

	def setControlsAnimations(self):
		button_animations = [ ('Focus', self.animation_fade(80, 100)), ]

		self.btn_next.setAnimations(button_animations)
		self.btn_previous.setAnimations(button_animations)
		self.btn_stretch.setAnimations(button_animations)
		self.btn_up.setAnimations(button_animations)
		self.btn_down.setAnimations(button_animations)
		self.btn_mv_up.setAnimations(button_animations)
		self.btn_mv_down.setAnimations(button_animations)
		self.button.setAnimations(button_animations)

	#def onAction(self, action):
	#	btn_code = action.getButtonCode()
	#	id = action.getId()
	#	utils.notify('Action - ID:%s Code:%s' % (id, str(btn_code)), time=1000)
	
	#def onControl(self, control):
	#	pass

	def setAnimation(self, control):
		animations = [
			('WindowOpen', self.animation_fade(0, 100)),
			('WindowClose', self.animation_fade(100, 0)),
		]
		control.setAnimations(animations)

	def animation_fade(self, start, end, time = 300):
		return 'effect=fade start=%s end=%s time=%s' % (start, end, time)

	def animation_zoom(self, h_percent, v_percent, time = 100):
		# horizontal,vertical or left,top,width,height
		return 'effect=zoom end=%s,%s center=auto time=%s' % (h_percent, v_percent, time)

	def animation_rotate(self, angle, time = 100):
		return 'effect=rotate end=%s center=auto time=%s' % (angle, time)
