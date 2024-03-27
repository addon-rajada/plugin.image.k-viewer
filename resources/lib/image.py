# -*- coding: utf-8 -*-
# Copyright (C) 2024 gbchr
# ref: https://github.com/Simon125q/cut_and_rotate_images
# ref: https://stackoverflow.com/questions/10615901/trim-whitespace-using-pil

try:
	from PIL import Image, ImageChops
	pil_imported = True
except:
	pil_imported = False

TOTAL_SECTORS = 3

class PageImage:

	def __init__(self, filename):
		self.is_pil_imported = pil_imported
		if not self.is_pil_imported: return None
		self.input = filename
		try: self.img = Image.open(self.input)
		except Exception as e:
			self.is_img_opened = False
			return None
		self.size = self.width, self.height = self.img.size
		self.is_img_opened = True

	def check_extension(self, name):
		if not name.endswith('.png'):
			return '%s.png' % name
		return name

	def rotate(self, output, trim, deg = 90):
		if not self.is_pil_imported: return False
		if not self.is_img_opened: return False
		self.output = self.check_extension(output)
		try:
			im_rotate = self.img.rotate(deg, expand = True)
			if deg == 90 or deg == 270:
				im_rotate.resize((self.height, self.width), resample = 0)
			if trim:
				if self.trim(self.output, im_rotate):
					return True # early return if trim succeeded
			im_rotate.save(self.output)
			return True
		except Exception as e:
			return False

	def cut(self, output, trim, sector = 0, total = TOTAL_SECTORS):
		if not self.is_pil_imported: return False
		if not self.is_img_opened: return False
		self.output = self.check_extension(output)
		left, right = 0, self.width
		height_size = self.height//total
		top = sector * height_size
		bottom = ((sector + 1) * height_size) + (height_size//3)
		if bottom > self.height: # for last page
			offset = bottom - top
			top = self.height - offset
			bottom = self.height
		try:
			im_cut = self.img.crop((left, top, right, bottom))
			if trim:
				if self.trim(self.output, im_cut):
					return True # early return if trim succeeded
			im_cut.save(self.output)
			return True
		except Exception as e:
			return False

	def trim(self, output, image = None):
		if not self.is_pil_imported: return False
		if not self.is_img_opened: return False
		self.output = self.check_extension(output)
		try:
			base_img = self.img.convert('RGB') if image == None else image.convert('RGB') # use image or self.img
			bg = Image.new(base_img.mode, base_img.size, base_img.getpixel((0,0))) # background color
			diff = ImageChops.difference(base_img, bg)
			diff = ImageChops.add(diff, diff, 2.0, -100) # subtracts scalar
			bbox = diff.getbbox()
			if bbox:
				crop_img = base_img.crop(bbox)
				crop_img.save(self.output)
				return True
			return False
		except Exception as e:
			return False
