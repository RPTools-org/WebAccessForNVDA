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

globalCriteria = False

class GeneralPanel(SettingsPanel):
	# Translators: This is the label for the general settings panel.
	title = _("General")

	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		
		# Name
		nameLabel = wx.StaticText(self, label=_("&Name"))
		self.criteriaName = wx.TextCtrl(self)
		
		# Sequence order
		sequenceLabel = wx.StaticText(self, label=_("&Sequence order"))
		self.criteriaOrder = wx.Choice(self)

		# Technical notes
		notesLabel = wx.StaticText(self, label=_("Technical &notes"))
		self.criteriaNotes = wx.TextCtrl(self, size=(300, 200), style=wx.TE_MULTILINE)
		
		mainSizer.Add(nameLabel)
		mainSizer.Add(self.criteriaName, flag=wx.EXPAND)
		mainSizer.AddSpacer(10)
		mainSizer.Add(sequenceLabel)
		mainSizer.Add(self.criteriaOrder, flag=wx.EXPAND)
		mainSizer.AddSpacer(10)
		mainSizer.Add(notesLabel)
		mainSizer.Add(self.criteriaNotes, flag=wx.EXPAND)

		self.initData()

	def initData(self):
		# todo: Init criteriaOrder
		self.criteriaOrder.AppendItems(["order 1", "order 2", "order 3"])
		
		if not globalCriteria:
			self.criteriaName.Value = ""
			self.criteriaOrder.SetSelection(-1)
			self.criteriaNotes.Value = ""
			
		# todo: Real initialisation
		else:
			self.criteriaName.Value = globalCriteria.get("name", "")
			self.criteriaNotes.Value = globalCriteria.get("notes", "")
			self.criteriaOrder.SetSelection(globalCriteria.get("sequenceOrder", -1))
	
	def onSave(self):
		if self.criteriaName.Value:
			globalCriteria['name'] = self.criteriaName.Value
		if self.criteriaNotes.Value:
			globalCriteria["notes"] = self.criteriaNotes.Value
		if self.criteriaOrder.Selection != -1:
			globalCriteria["sequenceOrder"] = self.criteriaOrder.Selection


class CriteriaSetEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess settings dialog.
	title = _("WebAccess Criteria set editor")
	categoryClasses = [GeneralPanel]
	INITIAL_SIZE = (800, 480)
	MIN_SIZE = (470, 240)


	def __init__(self, parent, initialCategory=None, criteria=None):
		global globalCriteria
		if criteria:
			globalCriteria = criteria
		else:
			globalCriteria = dict()
		self.initialCategory = initialCategory
		self.currentCategory = None
		self.setPostInitFocus = None
		self.catIdToInstanceMap = {}
		super(MultiCategorySettingsDialog, self).__init__(parent)

		self.SetMinSize(self.scaleSize(self.MIN_SIZE))
		self.SetSize(self.scaleSize(self.INITIAL_SIZE))
		self.CentreOnScreen()

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

		self.criteria = globalCriteria
		wx.Dialog.ProcessEvent(self, evt)
		super(MultiCategorySettingsDialog, self).onOk(evt)

	def Destroy(self):
		super(CriteriaSetEditorDialog, self).Destroy()
