# -*- coding: utf-8 -*-

import wx

import gui
from logHandler import log

from ..ruleHandler import ruleTypes

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


class GeneralPanel(SettingsPanel):
	# Translators: This is the label for the general settings panel.
	title = _("General")

	def makeSettings(self, settingsSizer):
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)

		typeChoices = []
		for key, label in ruleTypes.ruleTypeLabels.items():
			typeChoices.append(label)
		self.typeList = settingsSizerHelper.addLabeledControl(_("Type list"), wx.Choice, choices=typeChoices)
		self.typeList.SetToolTip(wx.ToolTip("Choose the type."))

		# typeInputText = wx.StaticText(self, label=_(u"Rule &type:"))
		# settingsSizerHelper.addItem(typeInputText)
		# typeInput = self.ruleTypeCombo = wx.ComboBox(self, style=wx.CB_READONLY)
		# typeInput.Bind(wx.EVT_COMBOBOX, self.onRuleTypeChoice)
		# for key, label in ruleTypes.ruleTypeLabels.items():
		# 	self.ruleTypeCombo.Append(label, key)
		# headerSizer.Add(typeInput, flag=wx.EXPAND)
	
	def onSave(self):
		raise NotImplementedError


class RuleEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess settings dialog.
	title = _("WebAccess rule editor")
	categoryClasses = [GeneralPanel]

	def makeSettings(self, settingsSizer):
		# Ensure that after the settings dialog is created the name is set correctly
		super(RuleEditorDialog, self).makeSettings(settingsSizer)
		self.SetTitle(self._getDialogTitle())
		
	def _getDialogTitle(self):
		return u"{dialogTitle}: {panelTitle}".format(
			dialogTitle=self.title,
			panelTitle=self.currentCategory.title
		)

	def onOk(self, evt):
		log.debugWarning("OK")

	def onCancel(self, evt):
		log.debugWarning("CANCEL")

	def onCategoryChange(self,evt):
		super(RuleEditorDialog,self).onCategoryChange(evt)
		if evt.Skipped:
			return
		self.SetTitle(self._getDialogTitle())

	def Destroy(self):
		super(RuleEditorDialog, self).Destroy()
