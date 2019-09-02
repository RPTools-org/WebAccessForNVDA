# -*- coding: utf-8 -*-

import wx

import gui
from collections import OrderedDict
from logHandler import log

from .. import ruleHandler
from ..ruleHandler import ruleTypes
import controlTypes
from .. import webModuleHandler

try:
	from gui import guiHelper
except ImportError:
	from ..backports.nvda_2016_4 import gui_guiHelper as guiHelper

try:
	from gui.settingsDialogs import (
		MultiCategorySettingsDialog,
		SettingsPanel
	)
except ImportError:
	from ..backports.nvda_2018_2.gui_settingsDialogs import (
		MultiCategorySettingsDialog,
		SettingsPanel
	)

formModeRoles = [
	controlTypes.ROLE_EDITABLETEXT,
	controlTypes.ROLE_COMBOBOX,
]

globalRule = None
newRule = True


class CriteriaPanel(SettingsPanel):
	# Translators: This is the label for the criteria sets settings panel.
	title = _("Criteria sets")

	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)

		mainGridSizer = wx.FlexGridSizer(rows=4, cols=2, hgap=10, vgap=5)
		mainSizer.Add(mainGridSizer)

		# Criteria sets
		criteriaSetsLabel = wx.StaticText(self, label=_("&Criteria sets"))
		self.criteriaSetsList = wx.ListBox(self)

		# Criteria summary
		criteriaSummaryLabel = wx.StaticText(self, label=_("Criteria &summary"))
		self.criteriaSummary = wx.TextCtrl(self, size=(220, 100), style=wx.TE_MULTILINE | wx.TE_READONLY)

		# Buttons
		newButton = wx.Button(self, label=_("&New"))
		newButton.Bind(wx.EVT_BUTTON, self.onCriteriaBtn)
		editButton = wx.Button(self, label=_("&Edit"))
		editButton.Bind(wx.EVT_BUTTON, self.onCriteriaBtn)
		deleteButton = wx.Button(self, label=_("&Delete"))
		deleteButton.Bind(wx.EVT_BUTTON, self.onCriteriaBtn)

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer.AddMany((
			newButton,
			(5,5),
			editButton,
			(5,5),
			deleteButton
		))

		mainGridSizer.Add(criteriaSetsLabel)
		mainGridSizer.Add(criteriaSummaryLabel)
		mainGridSizer.Add(self.criteriaSetsList, flag=wx.EXPAND)
		mainGridSizer.Add(self.criteriaSummary, flag=wx.EXPAND)
		mainGridSizer.AddSpacer(5)
		mainGridSizer.AddSpacer(5)
		mainGridSizer.Add(buttonSizer)

		self.initData()

	def initData(self):
		self.isValidData = True

		if newRule:
			self.criteriaSetsList.Clear()
			self.criteriaSummary.Value = ""
			self.criteriaSetsList.InsertItems(["Mon super critere"], 0) #todo:

		# else:
		# 	for index, key in enumerate(ruleTypes.ruleTypeLabels.keys()):
		# 		if key == globalRule["type"]:
		# 			self.ruleType.SetSelection(index)
		# 			break
		# 	self.ruleName.Value = globalRule["name"]
		# 	self.ruleDocumentation.Value = globalRule["comment"]
		# todo: populate if given

	def onCriteriaBtn(self, evt):
		from ..gui import criteriaSetEditor
		gui.mainFrame.prePopup()
		criteriaSetEditor.CriteriaSetEditorDialog(gui.mainFrame, rule=globalRule).Show()
		gui.mainFrame.postPopup()
		# with RuleCriteriaEditor(self) as dlg:
		# 	if dlg.ShowModal(self.context) == wx.ID_OK:
		# 		self.refreshCriteria()

	def isValid(self):
		return self.isValidData
	
	def onSave(self):
		self.isValidData = True

		# # Type is required
		# if not self.ruleType.Selection >= 0:
		# 	gui.messageBox(
		# 		message=_("You must choose a type for this rule"),
		# 		caption=_("Error"),
		# 		style=wx.OK | wx.ICON_ERROR,
		# 		parent=self
		# 	)
		# 	self.isValidData = False
		# 	self.ruleType.SetFocus()
		# 	return
		# else:
		# 	globalRule["type"] = ruleTypes.ruleTypeLabels.keys()[self.ruleType.Selection]

		# # Name is required
		# if not self.ruleName.Value.strip():
		# 	gui.messageBox(
		# 		message=_("You must choose a name for this rule"),
		# 		caption=_("Error"),
		# 		style=wx.OK | wx.ICON_ERROR,
		# 		parent=self
		# 	)
		# 	self.isValidData = False
		# 	self.ruleName.SetFocus()
		# 	return
		# else:
		# 	globalRule["name"] = self.ruleName.Value
		
		# globalRule["comment"] = self.ruleDocumentation.Value


class GeneralPanel(SettingsPanel):
	# Translators: This is the label for the general settings panel.
	title = _("General")

	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)

		gridBagSizer = wx.GridBagSizer(vgap=5, hgap=10)
		gridBagSizer.AddGrowableRow(0)
		gridBagSizer.AddGrowableRow(1)
		mainSizer.Add(gridBagSizer, flag=wx.EXPAND, proportion=1)

		# Type
		typeChoices = []
		for key, label in ruleTypes.ruleTypeLabels.items():
			typeChoices.append(label)
		ruleTypeLabel = wx.StaticText(self, label=_("Rule &type"))
		self.ruleType = wx.Choice(self, choices=typeChoices)
		
		# Name
		ruleNameLabel = wx.StaticText(self, label=_("Rule &name"))
		self.ruleName = wx.TextCtrl(self)

		# User documentation
		userDocLabel = wx.StaticText(self, label=_("User &documentation"))
		self.ruleDocumentation = wx.TextCtrl(self, size=(400, 100), style=wx.TE_MULTILINE)

		# Summary
		summaryLabel = wx.StaticText(self, label=_("&Summary"))
		self.ruleSummary = wx.TextCtrl(self, size=(400, 100), style=wx.TE_MULTILINE | wx.TE_READONLY)

		gridBagSizer.Add(ruleTypeLabel, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL)
		gridBagSizer.Add(self.ruleType, pos=(0,1), flag=wx.EXPAND)

		gridBagSizer.Add(5, 5, pos=(1,0), span=(1,2))
		gridBagSizer.Add(ruleNameLabel, pos=(2,0), flag=wx.ALIGN_CENTER_VERTICAL)
		gridBagSizer.Add(self.ruleName, pos=(2,1), flag=wx.EXPAND)

		gridBagSizer.Add(5, 5, pos=(3,0), span=(1,2))
		gridBagSizer.Add(userDocLabel, pos=(4,0), span=(1,2))
		gridBagSizer.Add(self.ruleDocumentation, pos=(5,0), span=(1,2), flag=wx.EXPAND)

		staticLine = wx.StaticLine(self)
		gridBagSizer.Add(5, 5, pos=(6,0), span=(1,2))
		gridBagSizer.Add(staticLine, pos=(7,0), span=(1,2), flag=wx.EXPAND)

		gridBagSizer.Add(5, 5, pos=(8,0), span=(1,2))
		gridBagSizer.Add(summaryLabel, pos=(9,0))
		gridBagSizer.Add(self.ruleSummary, pos=(10,0), span=(1,2), flag=wx.EXPAND)

		self.initData()


	def initData(self):
		self.isValidData = True

		if newRule:
			self.ruleType.SetSelection(-1)
			self.ruleName.Value = ""
			self.ruleDocumentation.Value = ""
			self.ruleSummary.Value = ""

		else:
			for index, key in enumerate(ruleTypes.ruleTypeLabels.keys()):
				if key == globalRule["type"]:
					self.ruleType.SetSelection(index)
					break
			self.ruleName.Value = globalRule["name"]
			self.ruleDocumentation.Value = globalRule["comment"]
		# todo: Init summary

	def isValid(self):
		return self.isValidData
	
	def onSave(self):
		self.isValidData = True

		# Type is required
		if not self.ruleType.Selection >= 0:
			gui.messageBox(
				message=_("You must choose a type for this rule"),
				caption=_("Error"),
				style=wx.OK | wx.ICON_ERROR,
				parent=self
			)
			self.isValidData = False
			self.ruleType.SetFocus()
			return
		else:
			globalRule["type"] = ruleTypes.ruleTypeLabels.keys()[self.ruleType.Selection]

		# Name is required
		if not self.ruleName.Value.strip():
			gui.messageBox(
				message=_("You must choose a name for this rule"),
				caption=_("Error"),
				style=wx.OK | wx.ICON_ERROR,
				parent=self
			)
			self.isValidData = False
			self.ruleName.SetFocus()
			return
		else:
			globalRule["name"] = self.ruleName.Value
		
		globalRule["comment"] = self.ruleDocumentation.Value


class RuleEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess settings dialog.
	title = _("WebAccess Rule editor")
	categoryClasses = [GeneralPanel, CriteriaPanel]
	INITIAL_SIZE = (750, 520)
	MIN_SIZE = (470, 240)


	def __init__(self, parent, initialCategory=None, context=None):
		self.initialCategory = initialCategory
		self.currentCategory = None
		self.setPostInitFocus = None
		self.catIdToInstanceMap = {}
		self.initData(context)
		super(MultiCategorySettingsDialog, self).__init__(parent, resizeable=True)

		self.SetMinSize(self.scaleSize(self.MIN_SIZE))
		self.SetSize(self.scaleSize(self.INITIAL_SIZE))
		self.CentreOnScreen()


	def initData(self, context):
		global globalRule
		global newRule

		self.context = context
		self.rule = context.get("rule")
		self.markerManager = context["webModule"].markerManager

		if context.get("rule"):
			newRule = False
			globalRule = context.get("rule").getData().copy()
		else:
			globalRule = OrderedDict()

		if not self.rule and self.markerManager.nodeManager:
			node = self.markerManager.nodeManager.getCaretNode()
			while node is not None:
				if node.role in formModeRoles:
					globalRule["formMode"] = True
					break
				node = node.parent

	def _doSave(self):
		for panel in self.catIdToInstanceMap.values():
			panel.onSave()
			if panel.isValid() is False:
				raise ValueError("Validation for %s blocked saving settings" % panel.__class__.__name__)

	def onOk(self, evt):
		try:
			self._doSave()
		except ValueError:
			log.debugWarning("", exc_info=True)
			return

		for rule in self.markerManager.getQueries():
			if globalRule["name"] == rule.name and newRule:
				gui.messageBox(
					message=_("There already is another rule with the same name."),
					caption=_("Error"),
					style=wx.ICON_ERROR | wx.OK | wx.CANCEL,
					parent=self
				)
				return

		if not newRule:
			self.markerManager.removeQuery(self.rule)
		savedRule = ruleHandler.VirtualMarkerQuery(self.markerManager, globalRule)
		self.markerManager.addQuery(savedRule)
		webModuleHandler.update(
			webModule=self.context["webModule"],
			focus=self.context["focusObject"]
		)

		for panel in self.catIdToInstanceMap.values():
			panel.Destroy()
		super(MultiCategorySettingsDialog, self).onOk(evt)

	def Destroy(self):
		super(RuleEditorDialog, self).Destroy()
