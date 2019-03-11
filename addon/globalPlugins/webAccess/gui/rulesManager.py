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


class TreeQuery:
	def __init__(self, name, data, treeid):
		self.name = name
		self.data = data
		self.treeid = treeid
	
	def __repr__(self):
		return repr((self.name, self.treeid))


class Dialog(wx.Dialog):

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
		radioButtons.SetSelection(0)
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

		self.ruleTree = wx.TreeCtrl(self, size=wx.Size(500, 600), style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT)
		self.ruleTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnRuleListChoice)
		self.ruleTreeRoot = self.ruleTree.AddRoot("root")
		contentsSizer.Add(self.ruleTree,flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		ruleCommentLabel = wx.StaticText(self, label="Description")
		contentsSizer.Add(ruleCommentLabel, flag=wx.EXPAND)
		self.ruleComment = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NO_VSCROLL)
		contentsSizer.Add(self.ruleComment, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		bHelper = gui.guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.movetoButton = bHelper.addButton(self, label=_("Move to"))
		self.movetoButton.Bind(wx.EVT_BUTTON, self.OnMoveto)
		self.AffirmativeId = self.movetoButton.Id
		self.movetoButton.SetDefault()

		self.newButton = bHelper.addButton(self, label=_("&New rule..."))
		self.newButton.Bind(wx.EVT_BUTTON, self.OnNew)

		self.editButton = bHelper.addButton(self, label=_("&Edit..."))
		self.editButton.Bind(wx.EVT_BUTTON, self.OnEdit)
		self.editButton.Enabled = False

		self.deleteButton = bHelper.addButton(self, label=_("&Delete"))
		self.deleteButton.Bind(wx.EVT_BUTTON, self.OnDelete)
		self.deleteButton.Enabled = False

		contentsSizer.Add(bHelper.sizer, flag=wx.ALIGN_RIGHT)
		mainSizer.Add(contentsSizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND)
		mainSizer.Add(self.CreateSeparatedButtonSizer(wx.CLOSE), flag=wx.EXPAND)
		mainSizer.Fit(self)
		self.Sizer = mainSizer

		self.CentreOnScreen()


	def __del__(self):
		Dialog._instance = None


	def InitData(self, context):
		self.context = context
		webModule = context["webModule"]
		self.markerManager = webModule.markerManager
		self.rule = context["rule"]
		self.RefreshRuleList()


	def RefreshRuleList(self, selectName=None, elType=ELEMENT_TYPES[0]):
		api.processPendingEvents()
		"""
		Refresh the list of rules.
		
		If *selectName" is set, the rule with that name gets selected.
		Otherwise, the rule matching the current focus in the document (self.rule),
		if any, gets selected.
		"""
		self.treeRuleList = []
		sortedTreeRuleList = []
		self.ruleTree.DeleteChildren(self.ruleTreeRoot)

		# TRI PAR NOM
		if elType[0] == 'Name':
			for result in self.markerManager.getResults():
				self.treeRuleList.append(TreeQuery(self.GetRuleName(result, result.markerQuery.gestures), result, None))

			if not self.displayActiveRules.Value:
				for query in self.markerManager.getQueries():
					if query not in [x.markerQuery for x in self.markerManager.getResults()]:
						self.treeRuleList.append(TreeQuery(self.GetRuleName(query, query.gestures), query, None))
				
			sortedTreeRuleList = sorted(self.treeRuleList, key=lambda rule: rule.name)

			for rule in sortedTreeRuleList:
				rule.treeid = self.ruleTree.AppendItem(self.ruleTreeRoot, rule.name)

			if selectName:
				self.ruleTree.SelectItem([x.treeid for x in self.treeRuleList if x.data.name == selectName][0])
			elif self.rule:
				self.ruleTree.SelectItem([x.treeid for x in self.treeRuleList if x.data.name == self.rule.name][0])

		elif elType[0] == 'Gestures':
			gesturesDic = {}
			for result in self.markerManager.getResults():
				for gesture in result.markerQuery.gestures:
					if gesturesDic.get(gesture):
						gesturesDic[gesture].append(result)
					else:
						gesturesDic[gesture] = [result]
			
			if not self.displayActiveRules.Value:
				for query in self.markerManager.getQueries():
						if query not in [x.markerQuery for x in self.markerManager.getResults()]:
							for gesture in query.gestures:
								if gesturesDic.get(gesture):
									gesturesDic[gesture].append(query)
								else:
									gesturesDic[gesture] = [query]

			for gestureKey in gesturesDic.keys():
				gestureTreeId = self.ruleTree.AppendItem(self.ruleTreeRoot, gestureKey)
				for rule in gesturesDic[gestureKey]:
					ruleId = self.ruleTree.AppendItem(gestureTreeId, rule.name)
					self.treeRuleList.append(TreeQuery(rule.name, rule, ruleId))


	def GetRuleName(self, rule, gestures):
		ruleName = rule.name
		gesturesKeys = gestures.keys()

		if len(gesturesKeys):
			if len(gesturesKeys) >= 1:
				ruleName += " - "
				ruleName += gestures[gesturesKeys[0]]
			else:
				for gestureKey in gesturesKeys:
					ruleName += " - "
					ruleName += gestures[gestureKey]
		return ruleName


	def OnMoveto(self, evt):
		sel = self.ruleTree.Selection
		result = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		if not isinstance(result, ruleHandler.MarkerResult):
			wx.Bell()
			return
		result.script_moveto(None)
		self.Close()


	def OnNew(self, evt):
		context = self.context.copy()  # Shallow copy
		if ruleHandler.showCreator(context):
			self.RefreshRuleList(context["data"]["rule"]["name"])
			self.ruleTree.SetFocus()


	def OnDelete(self, evt):
		if gui.messageBox(
			_("Are you sure you want to delete this rule?"),
			_("Confirm Deletion"),
			wx.YES | wx.NO | wx.ICON_QUESTION, self
		) == wx.NO:
			return
		sel = self.ruleTree.Selection
		result = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		if isinstance(result, ruleHandler.MarkerQuery):
			query = result
		else:
			query = result.markerQuery
		self.markerManager.removeQuery(query)
		webModuleHandler.update(
			webModule=self.context["webModule"],
			focus=self.context["focusObject"]
			)
		self.RefreshRuleList()
		self.ruleTree.SetFocus()


	def OnRuleListChoice(self, evt):
		sel = self.ruleTree.Selection
		if sel < 0:
			self.movetoButton.Enabled = False
			self.deleteButton.Enabled = False
			self.editButton.Enabled = False
			return
		result = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		if isinstance(result, ruleHandler.MarkerResult):
			self.movetoButton.Enabled = True
		else:
			self.movetoButton.Enabled = False
		self.deleteButton.Enabled = True
		self.editButton.Enabled = True


	def OnEdit(self, evt):
		sel = self.ruleTree.Selection
		result = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		if isinstance(result, ruleHandler.MarkerQuery):
			query = result
		else:
			query = result.markerQuery
		context = self.context.copy()  # Shallow copy
		context["rule"] = query
		if ruleHandler.showEditor(context):
			# Pass the eventually changed rule name
			self.RefreshRuleList(context["data"]["rule"]["name"])
			self.ruleTree.SetFocus()


	def OnDisplayActiveRules(self, evt):
		self.RefreshRuleList()
		self.ruleTree.SetFocus()


	def onElementTypeChange(self, evt):
		self.RefreshRuleList(elType=self.ELEMENT_TYPES[evt.GetInt()])
		# We need to make sure this gets executed after the focus event.
		# Otherwise, NVDA doesn't seem to get the event.
		# queueHandler.queueFunction(queueHandler.eventQueue, self.initElementType, self.ELEMENT_TYPES[elementType][0])
		# self.lastSelectedElementType=elementType


	def onFilterEditTextChange(self, evt):
		self.filter(self.filterEdit.GetValue())
		evt.Skip()


	def filter(self, filterText, newElementType=False):
		print("filter")
		# # If this is a new element type, use the element nearest the cursor.
		# # Otherwise, use the currently selected element.
		# # #8753: wxPython 4 returns "invalid tree item" when the tree view is empty, so use initial element if appropriate.
		# try:
		# 	defaultElement = self._initialElement if newElementType else self.ruleTree.GetItemData(self.ruleTree.GetSelection())
		# except:
		# 	defaultElement = self._initialElement
		# # Clear the tree.
		# self.ruleTree.DeleteChildren(self.treeRoot)

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
		# 	item = self.ruleTree.AppendItem(parent or self.treeRoot, label)
		# 	self.ruleTree.SetItemData(item, element)
		# 	elementsToTreeItems[element] = item
		# 	if element == defaultElement:
		# 		defaultItem = item

		# self.ruleTree.ExpandAll()

		# if not matched:
		# 	# No items, so disable the buttons.
		# 	self.activateButton.Disable()
		# 	self.moveButton.Disable()
		# 	return

		# # If there's no default item, use the first item in the tree.
		# self.ruleTree.SelectItem(defaultItem or self.ruleTree.GetFirstChild(self.treeRoot)[0])
		# # Enable the button(s).
		# # If the activate button isn't the default button, it is disabled for this element type and shouldn't be enabled here.
		# if self.AffirmativeId == self.activateButton.Id:
		# 	self.activateButton.Enable()
		# self.moveButton.Enable()


	def ShowModal(self, context):
		self.InitData(context)
		self.Fit()
		self.Center(wx.BOTH | wx.CENTER_ON_SCREEN)
		self.ruleTree.SetFocus()
		return super(Dialog, self).ShowModal()
