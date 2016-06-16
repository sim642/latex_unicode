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
# 2016-06-15, Simmo Saan <simmo.saan@gmail.com>
#   version 0.5: remove lxml dependency
# 2016-06-15, Simmo Saan <simmo.saan@gmail.com>
#   version 0.4: more options for replacement location fine tuning
# 2016-06-14, Simmo Saan <simmo.saan@gmail.com>
#   version 0.3: options for disabling/enabling replacements by location
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
SCRIPT_VERSION = "0.5"
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
import xml.etree.ElementTree as ET

SETTINGS = {
	"input": (
		"on",
		"replace LaTeX in input display: off, on",
		True),
	"send": (
		"on",
		"replace LaTeX in input sending: off, on",
		True),
	"buffer": (
		"on",
		"replace LaTeX in buffer: off, on",
		True)
}

SETTINGS_PREFIX = "plugins.var.python.{}.".format(SCRIPT_NAME)

hooks = []

xml_path = None
replacements = []

def log(string):
	"""Log script's message to core buffer."""

	weechat.prnt("", "{}: {}".format(SCRIPT_NAME, string))

def setup():
	"""Load replacements from available resource."""

	global xml_path
	xml_path = weechat.string_eval_path_home("%h/latex_unicode.xml", "", "", "")

	if os.path.isfile(xml_path):
		setup_from_file()
	else:
		setup_from_url()

def setup_from_url():
	"""Download replacements and store them in weechat home directory."""

	log("downloading XML...")
	weechat.hook_process_hashtable("url:https://www.w3.org/Math/characters/unicode.xml",
		{
			"file_out": xml_path
		},
		30000, "download_cb", "")

def download_cb(data, command, return_code, out, err):
	"""Load downloaded replacements."""

	log("downloaded XML")
	setup_from_file()
	return weechat.WEECHAT_RC_OK

def setup_from_file():
	"""Load replacements from file in weechat home directory."""

	log("loading XML...")
	global replacements

	root = ET.parse(xml_path)
	for character in root.findall("character"):
		dec = character.get("dec")
		if "-" not in dec: # is not a range of characters
			char = unichr(int(dec))
			
			ams = character.find("AMS")
			if ams is not None:
				replacements.append((ams.text, char))

			latex = character.find("latex")
			if latex is not None:
				latex = latex.text.strip()
				if latex[0] == "\\": # only add \commands
					replacements.append((latex, char))

	replacements = sorted(replacements, key=lambda replacement: len(replacement[0]), reverse=True) # sort by tex string length descendingly

	log("loaded XML")
	hook_modifiers()

def hook_modifiers():
	"""Update modifier hooks to match settings."""

	# remove existing modifier hooks
	global hooks
	for hook in hooks:
		weechat.unhook(hook)
	hooks = []

	# add hooks according to settings

	input_option = weechat.config_get_plugin("input")
	if weechat.config_string_to_boolean(input_option):
		hooks.append(weechat.hook_modifier("input_text_display", "modifier_cb", ""))

	send_option = weechat.config_get_plugin("send")
	if weechat.config_string_to_boolean(send_option):
		hooks.append(weechat.hook_modifier("input_text_for_buffer", "modifier_cb", ""))

	buffer_option = weechat.config_get_plugin("buffer")
	if weechat.config_string_to_boolean(buffer_option):
		hooks.append(weechat.hook_modifier("weechat_print", "modifier_cb", ""))

def latex_unicode_replace(string):
	"""Apply replacements to message."""

	string = string.decode("utf-8")
	for tex, char in replacements:
		string = string.replace(tex, char)
	return string.encode("utf-8")

def modifier_cb(data, modifier, modifier_data, string):
	"""Handle modifier hooks."""

	return latex_unicode_replace(string)

def command_cb(data, buffer, args):
	"""Handle command hook."""

	return weechat.WEECHAT_RC_OK

def config_cb(data, option, value):
	"""Handle config hooks (option changes)."""

	option = option[len(SETTINGS_PREFIX):]

	if SETTINGS[option][2]: # if option requires modifier hooks update
		hook_modifiers()

	return weechat.WEECHAT_RC_OK

if __name__ == "__main__" and IMPORT_OK:
	if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
		weechat.hook_command(SCRIPT_COMMAND, SCRIPT_DESC,
		"""""", """""", """""",
		"command_cb", "")

		for option, value in SETTINGS.items():
			if not weechat.config_is_set_plugin(option):
				weechat.config_set_plugin(option, value[0])

			weechat.config_set_desc_plugin(option, "%s (default: \"%s\")" % (value[1], value[0]))

		weechat.hook_config(SETTINGS_PREFIX + "*", "config_cb", "")

		setup()
