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


class TreeRule:
	def __init__(self, displayName, data, treeid):
		self.displayName = displayName
		self.data = data
		self.treeid = treeid
	
	def __repr__(self):
		return repr((self.name, self.treeid))

class Dialog(wx.Dialog):

	_instance = None
	GROUP_BY = (
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

		self.radioButtons = wx.RadioBox(self, label=_("&Group by: "), choices=tuple(et[1] for et in self.GROUP_BY))
		self.radioButtons.SetSelection(0)
		self.radioButtons.Bind(wx.EVT_RADIOBOX, self.OnRadioButtonChange)
		contentsSizer.Add(self.radioButtons, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		filtersSizer = wx.GridSizer(1, 2, 10, 10)

		filterText = _("&Filter by:")
		labelledCtrl = gui.guiHelper.LabeledControlHelper(self, filterText, wx.TextCtrl)
		self.filterEdit = labelledCtrl.control
		self.filterEdit.Bind(wx.EVT_TEXT, self.RefreshRuleList)
		filtersSizer.Add(labelledCtrl.sizer)

		self.displayActiveRules = wx.CheckBox(self, label=_("Display only &active rules"))
		self.displayActiveRules.Value = False
		self.displayActiveRules.Bind(wx.EVT_CHECKBOX, self.RefreshRuleList)
		filtersSizer.Add(self.displayActiveRules)

		contentsSizer.Add(filtersSizer, flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		self.ruleTree = wx.TreeCtrl(self, size=wx.Size(700, 600), style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_LINES_AT_ROOT)
		self.ruleTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnRuleListChoice)
		self.ruleTreeRoot = self.ruleTree.AddRoot("root")
		contentsSizer.Add(self.ruleTree,flag=wx.EXPAND)
		contentsSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_VERTICAL_DIALOG_ITEMS)

		ruleCommentLabel = wx.StaticText(self, label=_("Description"))
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


	def InitData(self, context):
		self.context = context
		self.markerManager = context["webModule"].markerManager
		self.rule = context["rule"]
		self.RefreshRuleList()
	

	def GetRules(self):
		self.treeRuleList = []
		for query in self.markerManager.getQueries():
			self.treeRuleList.append(TreeRule(query.getDisplayString(), query, None))


	def RefreshRuleList(self, selectName = None):
		api.processPendingEvents()
		currentGroupBy = self.GROUP_BY[self.radioButtons.GetSelection()][0]
		filterText = self.filterEdit.GetValue()
		self.GetRules()
		self.ruleTree.DeleteChildren(self.ruleTreeRoot)

		# NAME GROUP BY
		if currentGroupBy == 'Name':
			sortedTreeRuleList = sorted(self.treeRuleList, key=lambda rule: rule.displayName.lower())
			for rule in sortedTreeRuleList:
				if not self.displayActiveRules.Value or rule.data.getResults():
					if not filterText or filterText in rule.displayName:
						rule.treeid = self.ruleTree.AppendItem(self.ruleTreeRoot, rule.displayName)

		# GESTURES GROUP BY
		elif currentGroupBy == 'Gestures':
			gesturesDic = {}
			noGesturesList = []
			for rule in self.treeRuleList:
				if not self.displayActiveRules.Value or rule.data.getResults():
					if not filterText or filterText in rule.data.name:
						if len(rule.data.gestures):
							for gesture in rule.data.gestures:
								if gesturesDic.get(gesture):
									gesturesDic[gesture].append(rule)
								else:
									gesturesDic[gesture] = [rule]
						else:
							noGesturesList.append(rule)

			for gestureKey in gesturesDic.keys():
				gestureTreeId = self.ruleTree.AppendItem(self.ruleTreeRoot, inputCore.getDisplayTextForGestureIdentifier(gestureKey)[1])
				for rule in gesturesDic[gestureKey]:
					displayName = [rule.data.name, " - ", rule.data.gestures[gestureKey]]
					rule.treeid = self.ruleTree.AppendItem(gestureTreeId, ''.join(displayName))

			noGestureTreeId = self.ruleTree.AppendItem(self.ruleTreeRoot, 'none')
			for rule in noGesturesList:
				rule.treeid = self.ruleTree.AppendItem(noGestureTreeId, rule.data.name)

		self.ruleTree.ExpandAllChildren(self.ruleTreeRoot)
		if selectName:
			self.ruleTree.SelectItem([x.treeid for x in self.treeRuleList if x.data.name == selectName][0])
		elif self.rule:
			self.ruleTree.SelectItem([x.treeid for x in self.treeRuleList if x.data.name == self.rule.name][0])


	def OnMoveto(self, evt):
		sel = self.ruleTree.Selection
		rule = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		if not rule.getResults():
			wx.Bell()
			return
		rule.script_moveto(None)
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
		rule = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		self.markerManager.removeQuery(rule)
		webModuleHandler.update(
			webModule=self.context["webModule"],
			focus=self.context["focusObject"]
			)
		self.RefreshRuleList()
		self.ruleTree.SetFocus()

	def OnRuleListChoice(self, evt):
		if evt.EventObject is None or evt.EventObject.IsBeingDeleted():
			return
		matchingRules = [x.data for x in self.treeRuleList if x.treeid == self.ruleTree.Selection]
		if not len(matchingRules):
			self.movetoButton.Enabled = False
			self.deleteButton.Enabled = False
			self.editButton.Enabled = False
			return
		rule = matchingRules[0]
		if rule.getResults():
			self.movetoButton.Enabled = True
		else:
			self.movetoButton.Enabled = False
		
		if rule.comment:
			self.ruleComment.SetValue(rule.comment)
		else:
			self.ruleComment.SetValue('')
		self.deleteButton.Enabled = True
		self.editButton.Enabled = True

	def OnEdit(self, evt):
		sel = self.ruleTree.Selection
		rule = [x.data for x in self.treeRuleList if x.treeid == sel][0]
		context = self.context.copy()  # Shallow copy
		context["rule"] = rule
		if ruleHandler.showEditor(context):
			# Pass the eventually changed rule name
			self.RefreshRuleList(context["data"]["rule"]["name"])
			self.ruleTree.SetFocus()

	def OnRadioButtonChange(self, evt):
		self.RefreshRuleList()

	def ShowModal(self, context):
		self.InitData(context)
		self.Fit()
		self.Center(wx.BOTH | wx.CENTER_ON_SCREEN)
		self.ruleTree.SetFocus()
		return super(Dialog, self).ShowModal()
