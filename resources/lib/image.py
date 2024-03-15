# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr
# ref: https://github.com/Simon125q/cut_and_rotate_images

try:
	from PIL import Image
	pil_imported = True
except:
	pil_imported = False

TOTAL_SECTORS = 3

class PageImage:

	def __init__(self, filename):
		self.is_pil_imported = pil_imported
		if not self.is_pil_imported: return None
		self.input = filename
		self.img = Image.open(self.input)
		self.size = self.width, self.height = self.img.size

	def check_extension(self, name):
		if not name.endswith('.png'):
			return '%s.png' % name
		return name

	def rotate(self, output, deg = 90):
		if not self.is_pil_imported: return False
		self.output = self.check_extension(output)
		im_rotate = self.img.rotate(deg, expand = True)
		if deg == 90 or deg == 270:
			im_rotate.resize((self.height, self.width), resample = 0)
		im_rotate.save(self.output)
		return True

	def cut(self, output, sector = 0, total = TOTAL_SECTORS):
		if not self.is_pil_imported: return False
		self.output = self.check_extension(output)
		left, right = 0, self.width
		height_size = self.height//total
		top = sector * height_size
		bottom = ((sector + 1) * height_size) + (height_size//3)
		im_cut = self.img.crop((left, top, right, bottom))
		im_cut.save(self.output)
		return True

