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
	'list': [1, 0, 9, 2],
	
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
		self.image_mode = MODE_SCALE_DOWN
		self.move_index = 0 # page top
		self.fade_label = None
		self.current_image = None
		self.original_uuid = None # use UUID instead fixed/image name because Kodi cache behaviour
		self.rotated_uuid = None
		self.cut_uuid = None
		self.update_page(self.current_page)
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
		# image mode buttons
		btn_stretch = pyxbmct.Button('Stretch')
		btn_up = pyxbmct.Button('Scale Up')
		btn_down = pyxbmct.Button('Scale Down')
		self.placeControl(btn_stretch, *controlInfo['stretch_button'])
		self.placeControl(btn_up, *controlInfo['scale_up_button'])
		self.placeControl(btn_down, *controlInfo['scale_down_button'])
		self.connect(btn_stretch, lambda: self.set_image_mode(MODE_STRETCH))
		self.connect(btn_up, lambda: self.set_image_mode(MODE_SCALE_UP))
		self.connect(btn_down, lambda: self.set_image_mode(MODE_SCALE_DOWN))
		# move up button
		btn_mv_up = pyxbmct.Button('Move Up')
		self.placeControl(btn_mv_up, *controlInfo['move_up_button'])
		self.connect(btn_mv_up, lambda: self.move(self.move_index - 1))
		self.connect(pyxbmct.ACTION_MOVE_UP, lambda: self.move(self.move_index - 1))
		self.connect(pyxbmct.ACTION_MOUSE_WHEEL_UP, lambda: self.move(self.move_index - 1))
		# move down button
		btn_mv_down = pyxbmct.Button('Move Down')
		self.placeControl(btn_mv_down, *controlInfo['move_down_button'])
		self.connect(btn_mv_down, lambda: self.move(self.move_index + 1))
		self.connect(pyxbmct.ACTION_MOVE_DOWN, lambda: self.move(self.move_index + 1))
		self.connect(pyxbmct.ACTION_MOUSE_WHEEL_DOWN, lambda: self.move(self.move_index + 1))
		# next button
		btn_next = pyxbmct.Button('Next Page')
		self.placeControl(btn_next, *controlInfo['next_button'])
		self.connect(btn_next, lambda: self.update_page(self.current_page + 1))
		self.connect(pyxbmct.ACTION_MOVE_RIGHT, lambda: self.update_page(self.current_page + 1))
		# previous button
		btn_previous = pyxbmct.Button('Previous Page')
		self.placeControl(btn_previous, *controlInfo['previous_button'])
		self.connect(btn_previous, lambda: self.update_page(self.current_page - 1))
		self.connect(pyxbmct.ACTION_MOVE_LEFT, lambda: self.update_page(self.current_page - 1))

	def update_page(self, index):
		if index != -1 and index < len(self.pages):
			self.current_page = index
		# label
		if self.fade_label != None:
			self.fade_label.setVisible(False)
		self.fade_label = pyxbmct.FadeLabel()
		self.placeControl(self.fade_label, *controlInfo['fade_label'])
		self.fade_label.addLabel(10*' ' + self.pages[self.current_page]['name'])
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

	def setAnimation(self, control):
		control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
								('WindowClose', 'effect=fade start=100 end=0 time=500',)])


