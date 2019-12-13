# globalPlugins/webAccess/gui/ruleEditor.py
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

# Get ready for Python 3
from __future__ import absolute_import, division, print_function

__version__ = "2019.12.12"
__author__ = u"Shirley Noël <shirley.noel@pole-emploi.fr>"


from collections import OrderedDict
import wx

import controlTypes
import gui
import inputCore
from logHandler import log

from .. import ruleHandler
from ..ruleHandler import ruleTypes
from .. import webModuleHandler

from ..ruleHandler.controlMutation import (
	MUTATIONS_BY_RULE_TYPE,
	mutationLabels
)

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
	
def setIfNotEmpty(dic, key, value):
	if value and value.strip():
		dic[key] = value
		return
	elif dic.get(key):
		del dic[key]

formModeRoles = [
	controlTypes.ROLE_EDITABLETEXT,
	controlTypes.ROLE_COMBOBOX,
]

globalContext = None
globalRule = None
newRule = True

class ActionsPanel(SettingsPanel):
	# Translators: This is the label for the rule dialog's action panel.
	title = _("Actions")
	
	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		
		# Translators: Text showed when the selected type doesn't have actions available
		self.noActionsTxt = wx.StaticText(self, label=_("No actions available for the selected rule type."))
		mainSizer.Add(self.noActionsTxt)
		
		self.mainGridSizer = wx.GridBagSizer(vgap=5, hgap=10)
		mainSizer.Add(self.mainGridSizer)
		
		# Translators: Keyboard shortcut input label for the rule dialog's action panel.
		gesturesLabel = wx.StaticText(self, label=_("&Keyboard shortcut"))
		self.gesturesList = wx.ListBox(self)

		# Translators: Add a keyboard shortcut button label for the rule dialog's action panel.
		self.addButton = wx.Button(self, label=_("Add a keyboard shortcut"))
		# Translators: Delete a keyboard shortcut button label for the rule dialog's action panel.
		self.deleteButton = wx.Button(self, label=_("Delete this shortcut"))
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteGesture)

		# Translators: Automatic action at rule detection input label for the rule dialog's action panel.
		actionLabel = wx.StaticText(self, label=_("&Automatic action at rule detection"))
		self.actionList = wx.ComboBox(self, style=wx.CB_READONLY)
		
		self.mainGridSizer.AddMany([
				(gesturesLabel, (0,0), (1,2)),
				(self.gesturesList, (1,0), (2,1), wx.EXPAND),
				(self.addButton, (1,1), (1,1), wx.EXPAND),
				(self.deleteButton, (2,1), (1,1), wx.EXPAND),
				(5,5, (3,0)),
				(actionLabel, (4,0), (1,2)),
				(self.actionList, (5,0), (1,2), wx.EXPAND)
			])
		
		self.initData()
		
	def onAddGesture(self, evt):
		from ..gui import shortcutDialog
		shortcutDialog.markerManager = self.markerManager
		if shortcutDialog.show():
			self.gestureMapValue[shortcutDialog.resultShortcut] = shortcutDialog.resultActionData
			self.updateGesturesList(shortcutDialog.resultShortcut)
			self.gesturesList.SetFocus()
		
	def onDeleteGesture(self, evt):
		gestureIdentifier = self.gesturesList.GetClientData(self.gesturesList.Selection)
		del self.gestureMapValue[gestureIdentifier]
		self.updateGesturesList()
		
	def updateGesturesList(self, newGestureIdentifier=None):
		self.gesturesList.Clear()
		i = 0
		sel = 0
		for gestureIdentifier in self.gestureMapValue:
			gestureSource, gestureMain = inputCore.getDisplayTextForGestureIdentifier(gestureIdentifier)
			actionStr = self.markerManager.getActions()[self.gestureMapValue[gestureIdentifier]]
			self.gesturesList.Append("%s = %s" % (gestureMain, actionStr), gestureIdentifier)
			if gestureIdentifier == newGestureIdentifier:
				sel = i
			i += 1
		if len(self.gestureMapValue) > 0:
			self.gesturesList.SetSelection(sel)
		
		if self.gesturesList.Selection < 0:
			self.deleteButton.Enabled = False
		else:
			self.deleteButton.Enabled = True
		
		self.gesturesList.SetFocus()
		
	def initData(self):
		self.checkVisibility()
		self.markerManager = globalContext["webModule"].markerManager
		self.addButton.Bind(wx.EVT_BUTTON, self.onAddGesture)
		
		actionsDict = self.markerManager.getActions()
		self.actionList.Clear()
		# Translators: No action choice
		self.actionList.Append(pgettext("webAccess.action", "No action"), "")
		for action in actionsDict:
			self.actionList.Append(actionsDict[action], action)
			
		if newRule:
			self.gestureMapValue = {}
			self.actionList.SetSelection(0)
		else:
			self.gestureMapValue = globalRule.get("gestures", {}).copy()
			self.actionList.SetSelection(
				self.markerManager.getActions().keys().index(
					globalRule.get("autoAction", "")
				) + 1  # Empty entry at index 0
				if "autoAction" in globalRule.keys() else 0
			)
		self.updateGesturesList(None)
		
	def checkVisibility(self):
		ruleType = globalRule.get("type")
		if ruleType in (ruleTypes.ZONE, ruleTypes.MARKER):
			self.noActionsTxt.Show(False)
			self.mainGridSizer.ShowItems(True)
		else:
			self.noActionsTxt.Show(True)
			self.mainGridSizer.ShowItems(False)
		
	def onSave(self):
		ruleType = globalRule.get("type")
		if ruleType in (ruleTypes.ZONE, ruleTypes.MARKER):
			globalRule["gestures"] = self.gestureMapValue
			autoAction = self.actionList.GetClientData(self.actionList.Selection)
			setIfNotEmpty(globalRule, "autoAction", autoAction)
		else:
			if globalRule.get("gestures"):
				del globalRule["gestures"]
			if globalRule.get("autoAction"):
				del globalRule["autoAction"]


class PropertiesPanel(SettingsPanel):
	# Translators: This is the label for the rule dialog's properties panel.
	title = _("Properties")
	
	# The semi-column is part of the labels because some localizations
	# (ie. French) require it to be prepended with one space.
	FIELDS = OrderedDict((
		# Translator: Multiple results checkbox label for the rule dialog's properties panel.
		("multiple", pgettext("webAccess.ruleProperties", u"&Multiple results")),
		# Translator: Activate form mode checkbox label for the rule dialog's properties panel.
		("formMode", pgettext("webAccess.ruleProperties", u"Activate &form mode")),
		# Translator: Skip page down checkbox label for the rule dialog's properties panel.
		("skip", pgettext("webAccess.ruleProperties", u"S&kip with Page Down")),
		# Translator: Speak rule name checkbox label for the rule dialog's properties panel.
		("sayName", pgettext("webAccess.ruleProperties", u"&Speak rule name")),
		# Translator: Custom name input label for the rule dialog's properties panel.
		("customName", pgettext("webAccess.ruleProperties", u"Custom &name:")),
		# Label depends on rule type)
		("customValue", None),
		# Translator: Transform select label for the rule dialog's properties panel.
		("mutation", pgettext("webAccess.ruleProperties", u"&Transform:")),
	))
	
	RULE_TYPE_FIELDS = OrderedDict((
		(ruleTypes.PAGE_TITLE_1, ("customValue",)),
		(ruleTypes.PAGE_TITLE_2, ("customValue",)),
		(ruleTypes.ZONE, ("formMode", "skip", "sayName", "customName", "customValue", "mutation")),
		(ruleTypes.MARKER, ("multiple", "formMode", "skip", "sayName", "customName", "customValue", "mutation")),
	))
	
	def strToBool(self, str):
		if str == "True":
			return True
		if str == "False":
			return False
		raise ValueError("Cannot convert {} to a bool".format(repr(str)))
	
	@classmethod
	def getAltFieldLabel(cls, ruleType):
		if ruleType in (ruleTypes.PAGE_TITLE_1, ruleTypes.PAGE_TITLE_2):
			# Translator: Custom page title input label for the rule dialog's properties panel.
			return pgettext("webAccess.ruleProperties", u"Custom page &title:")
		elif ruleType in (ruleTypes.ZONE, ruleTypes.MARKER):
			# Translator: Custom message input label for the rule dialog's properties panel.
			return pgettext("webAccess.ruleProperties", u"Custom messa&ge:")
		return ""
	
	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		
		self.mainGridSizer = wx.GridBagSizer(vgap=5, hgap=10)
		mainSizer.Add(self.mainGridSizer)
		
		self.multipleProperty = wx.CheckBox(self, label=self.FIELDS["multiple"])
		self.formModeProperty = wx.CheckBox(self, label=self.FIELDS["formMode"])
		self.skipProperty = wx.CheckBox(self, label=self.FIELDS["skip"])
		self.sayNameProperty = wx.CheckBox(self, label=self.FIELDS["sayName"])
		self.customNameLabel = wx.StaticText(self, label=self.FIELDS["customName"])
		self.customNameProperty = wx.TextCtrl(self, size=(350, -1))
		self.customValueLabel = wx.StaticText(self, label=self.FIELDS["customValue"] or "")
		self.customValueProperty = wx.TextCtrl(self, size=(350, -1))
		self.mutationLabel = wx.StaticText(self, label=self.FIELDS["mutation"])
		self.mutationProperty = wx.ComboBox(self, style=wx.CB_READONLY)
		# Translator: Text showed when the selected type doesn't have properties available
		self.noPropertiesText = wx.StaticText(self, label=_("No properties available for the selected rule type"))
		
		self.initData()
		
	def checkVisibility(self):
		ruleType = globalRule.get("type", "")
		fields = self.RULE_TYPE_FIELDS.get(ruleType, {})
		self.multipleProperty.Show("multiple" in fields)
		self.formModeProperty.Show("formMode" in fields)
		self.skipProperty.Show("skip" in fields)
		self.sayNameProperty.Show("sayName" in fields)
		self.customNameLabel.Show("customName" in fields)
		self.customNameProperty.Show("customName" in fields)
		self.customValueLabel.Show("customValue" in fields)
		self.customValueProperty.Show("customValue" in fields)
		self.mutationLabel.Show("mutation" in fields)
		self.mutationProperty.Show("mutation" in fields)
		self.noPropertiesText.Show(not bool(fields))
			
		if "mutation" in fields:
			# Translators: The label when there is no control mutation.
			self.mutationProperty.Append(pgettext("webAccess.controlMutation", "<None>"), "")
			for id_ in MUTATIONS_BY_RULE_TYPE.get(ruleType, []):
				label = mutationLabels.get(id_)
				if label is None:
					log.error("No label for mutation id: {}".format(id_))
					label = id_
				self.mutationProperty.Append(label, id_)
			
		self.mainGridSizer.Clear()
		if not bool(fields):
			self.mainGridSizer.Add(self.noPropertiesText, (0,0))
			return
		self.customValueLabel.Label = self.getAltFieldLabel(ruleType)
		if ruleType == ruleTypes.PAGE_TITLE_1 or ruleType == ruleTypes.PAGE_TITLE_2:
			self.mainGridSizer.AddMany([
				(self.customValueLabel, (0,0), (1,2)),
				(self.customValueProperty, (1,0), (1,2))
				])
			return
		if ruleType == ruleTypes.ZONE:	
			self.mainGridSizer.AddMany([
				(self.formModeProperty, (0,0)), 
				(self.skipProperty, (0,1)),
				(self.sayNameProperty, (1,0)),
				(10, 8, (2,0), (1,2)),
				(self.customNameLabel, (3,0), (1,2)),
				(self.customNameProperty, (4,0), (1,2), wx.EXPAND),
				(10, 8, (5,0), (1,2)),
				(self.customValueLabel, (6,0), (1,2)),
				(self.customValueProperty, (7,0), (1,2), wx.EXPAND),
				(10, 8, (8,0), (1,2)),
				(self.mutationLabel, (9,0), (1,2)),
				(self.mutationProperty, (10,0), (1,2), wx.EXPAND),
				])
			return
		if ruleType == ruleTypes.MARKER:
			self.mainGridSizer.AddMany([
				(self.multipleProperty, (0,0)),
				(self.formModeProperty, (0,1)), 
				(self.skipProperty, (1,0)),
				(self.sayNameProperty, (1,1)),
				(10, 8, (2,0), (1,2)),
				(self.customNameLabel, (3,0), (1,2)),
				(self.customNameProperty, (4,0), (1,2), wx.EXPAND),
				(10, 8, (5,0), (1,2)),
				(self.customValueLabel, (6,0), (1,2)),
				(self.customValueProperty, (7,0), (1,2), wx.EXPAND),
				(10, 8, (8,0), (1,2)),
				(self.mutationLabel, (9,0), (1,2)),
				(self.mutationProperty, (10,0), (1,2), wx.EXPAND),
				])
			return
			
	
	def initData(self):
		self.checkVisibility()
		ruleType = globalRule.get("type", "")
		self.multipleProperty.Value = self.strToBool(globalRule["multiple"]) if globalRule.get("multiple") else False
		self.formModeProperty.Value = self.strToBool(globalRule["formMode"]) if globalRule.get("formMode") else False
		self.skipProperty.Value = self.strToBool(globalRule["skip"]) if globalRule.get("skip") else False
		self.sayNameProperty.Value = self.strToBool(globalRule["sayName"]) if globalRule.get("sayName") else True
		self.customNameProperty.Value = globalRule.get("customName", "")
		self.customValueLabel.Label = self.getAltFieldLabel(ruleType)
		self.customValueProperty.Value = globalRule.get("customValue", "")
		
		if globalRule.get("mutation"):
			for index in range(1, self.mutationProperty.Count + 1):
				id_ = self.mutationProperty.GetClientData(index)
				if id_ == globalRule["mutation"]:
					break
			else:
				# Allow to bypass mutation choice by rule type
				label = mutationLabels.get(id_)
				if label is None:
					log.error("No label for mutation id: {}".format(id_))
					label = id_
				self.mutationProperty.Append(label, id_)
				index += 1
		else:
			index = 0
		self.mutationProperty.SetSelection(index)
		
	def onSave(self):
		setIfNotEmpty(globalRule, "multiple", str(self.multipleProperty.Value))
		setIfNotEmpty(globalRule, "formMode", str(self.formModeProperty.Value))
		setIfNotEmpty(globalRule, "skip", str(self.skipProperty.Value))
		setIfNotEmpty(globalRule, "sayName", str(self.sayNameProperty.Value))
		setIfNotEmpty(globalRule, "customName", self.customNameProperty.Value)
		setIfNotEmpty(globalRule, "customValue", self.customValueProperty.Value)
		if self.mutationProperty.Selection > 0:
			globalRule["mutation"] = self.mutationProperty.GetClientData(self.mutationProperty.Selection)
		
		ruleType = globalRule.get("type", "")
		showedFields = self.RULE_TYPE_FIELDS.get(ruleType, {})
		for field in self.FIELDS.keys():
			if field not in showedFields and globalRule.get(field):
				del globalRule[field]


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

		# Translators: Label for the box containing the criterias by sequence order in the criteria panel
		criteriaSetsLabel = wx.StaticText(self, label=_("&Criteria sets by sequence order"))
		self.criteriaSetsList = wx.ListBox(self)
		self.criteriaSetsList.Bind(wx.EVT_LISTBOX, self.onCriteriaChange)

		# Translators: Label for the criteria's summary readonly input
		criteriaSummaryLabel = wx.StaticText(self, label=_("Criteria &summary"))
		self.criteriaSummary = wx.TextCtrl(self, size=(220, 100), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)

		# Translators: New criteria button label
		self.newButton = wx.Button(self, label=_("&New"))
		# Translators: Edit criteria button label
		self.editButton = wx.Button(self, label=_("&Edit"))
		# Translators: Delete criteria button label
		self.deleteButton = wx.Button(self, label=_("&Delete"))

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer.AddMany((
			self.newButton,
			(5,5),
			self.editButton,
			(5,5),
			self.deleteButton
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
		self.criterias = []
		self.newButton.Bind(wx.EVT_BUTTON, self.onNewCriteriaBtn)
		self.editButton.Bind(wx.EVT_BUTTON, self.onEditCriteriaBtn)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDeleteCriteriaBtn)

		if newRule or not globalRule.get("criterias"):
			self.criteriaSetsList.Clear()
			self.criteriaSummary.Value = ""
			self.editButton.Disable()
			self.deleteButton.Disable()

		else:
			self.criterias = globalRule["criterias"]
			for criteria in self.criterias:
				self.criteriaSetsList.Append(self.getCriteriaName(criteria))
			self.criteriaSetsList.SetSelection(0)
			self.criteriaSummary.Value = ""
			self.getCriteriaSummary(self.criterias[0])
			
	# todo: complete criteria's  summary
	def getCriteriaSummary(self, criteria):
		from ..gui import criteriaSetEditor
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.Colour(55,71,79)))
		self.criteriaSummary.AppendText("General\n")
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.BLACK))
		self.criteriaSummary.AppendText("Name ")
		self.criteriaSummary.AppendText(criteria.get("name", "none"))
		
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.Colour(55,71,79)))
		self.criteriaSummary.AppendText("\nContext\n")
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.BLACK))
		self.criteriaSummary.AppendText(criteriaSetEditor.ContextPanel.getSummary(criteria))
		
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.Colour(55,71,79)))
		self.criteriaSummary.AppendText("\nCriterias\n")
		self.criteriaSummary.SetDefaultStyle(wx.TextAttr(wx.BLACK))
		self.criteriaSummary.AppendText(criteriaSetEditor.CriteriaPanel.getSummary(criteria))
				
	def getCriteriaName(self, criteria):
		if criteria.get("name"):
			return criteria["name"]
		else:
			existingCriterias = []
			if criteria.get("contextPageTitle"):
				existingCriterias.append(criteria["contextPageTitle"])
			if criteria.get("contextPageType"):
				existingCriterias.append(criteria["contextPageType"])
			if criteria.get("contextParent"):
				existingCriterias.append(criteria["contextParent"])
			return " / ".join(existingCriterias)

	def onNewCriteriaBtn(self, evt):
		from ..gui import criteriaSetEditor
		gui.mainFrame.prePopup()
		with criteriaSetEditor.CriteriaSetEditorDialog(gui.mainFrame, self.criterias) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				self.criterias.insert(dlg.sequenceOrder, dlg.criteria)
				self.refreshCriterias(dlg.sequenceOrder)
		gui.mainFrame.postPopup()

	def onEditCriteriaBtn(self, evt):
		from ..gui import criteriaSetEditor
		gui.mainFrame.prePopup()
		selectedCriteria = self.criterias[self.criteriaSetsList.Selection]
		with criteriaSetEditor.CriteriaSetEditorDialog(gui.mainFrame, self.criterias, self.criteriaSetsList.Selection) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				if dlg.sequenceOrder != self.criteriaSetsList.Selection:
					self.criterias.remove(selectedCriteria)
					self.criterias.insert(dlg.sequenceOrder, dlg.criteria)
				else:
					selectedCriteria = dlg.criteria
				self.refreshCriterias(dlg.sequenceOrder)
		gui.mainFrame.postPopup()
		
	def onDeleteCriteriaBtn(self, evt):
		# Translators: Confirmation message when deleting a criteria
		with wx.GenericMessageDialog(self, _("Are you sure you want to delete this criteria ?")) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				selectedCriteria = self.criterias[self.criteriaSetsList.Selection]
				self.criterias.remove(selectedCriteria)
				self.refreshCriterias()
	
	def onCriteriaChange(self, evt):
		if not self.editButton.Enabled:
			self.editButton.Enable(enable=True)
			self.deleteButton.Enable(enable=True)
		selectedCriteria = self.criterias[self.criteriaSetsList.Selection]
		self.criteriaSummary.Value = ""
		self.getCriteriaSummary(selectedCriteria)
	
	def refreshCriterias(self, sequenceOrder=0):
		self.criteriaSetsList.Clear()
		for criteria in self.criterias:
				self.criteriaSetsList.Append(self.getCriteriaName(criteria))
		self.criteriaSetsList.Selection = sequenceOrder
		self.onCriteriaChange(None)	
	
	def onSave(self):
		if self.criterias:
			globalRule["criterias"] = self.criterias
		elif globalRule.get("criterias"):
			 del globalRule["criterias"]


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

		typeChoices = []
		for key, label in ruleTypes.ruleTypeLabels.items():
			typeChoices.append(label)
		# Translators: Label of the rule type choice list.
		ruleTypeLabel = wx.StaticText(self, label=_("Rule &type"))
		self.ruleType = wx.Choice(self, choices=typeChoices)
		self.ruleType.Bind(wx.EVT_CHOICE, self.onTypeChange)
		# todo: change tooltip's text
		# Translators: Tooltip for rule type choice list.
		self.ruleType.SetToolTip(_("TOOLTIP EXEMPLE"))
		
		# Translators: Label of the rule name input.
		ruleNameLabel = wx.StaticText(self, label=_("Rule &name"))
		self.ruleName = wx.TextCtrl(self)

		# Translators: Label of the rule documentation input.
		userDocLabel = wx.StaticText(self, label=_("User &documentation"))
		self.ruleDocumentation = wx.TextCtrl(self, size=(400, 100), style=wx.TE_MULTILINE)

		# Translators: Label of the rule summary.
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
			self.ruleSummary.Value = ""
		else:
			for index, key in enumerate(ruleTypes.ruleTypeLabels.keys()):
				if key == globalRule["type"]:
					self.ruleType.SetSelection(index)
					break
			# todo: Init summary value
			
		self.ruleDocumentation.Value = globalRule.get("comment", "")
		self.ruleName.Value = globalRule.get("name", "")
		
	# Rule's type needs to be saved when changed as numerous fields depends on which type is selected
	def onTypeChange(self, evt):
		globalRule["type"] = tuple(ruleTypes.ruleTypeLabels.keys())[self.ruleType.Selection]

	def isValid(self):
		return self.isValidData
	
	def onSave(self):
		self.isValidData = True

		# Type is required
		if not self.ruleType.Selection >= 0:
			gui.messageBox(
				# Translators: Error message when no type is chosen before saving the rule
				message=_("You must choose a type for this rule"),
				caption=_("Error"),
				style=wx.OK | wx.ICON_ERROR,
				parent=self
			)
			self.isValidData = False
			self.ruleType.SetFocus()
			return
		else:
			globalRule["type"] = tuple(ruleTypes.ruleTypeLabels.keys())[self.ruleType.Selection]

		# Name is required
		if not self.ruleName.Value.strip():
			gui.messageBox(
				# Translators: Error message when no name is entered before saving the rule
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
			
		setIfNotEmpty(globalRule, "comment", self.ruleDocumentation.Value)


class RuleEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess rule settings dialog.
	title = _("WebAccess Rule editor")
	categoryClasses = [GeneralPanel, CriteriaPanel, ActionsPanel, PropertiesPanel]
	INITIAL_SIZE = (750, 520)

	def __init__(self, parent, initialCategory=None, context=None, new=False):
		global newRule
		newRule = new	
		self.initData(context)
		super(RuleEditorDialog, self).__init__(parent, initialCategory=initialCategory)

	def initData(self, context):
		global globalRule, globalContext
		self.context = globalContext = context
		self.rule = context.get("rule")
		self.markerManager = context["webModule"].markerManager

		if context.get("rule"):
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
			
	def onCategoryChange(self, evt):
		currentCat = self.currentCategory
		newIndex = evt.GetIndex()
		if not currentCat or newIndex != self.categoryClasses.index(currentCat.__class__):
			panelClassName = type(self.catIdToInstanceMap.get(newIndex)).__name__
			if  panelClassName in ("ActionsPanel", "PropertiesPanel"):
				self.catIdToInstanceMap.get(newIndex).checkVisibility()
			self._doCategoryChange(newIndex)
		else:
			evt.Skip()

	def onOk(self, evt):
		try:
			self._doSave()
		except ValueError:
			log.debugWarning("", exc_info=True)
			return

		if newRule:
			for rule in self.markerManager.getQueries():
				if globalRule["name"] == rule.name:
					gui.messageBox(
						# Translators: Error message when another rule with the same name already exists
						message=_("There already is another rule with the same name."),
						caption=_("Error"),
						style=wx.ICON_ERROR | wx.OK | wx.CANCEL,
						parent=self
					)
					return

		else:
			self.markerManager.removeQuery(self.rule)
		savedRule = ruleHandler.VirtualMarkerQuery(self.markerManager, globalRule)
		self.markerManager.addQuery(savedRule)
		webModuleHandler.update(webModule=self.context["webModule"], focus=self.context["focusObject"])

		for panel in self.catIdToInstanceMap.values():
			panel.Destroy()
		super(MultiCategorySettingsDialog, self).onOk(evt)

	def Destroy(self):
		super(RuleEditorDialog, self).Destroy()
