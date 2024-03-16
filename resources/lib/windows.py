# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr

import pyxbmct
from resources.lib import utils, image
from uuid import uuid4
import os

IS_PORTRAIT_MODE = utils.get_setting('portrait_mode', bool)

dimensionsLandscape = {
	'w': 1280,
	'h': 720,
	'rows': 10,
	'columns': 10,
}

dimensionsPortrait = {
	'w': 1280,
	'h': 720,
	'rows': 20,
	'columns': 20,
}

controlInfoLandscape = { # row, column, rowspan, columnspan, pad_x, pad_y
	
	'image': [0, 2, 10, 6, 0, 0],
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

controlInfoPortrait = { # row, column, rowspan, columnspan, pad_x, pad_y
	
	'image': [0, 0, 20, 18, 1, 1],
	'fade_label': [0, 0, 1, 1],
	'sector_label': [0, 0, 1, 1],
	'list': [0, 0, 1, 1],

	'next_button': [0, 18, 10, 1],
	'previous_button': [10, 18, 10, 1],

	'stretch_button': [0, 0, 1, 1],
	'scale_up_button': [0, 0, 1, 1],
	'scale_down_button': [0, 0, 1, 1],

	'move_up_button': [0, 0, 1, 1],
	'move_down_button': [0, 0, 1, 1],
	
	'close_button': [0, 19, 20, 1],
}

dimensions = None
controlInfo = None

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

	def __init__(self, title = '', pages = [], headers = {}):
		super(PagesWindow, self).__init__(title)
		# view mode check
		global dimensions, controlInfo, IS_PORTRAIT_MODE
		dimensions = dimensionsLandscape
		controlInfo = controlInfoLandscape
		if IS_PORTRAIT_MODE:
			if not image.pil_imported:
				utils.notify(utils.localStr(32029))
				IS_PORTRAIT_MODE = False
			else:
				dimensions = dimensionsPortrait
				controlInfo = controlInfoPortrait	
		# window layout
		self.setGeometry(dimensions['w'], dimensions['h'], dimensions['rows'], dimensions['columns'])
		# pages
		if len(pages) == 0:
			utils.notify(utils.localStr(32013))
			self.close()
			return
		self.pages = []
		for item in pages:
			self.pages.append({
				'name': item['title'],
				'url': utils.base64_decode_url(item['link']),
				'headers': headers,
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
		self.list.addItems([utils.localStr(32014) % str(int(index) + 1) for index, item in enumerate(self.pages)])
		self.connect(self.list, self.selected_page)
		if IS_PORTRAIT_MODE: self.list.setVisible(False)
		# close button
		if IS_PORTRAIT_MODE:
			self.button = pyxbmct.Button('X')
		else:
			self.button = pyxbmct.Button(utils.localStr(32015))
		self.placeControl(self.button, *controlInfo['close_button'])
		self.connect(self.button, self.close)
		self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
		self.connect(ACTION_0, self.close)
		# image mode buttons
		self.btn_stretch = pyxbmct.Button(utils.localStr(32016))
		self.btn_up = pyxbmct.Button(utils.localStr(32017))
		self.btn_down = pyxbmct.Button(utils.localStr(32018))
		self.placeControl(self.btn_stretch, *controlInfo['stretch_button'])
		self.placeControl(self.btn_up, *controlInfo['scale_up_button'])
		self.placeControl(self.btn_down, *controlInfo['scale_down_button'])
		self.connect(self.btn_stretch, lambda: self.set_image_mode(MODE_STRETCH))
		self.connect(ACTION_1, lambda: self.set_image_mode(MODE_STRETCH))
		self.connect(self.btn_up, lambda: self.set_image_mode(MODE_SCALE_UP))
		self.connect(ACTION_2, lambda: self.set_image_mode(MODE_SCALE_UP))
		self.connect(self.btn_down, lambda: self.set_image_mode(MODE_SCALE_DOWN))
		self.connect(ACTION_3, lambda: self.set_image_mode(MODE_SCALE_DOWN))
		if IS_PORTRAIT_MODE:
			self.btn_stretch.setVisible(False)
			self.btn_up.setVisible(False)
			self.btn_down.setVisible(False)
		# move up button
		self.btn_mv_up = pyxbmct.Button(utils.localStr(32019))
		self.placeControl(self.btn_mv_up, *controlInfo['move_up_button'])
		self.connect(self.btn_mv_up, lambda: self.move(self.move_index - 1))
		self.connect(ACTION_6, lambda: self.move(self.move_index - 1))
		#self.connect(pyxbmct.ACTION_MOVE_UP, lambda: self.move(self.move_index - 1))
		#self.connect(pyxbmct.ACTION_MOUSE_WHEEL_UP, lambda: self.move(self.move_index - 1))
		if IS_PORTRAIT_MODE: self.btn_mv_up.setVisible(False)
		# move down button
		self.btn_mv_down = pyxbmct.Button(utils.localStr(32020))
		self.placeControl(self.btn_mv_down, *controlInfo['move_down_button'])
		self.connect(self.btn_mv_down, lambda: self.move(self.move_index + 1))
		self.connect(ACTION_9, lambda: self.move(self.move_index + 1))
		#self.connect(pyxbmct.ACTION_MOVE_DOWN, lambda: self.move(self.move_index + 1))
		#self.connect(pyxbmct.ACTION_MOUSE_WHEEL_DOWN, lambda: self.move(self.move_index + 1))
		if IS_PORTRAIT_MODE: self.btn_mv_down.setVisible(False)
		# next button
		if IS_PORTRAIT_MODE:
			self.btn_next = pyxbmct.Button('↑', font = 'font14')
		else:
			self.btn_next = pyxbmct.Button(utils.localStr(32006))
		self.placeControl(self.btn_next, *controlInfo['next_button'])
		self.connect(self.btn_next, lambda: self.update_page(self.current_page + 1))
		self.connect(ACTION_5, lambda: self.update_page(self.current_page + 1))
		#self.connect(pyxbmct.ACTION_MOVE_RIGHT, lambda: self.update_page(self.current_page + 1))
		# previous button
		if IS_PORTRAIT_MODE:
			self.btn_previous = pyxbmct.Button('↓', font = 'font14')
		else:
			self.btn_previous = pyxbmct.Button(utils.localStr(32007))
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
		if not IS_PORTRAIT_MODE:
			self.fade_label = pyxbmct.FadeLabel(_alignment = pyxbmct.ALIGN_CENTER_Y, font = 'font11')
			self.placeControl(self.fade_label, *controlInfo['fade_label'])
			label_for_fade = "%s%s%s%s" % (5*' ',
											(utils.localStr(32014) + ':[CR]') % str(self.current_page + 1),
											8*' ',
											self.pages[self.current_page]['name'])
			self.fade_label.addLabel(label_for_fade)
		# sector label
		if self.sector_label != None:
			self.sector_label.setVisible(False)
		if not IS_PORTRAIT_MODE:
			label_for_sector = "%s%s%s%s" % (5*' ', utils.localStr(32021), ':[CR]', 8*' ')
			color = '0xFF349A2C' # green
			if self.image_mode != MODE_SCALE_UP:
				label_for_sector += utils.localStr(32022)
				color = '0xFFDCD836' # yellow
			elif not image.pil_imported:
				label_for_sector += utils.localStr(32023)
				color = '0xFFE14C34' # red
			else:
				label_for_sector += '%s/%s' % (str(self.move_index + 1), str(image.TOTAL_SECTORS))
			self.sector_label = pyxbmct.Label(label_for_sector, alignment = pyxbmct.ALIGN_LEFT, font = 'font9', textColor = color)
			self.placeControl(self.sector_label, *controlInfo['sector_label'])
		# image
		if self.current_image != None:
			self.current_image.setVisible(False)
		current_url = self.pages[self.current_page]['url']
		current_headers = self.pages[self.current_page]['headers']
		fixed_image_mode = self.image_mode
		
		image_response = utils.do_request('get', current_url, headers = current_headers)
		if image_response != None:
			self.remove_and_update_uuid('original')
			self.remove_and_update_uuid('rotated')
			self.remove_and_update_uuid('cut')
			utils.write_file(utils.datapath(self.original_uuid), image_response.content, 'wb')

			pil_obj = image.PageImage(utils.datapath(self.original_uuid))
			# portrait mode
			if IS_PORTRAIT_MODE:
				fixed_image_mode = MODE_SCALE_DOWN

				#if self.image_mode == MODE_SCALE_UP and pil_obj.cut(utils.datapath(self.cut_uuid), self.move_index):
				#	pil_obj_cut = image.PageImage(utils.datapath(self.cut_uuid))
				#	fixed_image_mode = MODE_SCALE_DOWN # at scale up mode with cut image, we actually use scale down mode
				#	if pil_obj_cut.rotate(utils.datapath(self.rotated_uuid)):
				#		to_show = utils.datapath(self.rotated_uuid)
				#	else:
				#		to_show = utils.datapath(self.original_uuid) # in case rotate fails, use original file. It won't likely happen
				
				if pil_obj.rotate(utils.datapath(self.rotated_uuid)):
					to_show = utils.datapath(self.rotated_uuid)
				else:
					utils.notify(utils.localStr(32030), time = 1000, sound = False)
					to_show = utils.datapath(self.original_uuid)
			# landscape mode
			else:
				if self.image_mode == MODE_SCALE_UP and pil_obj.cut(utils.datapath(self.cut_uuid), self.move_index):
					fixed_image_mode = MODE_SCALE_DOWN # at scale up mode with cut image, we actually use scale down mode
					to_show = utils.datapath(self.cut_uuid)
				else:
					to_show = utils.datapath(self.original_uuid)
		else:
			utils.notify(utils.localStr(32031), time = 1000, sound = False)
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

		rotate_animations = [
							('WindowOpen', self.animation_rotate(90, 'rotate', 1)),
							('Focus', self.animation_rotate(90, 'rotate', 1)),
							]
		
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

	def animation_rotate(self, angle, type = 'rotate', time = 100):
		# rotate, rotatex, rotatey
		return 'effect=%s start=0 end=%s center=auto time=%s' % (type, angle, time)
