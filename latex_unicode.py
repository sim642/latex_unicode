# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 by Simmo Saan <simmo.saan@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# History:
#
# 2016-06-14, Simmo Saan <simmo.saan@gmail.com>
#   version 0.2: automatically load XML from W3 website if not available
# 2016-06-13, Simmo Saan <simmo.saan@gmail.com>
#   version 0.1: initial script
#

"""
Replace LaTeX with unicode representations
"""

from __future__ import print_function

SCRIPT_NAME = "latex_unicode"
SCRIPT_AUTHOR = "Simmo Saan <simmo.saan@gmail.com>"
SCRIPT_VERSION = "0.2"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Replace LaTeX with unicode representations"

SCRIPT_REPO = "https://github.com/sim642/latex_unicode"

SCRIPT_COMMAND = SCRIPT_NAME

IMPORT_OK = True

try:
	import weechat
except ImportError:
	print("This script must be run under WeeChat.")
	print("Get WeeChat now at: http://www.weechat.org/")
	IMPORT_OK = False

import os
from lxml import etree

xml_path = None
chars = {}

def log(string):
	weechat.prnt("", "{}: {}".format(SCRIPT_NAME, string))

def setup():
	global xml_path
	xml_path = weechat.string_eval_path_home("%h/latex_unicode.xml", "", "", "")

	if os.path.isfile(xml_path):
		setup_from_file()
	else:
		setup_from_url()

def setup_from_url():
	log("downloading XML...")
	weechat.hook_process_hashtable("url:https://www.w3.org/Math/characters/unicode.xml",
		{
			"file_out": xml_path
		},
		30000, "download_cb", "")

def download_cb(data, command, return_code, out, err):
	log("downloaded XML")
	setup_from_file()
	return weechat.WEECHAT_RC_OK

def setup_from_file():
	log("loading XML...")
	global chars

	root = etree.parse(xml_path)
	for character in root.xpath("character"):
		char = character.get("dec")
		if "-" not in char:
			char = unichr(int(char))
			
			ams = character.xpath("AMS")
			if ams:
				chars[ams[0].text] = char

			latex = character.xpath("latex")
			if latex:
				latex = latex[0].text.strip()
				if latex[0] == "\\":
					chars[latex] = char

	log("loaded XML")

def latex_unicode_replace(string):
	string = string.decode("utf-8")
	for tex, char in chars.items():
		string = string.replace(tex + " ", char)
	return string.encode("utf-8")

def input_text_content_cb(data, modifier, modifier_data, string):
	"""
	Handle "input_text_content" modifier.
	"""

	return latex_unicode_replace(string)

def weechat_print_cb(data, modifier, modifier_data, string):
	"""
	Handle "weechat_print" modifier.
	"""

	return latex_unicode_replace(string)

def command_cb(data, buffer, args):
	"""
	Handle command.
	"""
	return weechat.WEECHAT_RC_OK

if __name__ == "__main__" and IMPORT_OK:
	if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
		weechat.hook_modifier("input_text_content", "input_text_content_cb", "")
		weechat.hook_modifier("weechat_print", "weechat_print_cb", "")

		weechat.hook_command(SCRIPT_COMMAND, SCRIPT_DESC,
		"""""", """""", """""",
		"command_cb", "")

		setup()
