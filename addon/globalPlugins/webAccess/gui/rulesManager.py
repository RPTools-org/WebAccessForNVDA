# globalPlugins/webAccess/gui/rulesManager.py
# -*- coding: utf-8 -*-

# This file is part of Web Access for NVDA.
# Copyright (C) 2015-2019 Accessolutions (http://accessolutions.fr)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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
# See the file COPYING.txt at the root of this distribution for more details.

__version__ = "2019.03.08"

__author__ = u"Frédéric Brugnot <f.brugnot@accessolutions.fr>"


import wx

import addonHandler
addonHandler.initTranslation()
import controlTypes
import gui
import inputCore
from logHandler import log
import ui

from .. import ruleHandler
from ..webAppLib import *
from .. import webModuleHandler
from . import ListCtrlAutoWidth


def show(context):
	gui.mainFrame.prePopup()
	Dialog(gui.mainFrame).ShowModal(context)
	gui.mainFrame.postPopup()


class Dialog(wx.Dialog):

	lastSelectedElementType = 0
	ELEMENT_TYPES = (
		("Name", _("Name")),
		("Gestures", _("Gestures")),
		("Contexts", _("Contexts")),
		("Other1", _("Other1")),
		("Other2", _("Other2")),
	)
	
	def __init__(self, parent):
		super(Dialog, self).__init__(gui.mainFrame, wx.ID_ANY, _("Rules List"))

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		contentsSizer = wx.BoxSizer(wx.VERTICAL)

		radioButtons = wx.RadioBox(self, wx.ID_ANY, label=_("Group by: "), choices=tuple(et[1] for et in self.ELEMENT_TYPES))
		radioButtons.SetSelection(self.lastSelectedElementType)
		radioButtons.Bind(wx.EVT_RADIOBOX, self.onElementTypeChange)
		contentsSizer.Add(radioButtons, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		filtersSizer = wx.BoxSizer()

		filterText = _("Filt&er by:")
		labelledCtrl = gui.guiHelper.LabeledControlHelper(self, filterText, wx.TextCtrl)
		self.filterEdit = labelledCtrl.control
		self.filterEdit.Bind(wx.EVT_TEXT, self.onFilterEditTextChange)
		filtersSizer.Add(labelledCtrl.sizer)
		filtersSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		self.displayActiveRules = wx.CheckBox(self, label=_("Display only &active rules"))
		self.displayActiveRules.Value = False
		self.displayActiveRules.Bind(wx.EVT_CHECKBOX, self.OnDisplayActiveRules)
		filtersSizer.Add(self.displayActiveRules, flag=wx.EXPAND)

		contentsSizer.Add(filtersSizer)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		self.tree = wx.TreeCtrl(self, size=wx.Size(500, 600), style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT)
		self.treeRoot = self.tree.AddRoot("root")
		contentsSizer.Add(self.tree,flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		self.ruleList = wx.ListBox(self)
		self.ruleList.Bind(wx.EVT_LISTBOX, self.OnRuleListChoice)
		contentsSizer.Add(self.ruleList, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		self.ruleComment = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL)
		contentsSizer.Add(self.ruleComment, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		bHelper = gui.guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.movetoButton = bHelper.addButton(self, label=_("Move to"))
		self.movetoButton.Bind(wx.EVT_BUTTON, lambda evt: self.OnMoveto)
		self.AffirmativeId = self.movetoButton.Id
		self.movetoButton.SetDefault()

		self.newButton = bHelper.addButton(self, label=_("&New rule..."))
		self.newButton.Bind(wx.EVT_BUTTON, lambda evt: self.OnNew)

		self.editButton = bHelper.addButton(self, label=_("&Edit..."))
		self.editButton.Bind(wx.EVT_BUTTON, lambda evt: self.OnEdit)
		self.editButton.Enabled = False

		self.deleteButton = bHelper.addButton(self, label=_("&Delete"))
		self.deleteButton.Bind(wx.EVT_BUTTON, lambda evt: self.OnDelete)
		self.deleteButton.Enabled = False

		contentsSizer.Add(bHelper.sizer, flag=wx.ALIGN_RIGHT)
		mainSizer.Add(contentsSizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Add(self.CreateSeparatedButtonSizer(wx.CLOSE), flag=wx.EXPAND)
		mainSizer.Fit(self)
		self.Sizer = mainSizer

		self.initElementType(self.ELEMENT_TYPES[self.lastSelectedElementType][0])
		self.CentreOnScreen()


	def __del__(self):
		Dialog._instance = None


	def InitData(self, context):
		self.context = context
		webModule = context["webModule"]
		self.markerManager = webModule.markerManager
		self.rule = context["rule"]
		self.RefreshRuleList()



	def RefreshRuleList(self, selectName=None):
		"""
		Refresh the list of rules.
		
		If *selectName" is set, the rule with that name gets selected.
		Otherwise, the rule matching the current focus in the document,
		if any, gets selected.
		"""
		api.processPendingEvents()
		if not selectName:
			sel = self.ruleList.Selection
			if sel >= 0:
				selectName = self.ruleList.GetClientData(sel).name
		self.ruleList.Clear()
		sel = None
		index = 0
		for result in self.markerManager.getResults():
			self.ruleList.Append(result.getDisplayString(), result)
			if selectName is not None:
				if result.name == selectName:
					sel == index
			elif result == self.rule:
				sel = index
			index += 1
		if not self.displayActiveRules.Value:
			for query in self.markerManager.getQueries():
				if query not in [r.markerQuery for r in self.markerManager.getResults()]:
					self.ruleList.Append(query.getDisplayString(), query)
					if query.name == selectName:
						sel = index
					index += 1
		if sel is not None:
			self.ruleList.Selection = sel
			self.ruleList.EnsureVisible(sel)
		self.OnRuleListChoice(None)


	def OnMoveto(self, evt):
		sel = self.ruleList.Selection
		result = self.ruleList.GetClientData(sel)
		if not isinstance(result, ruleHandler.MarkerResult):
			wx.Bell()
			return
		result.script_moveto (None)
		self.Close()


	def OnNew(self, evt):
		context = self.context.copy()  # Shallow copy
		if ruleHandler.showCreator(context):
			self.RefreshRuleList(context["data"]["rule"]["name"])
			self.ruleList.SetFocus()


	def OnDelete(self, evt):
		sel = self.ruleList.Selection
		if gui.messageBox(
			_("Are you sure you want to delete this rule?"),
			_("Confirm Deletion"),
			wx.YES | wx.NO | wx.ICON_QUESTION, self
		) == wx.NO:
			return
		rule = self.ruleList.GetClientData(sel)
		if isinstance(rule, ruleHandler.MarkerQuery):
			query = rule
		else:
			query = rule.markerQuery
		self.markerManager.removeQuery(query)
		webModuleHandler.update(
			webModule=self.context["webModule"],
			focus=self.context["focusObject"]
			)
		self.RefreshRuleList()
		self.ruleList.SetFocus()


	def OnRuleListChoice(self, evt):
		sel = self.ruleList.Selection
		if sel < 0:
			self.movetoButton.Enabled = False
			self.deleteButton.Enabled = False
			self.editButton.Enabled = False
			return
		marker = self.ruleList.GetClientData(sel)
		if isinstance(marker, ruleHandler.VirtualMarkerQuery):
			self.movetoButton.Enabled = False
		else:
			self.movetoButton.Enabled = True
		self.deleteButton.Enabled = True
		self.editButton.Enabled = True


	def OnEdit(self, evt):
		sel = self.ruleList.Selection
		marker = self.ruleList.GetClientData(sel)
		if isinstance(marker, ruleHandler.MarkerQuery):
			query = marker
		else:
			query = marker.markerQuery
		context = self.context.copy()  # Shallow copy
		context["rule"] = query
		if ruleHandler.showEditor(context):
			# Pass the eventually changed rule name
			self.RefreshRuleList(context["data"]["rule"]["name"])
			self.ruleList.SetFocus()


	def OnDisplayActiveRules(self, evt):
		# api.processPendingEvents()
		self.RefreshRuleList()
		# import time
		# time.sleep(0.4)
		self.ruleList.SetFocus()


	def onElementTypeChange(self, evt):
		elementType=evt.GetInt()
		# We need to make sure this gets executed after the focus event.
		# Otherwise, NVDA doesn't seem to get the event.
		queueHandler.queueFunction(queueHandler.eventQueue, self.initElementType, self.ELEMENT_TYPES[elementType][0])
		self.lastSelectedElementType=elementType


	def initElementType(self, elType):
		print("init")
		# if elType in ("link","button"):
		# 	# Links and buttons can be activated.
		# 	self.activateButton.Enable()
		# 	self.SetAffirmativeId(self.activateButton.GetId())
		# else:
		# 	# No other element type can be activated.
		# 	self.activateButton.Disable()
		# 	self.SetAffirmativeId(self.moveButton.GetId())

		# # Gather the elements of this type.
		# self._elements = []
		# self._initialElement = None

		# parentElements = []
		# isAfterSelection=False
		# for item in self.document._iterNodesByType(elType):
		# 	# Find the parent element, if any.
		# 	for parent in reversed(parentElements):
		# 		if item.isChild(parent.item):
		# 			break
		# 		else:
		# 			# We're not a child of this parent, so this parent has no more children and can be removed from the stack.
		# 			parentElements.pop()
		# 	else:
		# 		# No parent found, so we're at the root.
		# 		# Note that parentElements will be empty at this point, as all parents are no longer relevant and have thus been removed from the stack.
		# 		parent = None

		# 	element=self.Element(item,parent)
		# 	self._elements.append(element)

		# 	if not isAfterSelection:
		# 		isAfterSelection=item.isAfterSelection
		# 		if not isAfterSelection:
		# 			# The element immediately preceding or overlapping the caret should be the initially selected element.
		# 			# Since we have not yet passed the selection, use this as the initial element. 
		# 			try:
		# 				self._initialElement = self._elements[-1]
		# 			except IndexError:
		# 				# No previous element.
		# 				pass

		# 	# This could be the parent of a subsequent element, so add it to the parents stack.
		# 	parentElements.append(element)

		# # Start with no filtering.
		# self.filterEdit.ChangeValue("")
		# self.filter("", newElementType=True)


	def onFilterEditTextChange(self, evt):
		self.filter(self.filterEdit.GetValue())
		evt.Skip()


	def filter(self, filterText, newElementType=False):
		print("filter")
		# # If this is a new element type, use the element nearest the cursor.
		# # Otherwise, use the currently selected element.
		# # #8753: wxPython 4 returns "invalid tree item" when the tree view is empty, so use initial element if appropriate.
		# try:
		# 	defaultElement = self._initialElement if newElementType else self.tree.GetItemData(self.tree.GetSelection())
		# except:
		# 	defaultElement = self._initialElement
		# # Clear the tree.
		# self.tree.DeleteChildren(self.treeRoot)

		# # Populate the tree with elements matching the filter text.
		# elementsToTreeItems = {}
		# defaultItem = None
		# matched = False
		# #Do case-insensitive matching by lowering both filterText and each element's text.
		# filterText=filterText.lower()
		# for element in self._elements:
		# 	label=element.item.label
		# 	if filterText and filterText not in label.lower():
		# 		continue
		# 	matched = True
		# 	parent = element.parent
		# 	if parent:
		# 		parent = elementsToTreeItems.get(parent)
		# 	item = self.tree.AppendItem(parent or self.treeRoot, label)
		# 	self.tree.SetItemData(item, element)
		# 	elementsToTreeItems[element] = item
		# 	if element == defaultElement:
		# 		defaultItem = item

		# self.tree.ExpandAll()

		# if not matched:
		# 	# No items, so disable the buttons.
		# 	self.activateButton.Disable()
		# 	self.moveButton.Disable()
		# 	return

		# # If there's no default item, use the first item in the tree.
		# self.tree.SelectItem(defaultItem or self.tree.GetFirstChild(self.treeRoot)[0])
		# # Enable the button(s).
		# # If the activate button isn't the default button, it is disabled for this element type and shouldn't be enabled here.
		# if self.AffirmativeId == self.activateButton.Id:
		# 	self.activateButton.Enable()
		# self.moveButton.Enable()


	def ShowModal(self, context):
		self.InitData(context)
		self.Fit()
		self.Center(wx.BOTH | wx.CENTER_ON_SCREEN)
		self.ruleList.SetFocus()
		return super(Dialog, self).ShowModal()
