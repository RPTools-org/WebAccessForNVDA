# -*- coding: utf-8 -*-

import wx

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


class GeneralPanel(SettingsPanel):
	# Translators: This is the label for the general settings panel.
	title = _("General")

	def makeSettings(self, settingsSizer):
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		settingsSizer.Add(mainSizer, flag=wx.EXPAND, proportion=1)

		# gridBagSizer = wx.GridBagSizer(vgap=10, hgap=10)
		# gridBagSizer.AddGrowableRow(0)
		# gridBagSizer.AddGrowableRow(1)
		# mainSizer.Add(gridBagSizer, flag=wx.EXPAND, proportion=1)

		# # Type
		# typeChoices = []
		# for key, label in ruleTypes.ruleTypeLabels.items():
		# 	typeChoices.append(label)
		# ruleTypeLabel = wx.StaticText(self, label=_("Rule &type"))
		# self.ruleType = wx.Choice(self, choices=typeChoices)
		
		# # Name
		# ruleNameLabel = wx.StaticText(self, label=_("Rule &name"))
		# self.ruleName = wx.TextCtrl(self)

		# # User documentation
		# userDocLabel = wx.StaticText(self, label=_("User &documentation"))
		# self.ruleDocumentation = wx.TextCtrl(self, size=(300, 200), style=wx.TE_MULTILINE)

		# # Summary
		# summaryLabel = wx.StaticText(self, label=_("&Summary"))
		# self.ruleSummary = wx.TextCtrl(self, size=(200, 100), style=wx.TE_MULTILINE | wx.TE_READONLY)

		# gridBagSizer.Add(ruleTypeLabel, pos=(0,0))
		# gridBagSizer.Add(self.ruleType, pos=(0,1), flag=wx.EXPAND)
		# gridBagSizer.Add(ruleNameLabel, pos=(1,0))
		# gridBagSizer.Add(self.ruleName, pos=(1,1), flag=wx.EXPAND)
		# gridBagSizer.Add(userDocLabel, pos=(2,0), span=(1,2))
		# gridBagSizer.Add(self.ruleDocumentation, pos=(3,0), span=(1,2), flag=wx.EXPAND)

		# staticLine = wx.StaticLine(self, style=wx.LI_VERTICAL)
		# gridBagSizer.Add(staticLine, pos=(0,2), span=(4,1), flag=wx.EXPAND)

		# gridBagSizer.Add(summaryLabel, pos=(0,3))
		# gridBagSizer.Add(self.ruleSummary, pos=(1,3), span=(3,1), flag=wx.EXPAND)

		self.initData()


	def initData(self):
		self.isValidData = True

		# if newRule:
		# 	self.ruleType.SetSelection(-1)
		# 	self.ruleName.Value = ""
		# 	self.ruleDocumentation.Value = ""
		# 	self.ruleSummary.Value = ""

		# else:
		# 	for index, key in enumerate(ruleTypes.ruleTypeLabels.keys()):
		# 		if key == globalRule["type"]:
		# 			self.ruleType.SetSelection(index)
		# 			break
		# 	self.ruleName.Value = globalRule["name"]
		# 	self.ruleDocumentation.Value = globalRule["comment"]
		# # todo: Init summary

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


class CriteriaSetEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess settings dialog.
	title = _("WebAccess Criteria set editor")
	categoryClasses = [GeneralPanel]
	INITIAL_SIZE = (800, 480)
	MIN_SIZE = (470, 240)


	def __init__(self, parent, initialCategory=None, rule=None):
		self.initialCategory = initialCategory
		self.currentCategory = None
		self.setPostInitFocus = None
		self.catIdToInstanceMap = {}
		self.initData(rule)
		super(MultiCategorySettingsDialog, self).__init__(parent)

		self.SetMinSize(self.scaleSize(self.MIN_SIZE))
		self.SetSize(self.scaleSize(self.INITIAL_SIZE))
		self.CentreOnScreen()


	def initData(self, rule):
		print("INIT")
		# global globalRule
		# global newRule

		# self.context = context
		# self.rule = context.get("rule")
		# self.markerManager = context["webModule"].markerManager

		# if context.get("rule"):
		# 	newRule = False
		# 	globalRule = context.get("rule").getData().copy()
		# else:
		# 	globalRule = OrderedDict()

		# if not self.rule and self.markerManager.nodeManager:
		# 	node = self.markerManager.nodeManager.getCaretNode()
		# 	while node is not None:
		# 		if node.role in formModeRoles:
		# 			globalRule["formMode"] = True
		# 			break
		# 		node = node.parent

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

		# for rule in self.markerManager.getQueries():
		# 	if globalRule["name"] == rule.name and newRule:
		# 		gui.messageBox(
		# 			message=_("There already is another rule with the same name."),
		# 			caption=_("Error"),
		# 			style=wx.ICON_ERROR | wx.OK | wx.CANCEL,
		# 			parent=self
		# 		)
		# 		return

		# if not newRule:
		# 	self.markerManager.removeQuery(self.rule)
		# savedRule = ruleHandler.VirtualMarkerQuery(self.markerManager, globalRule)
		# self.markerManager.addQuery(savedRule)
		# webModuleHandler.update(
		# 	webModule=self.context["webModule"],
		# 	focus=self.context["focusObject"]
		# )

		for panel in self.catIdToInstanceMap.values():
			panel.Destroy()
		super(MultiCategorySettingsDialog, self).onOk(evt)

	def Destroy(self):
		super(CriteriaSetEditorDialog, self).Destroy()
