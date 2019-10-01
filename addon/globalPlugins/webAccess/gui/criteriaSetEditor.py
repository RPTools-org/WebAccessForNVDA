# -*- coding: utf-8 -*-

import wx
import re
import gui
from collections import OrderedDict
from ..ruleHandler import ruleTypes
from ..gui import ruleEditor
import controlTypes
from logHandler import log

try:
	from gui.settingsDialogs import (
		MultiCategorySettingsDialog,
		SettingsDialog,
		SettingsPanel
	)
except ImportError:
	from ..backports.nvda_2018_2.gui_settingsDialogs import (
		MultiCategorySettingsDialog,
		SettingsDialog,
		SettingsPanel
	)

try:
	from six import iteritems, text_type
except ImportError:
	# NVDA version < 2018.3
	iteritems = dict.iteritems
	text_type = unicode

globalNewCriteria = True
globalNbCriterias = 0
globalSelectedCriteria = 0
globalCriteria = None

LABEL_ACCEL = re.compile("&(?!&)")
"""
Compiled pattern used to strip accelerator key indicators from labels.
"""
EXPR_VALUE = re.compile("(([^!&| ])+( (?=[^!&|]))*)+")
"""
Compiled pattern used to capture values in expressions.
"""
EXPR = re.compile("^ *!? *[^!&|]+( *[&|] *!? *[^!&|]+)*$")
"""
Compiled pattern used to validate expressions.
"""
EXPR_INT = re.compile("^ *!? *[0-9]+( *[&|] *!? *[0-9]+)* *$")
"""
Compiled pattern used to validate expressions whose values are integers.
"""

def captureValues(expr):
	"""
	Yields value, startPos, endPos
	"""
	for match in EXPR_VALUE.finditer(expr):
		span = match.span()
		yield expr[span[0]:span[1]], span[0], span[1]

def getStatesLblExprForSet(states):
	return " & ".join((
		controlTypes.stateLabels.get(state, state)
		for state in states
	))
	
def translateExprValues(expr, func):
	buf = list(expr)
	offset = 0
	for src, start, end in captureValues(expr):
		dest = text_type(func(src))
		start += offset
		end += offset
		buf[start:end] = dest
		offset += len(dest) - len(src)
	return u"".join(buf)

def translateRoleIdToLbl(expr):
	def translate(value):
		try:
			return controlTypes.roleLabels[int(value)]
		except (KeyError, ValueError):
			return value
	return translateExprValues(expr, translate)

def translateStatesLblToId(expr):
	def translate(value):
		for key, candidate in iteritems(controlTypes.stateLabels):
			if candidate == value:
				return text_type(key)
		return value
	return translateExprValues(expr, translate)

def translateStatesIdToLbl(expr):
	def translate(value):
		try:
			return controlTypes.stateLabels[int(value)]
		except (KeyError, ValueError):
			return value
	return translateExprValues(expr, translate)

def translateRoleLblToId(expr):
	def translate(value):
		for key, candidate in iteritems(controlTypes.roleLabels):
			if candidate == value:
				return text_type(key)
		return value
	return translateExprValues(expr, translate)

def stripAccel(label):
	return LABEL_ACCEL.sub("", label)

def stripAccelAndColon(label):
	return stripAccel(label).rstrip(":").rstrip()


# todo: make this panel
class OverridesPanes(SettingsPanel):
	# Translators: This is the label for the overrides's panel.
	title = _("Overrides")


class CriteriaPanel(SettingsPanel):
	# Translators: This is the label for the criteria panel.
	title = _("Criteria")
	
	# The semi-column is part of the labels because some localizations
	# (ie. French) require it to be prepended with one space.
	FIELDS = OrderedDict((
		# Translator: Text criteria field label on the rule's criteria panel dialog.
		("text", pgettext("webAccess.ruleCriteria", u"&Text")),
		# Translator: Role criteria field label on the rule's criteria panel dialog.
		("role", pgettext("webAccess.ruleCriteria", u"&Role")),
		# Translator: Tag criteria field label on the rule's criteria panel dialog.
		("tag", pgettext("webAccess.ruleCriteria", u"T&ag")),
		# Translator: ID criteria field label on the rule's criteria panel dialog.
		("id", pgettext("webAccess.ruleCriteria", u"&ID")),
		# Translator: Class criteria field label on the rule's criteria panel dialog.
		("className", pgettext("webAccess.ruleCriteria", u"&Class")),
		# Translator: States criteria field label on the rule's criteria panel dialog.
		("states", pgettext("webAccess.ruleCriteria", u"&States")),
		# Translator: Images source criteria field label on the rule's criteria panel dialog.
		("src", pgettext("webAccess.ruleCriteria", u"Ima&ge source")),
		# Translator: Relative path criteria field label on the rule's criteria panel dialog.
		("relativePath", pgettext("webAccess.ruleCriteria", u"R&elative path")),
		# Translator: Index criteria field label on the rule's criteria panel dialog.
		("index", pgettext("webAccess.ruleCriteria", u"Inde&x")),
	))
	
	@classmethod
	def getSummary(cls, data):
		parts = []
		for key, label in cls.FIELDS.items():
			if key in data:
				value = data[key]
				if key == "role":
					value = translateRoleIdToLbl(value)
				elif key == "states":
					value = translateStatesIdToLbl(value)
				parts.append(u"{} {}".format(stripAccel(label), value))
		if parts:
			return "\n".join(parts)
		else:
			# Translators: Fail-back criteria summary in rule's criteria panel dialog.
			return _("No criteria")
	
	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		flexGridSizer = wx.FlexGridSizer(cols=2, vgap=10, hgap=10)
		mainSizer.Add(flexGridSizer)
		
		textLabel = wx.StaticText(self, label=self.FIELDS["text"])
		self.textContext = wx.ComboBox(self, size=(200, -1))
		
		roleLabel = wx.StaticText(self, label=self.FIELDS["role"])
		self.roleContext = wx.ComboBox(self)

		tagLabel = wx.StaticText(self, label=self.FIELDS["tag"])
		self.tagContext = wx.ComboBox(self)
		
		idLabel = wx.StaticText(self, label=self.FIELDS["id"])
		self.idContext = wx.ComboBox(self)
		
		classNameLabel = wx.StaticText(self, label=self.FIELDS["className"])
		self.classNameContext = wx.ComboBox(self)

		statesLabel = wx.StaticText(self, label=self.FIELDS["states"])
		self.statesContext = wx.ComboBox(self)
		
		srcLabel = wx.StaticText(self, label=self.FIELDS["src"])
		self.srcContext = wx.ComboBox(self)
		
		relativePathLabel = wx.StaticText(self, label=self.FIELDS["relativePath"])
		self.relativePathContext = wx.TextCtrl(self)

		indexLabel = wx.StaticText(self, label=self.FIELDS["index"])
		self.indexContext = wx.TextCtrl(self)
		
		flexGridSizer.Add(textLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.textContext, flag=wx.EXPAND)
		flexGridSizer.Add(roleLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.roleContext, flag=wx.EXPAND)
		flexGridSizer.Add(tagLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.tagContext, flag=wx.EXPAND)
		flexGridSizer.Add(idLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.idContext, flag=wx.EXPAND)
		flexGridSizer.Add(classNameLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.classNameContext, flag=wx.EXPAND)
		flexGridSizer.Add(statesLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.statesContext, flag=wx.EXPAND)
		flexGridSizer.Add(srcLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.srcContext, flag=wx.EXPAND)
		flexGridSizer.Add(relativePathLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.relativePathContext, flag=wx.EXPAND)
		flexGridSizer.Add(indexLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.indexContext, flag=wx.EXPAND)
		
		self.initData()
		
	def initData(self):
		self.isValidData = True
		markerManager = ruleEditor.globalContext["webModule"].markerManager
		
		if markerManager.nodeManager:
			node = markerManager.nodeManager.getCaretNode()
			textNode = node
			node = node.parent
			t = textNode.text
			if t == " ":
				t = ""
			textChoices = [t]
			if node.previousTextNode is not None:
				textChoices.append("<" + node.previousTextNode.text)
			
			roleChoices = []
			tagChoices = []
			idChoices = []
			classChoices = []
			statesChoices = []
			srcChoices = []
			# todo: actually there are empty choices created
			while node is not None:
				roleChoices.append(controlTypes.roleLabels.get(node.role, "") or "")
				tagChoices.append(node.tag or "")
				idChoices.append(node.id or "")
				classChoices.append(node.className or "")
				statesChoices.append(getStatesLblExprForSet(node.states) or "")
				srcChoices.append(node.src or "")
				node = node.parent
			
			self.textContext.Set(textChoices)
			self.roleContext.Set(roleChoices)
			self.tagContext.Set(tagChoices)
			self.idContext.Set(idChoices)
			self.classNameContext.Set(classChoices)
			self.statesContext.Set(statesChoices)
			self.srcContext.Set(srcChoices)
		
		self.textContext.Value = globalCriteria.get("text", "")
		self.roleContext.Value = translateRoleIdToLbl(globalCriteria.get("role", ""))
		self.tagContext.Value = globalCriteria.get("tag", "")
		self.idContext.Value = globalCriteria.get("id", "")
		self.classNameContext.Value = globalCriteria.get("className", "")
		self.statesContext.Value = translateStatesIdToLbl(globalCriteria.get("states", ""))
		self.srcContext.Value = globalCriteria.get("src", "")
		self.relativePathContext.Value = str(globalCriteria.get("relativePath", ""))
		self.indexContext.Value = str(globalCriteria.get("index", ""))
		
	def isValid(self):
		return self.isValidData
		
	def onSave(self):
		self.isValidData = True
		ruleEditor.setIfNotEmpty(globalCriteria, "text", self.textContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "tag", self.tagContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "id", self.idContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "className", self.classNameContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "src", self.srcContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "relativePath", self.relativePathContext.Value)
		
		roleLblExpr = self.roleContext.Value
		if roleLblExpr:
			if not EXPR.match(roleLblExpr):
				gui.messageBox(
					# Translators: Error message when the field doesn't meet the required syntax
					message=(_('Syntax error in the field "{field}"'))
							.format(field=stripAccelAndColon(self.FIELDS["role"])),
					caption=_("Error"),
					style=wx.OK | wx.ICON_ERROR,
					parent=self
				)
				self.isValidData = False
				self.roleContext.SetFocus()
				return
			roleIdExpr = translateRoleLblToId(roleLblExpr)
			if not EXPR_INT.match(roleIdExpr):
				gui.messageBox(
					# Translators: Error message when the field doesn't match any known identifier
					message=(_('Unknown identifier in the field "{field}"'))
							.format(field=stripAccelAndColon(self.FIELDS["role"])),
					caption=_("Error"),
					style=wx.OK | wx.ICON_ERROR,
					parent=self
				)
				self.isValidData = False
				self.roleContext.SetFocus()
				return
			globalCriteria["role"] = roleIdExpr
			
		statesLblExpr = self.statesContext.Value
		if statesLblExpr:
			if not EXPR.match(statesLblExpr):
				gui.messageBox(
					# Translators: Error message when the field doesn't meet the required syntax
					message=(_('Syntax error in the field "{field}"'))
							.format(field=stripAccelAndColon(self.FIELDS["states"])),
					caption=_("Error"),
					style=wx.OK | wx.ICON_ERROR,
					parent=self
				)
				self.isValidData = False
				self.statesContext.SetFocus()
				return
			statesIdExpr = translateStatesLblToId(statesLblExpr)
			if not EXPR_INT.match(statesIdExpr):
				gui.messageBox(
					# Translators: Error message when the field doesn't match any known identifier
					message=(_('Unknown identifier in the field "{field}"'))
							.format(field=stripAccelAndColon(self.FIELDS["states"])),
					caption=_("Error"),
					style=wx.OK | wx.ICON_ERROR,
					parent=self
				)
				self.isValidData = False
				self.statesContext.SetFocus()
				return
			globalCriteria["states"] = statesIdExpr
			
		index = self.indexContext.Value
		if index.strip():
			try:
				index = int(index)
			except:
				index = 0
			if index > 0:
				globalCriteria["index"] = index
			else:
				gui.messageBox(
					# Translators: Error message when the index is not positive
					message=_("Index, if set, must be a positive integer."),
					caption=_("Error"),
					style=wx.OK | wx.ICON_ERROR,
					parent=self
				)
				self.isValidData = False
				self.indexContext.SetFocus()
				return


class ContextPanel(SettingsPanel):
	# Translators: This is the label for the criteria context panel.
	title = _("Context")
	
	# The semi-column is part of the labels because some localizations
	# (ie. French) require it to be prepended with one space.
	FIELDS = OrderedDict((
		# Translator: Page title field label on the criteria set's context panel.
		("contextPageTitle", pgettext("webAccess.ruleContext", u"Page &title")),
		# Translator: Page type field label on the criteria set's context panel.
		("contextPageType", pgettext("webAccess.ruleContext", u"Page t&ype")),
		# Translator: Parent element field label on the criteria set's context panel.
		("contextParent", pgettext("webAccess.ruleContext", u"&Parent element")),
	))
	
	@classmethod
	def getSummary(cls, data):
		parts = []
		for key, label in cls.FIELDS.items():
			if key in data:
				parts.append(u"{} {}".format(stripAccel(label), data[key]))
		if parts:
			return "\n".join(parts)
		else:
			# Translators: Fail-back context summary in criteria set's context panel.
			return _("Global - Applies to the whole web module.")
	
	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		flexGridSizer = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=10)
		mainSizer.Add(flexGridSizer)
		
		self.pageTitleLabel = wx.StaticText(self, label=self.FIELDS["contextPageTitle"])
		self.pageTitleContext = wx.ComboBox(self, size=(200, -1))
		
		pageTypeLabel = wx.StaticText(self, label=self.FIELDS["contextPageType"])
		self.pageTypeContext = wx.ComboBox(self)

		parentElementLabel = wx.StaticText(self, label=self.FIELDS["contextParent"])
		self.parentElementContext = wx.ComboBox(self)
		
		flexGridSizer.Add(self.pageTitleLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.pageTitleContext, flag=wx.EXPAND)
		flexGridSizer.Add(pageTypeLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.pageTypeContext, flag=wx.EXPAND)
		flexGridSizer.Add(parentElementLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		flexGridSizer.Add(self.parentElementContext, flag=wx.EXPAND)

		self.initData()

	def initData(self):
		markerManager = ruleEditor.globalContext["webModule"].markerManager
		node = markerManager.nodeManager.getCaretNode()
		
		showPageTitle = ruleEditor.globalRule.get("type", "") != ruleTypes.PAGE_TITLE_1
		if showPageTitle:
			self.pageTitleContext.Set([ruleEditor.globalContext["pageTitle"]])
			self.pageTitleContext.Value = globalCriteria.get("contextPageTitle", "")
		self.pageTitleLabel.Show(showPageTitle)
		self.pageTitleContext.Show(showPageTitle)
		
		self.pageTypeContext.Set(markerManager.getPageTypes())
		self.pageTypeContext.Value = globalCriteria.get("contextPageType", "")

		parents = []
		for result in markerManager.getResults():
			query = result.markerQuery
			if (
				query.type in (ruleTypes.PARENT, ruleTypes.ZONE)
				and node in result.node
			):
				parents.insert(0, query.name)
		self.parentElementContext.Set(parents)
		self.parentElementContext.Value = globalCriteria.get("contextParent", "")

	def onSave(self):
		ruleEditor.setIfNotEmpty(globalCriteria, "contextPageTitle", self.pageTitleContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "contextPageType", self.pageTypeContext.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "contextParent", self.parentElementContext.Value)


class GeneralPanel(SettingsPanel):
	# Translators: This is the label for the criteria general panel.
	title = _("General")

	def makeSettings(self, settingsSizer):
		marginSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		marginSizer.AddSpacer(10)
		marginSizer.Add(mainSizer)
		settingsSizer.Add(marginSizer, flag=wx.EXPAND, proportion=1)
		
		# Translators: Name field label of the criteria dialog's general panel.
		nameLabel = wx.StaticText(self, label=_("&Name"))
		self.criteriaName = wx.TextCtrl(self)
		
		# Translators: Sequence order field label of the criteria dialog's general panel.
		sequenceLabel = wx.StaticText(self, label=_("&Sequence order"))
		self.criteriaOrder = wx.Choice(self)

		# Translators: Technical notes field label of the criteria dialog's general panel.
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
		nbCriteriasAfterCreation = globalNbCriterias + 1 if globalNewCriteria else globalNbCriterias
		for i in range(nbCriteriasAfterCreation):
			self.criteriaOrder.Append(str(i + 1))
		
		if globalNewCriteria:
			self.criteriaOrder.SetSelection(globalNbCriterias)
		else:
			self.criteriaOrder.SetSelection(globalSelectedCriteria)
			
		self.criteriaName.Value = globalCriteria.get("name", "")
		self.criteriaNotes.Value = globalCriteria.get("notes", "")
	
	def onSave(self):
		global globalSelectedCriteria
		globalSelectedCriteria = self.criteriaOrder.Selection
		ruleEditor.setIfNotEmpty(globalCriteria, "name", self.criteriaName.Value)
		ruleEditor.setIfNotEmpty(globalCriteria, "notes", self.criteriaNotes.Value)


class CriteriaSetEditorDialog(MultiCategorySettingsDialog):

	# Translators: This is the label for the WebAccess criteria settings dialog.
	title = _("WebAccess Criteria set editor")
	categoryClasses = [GeneralPanel, ContextPanel, CriteriaPanel]
	INITIAL_SIZE = (800, 480)

	def __init__(self, parent, criterias, selectedCriteria=None):
		global globalCriteria
		global globalNbCriterias
		global globalSelectedCriteria
		global globalNewCriteria
		globalCriteria = dict() if selectedCriteria is None else criterias[selectedCriteria]
		globalNewCriteria = selectedCriteria is None
		globalSelectedCriteria = selectedCriteria
		globalNbCriterias = len(criterias)
		
		super(CriteriaSetEditorDialog, self).__init__(parent, initialCategory=None)

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
		for panel in self.catIdToInstanceMap.values():
			panel.Destroy()
		self.criteria = globalCriteria
		self.sequenceOrder = globalSelectedCriteria
		SettingsDialog.onOk(self, evt)

	def Destroy(self):
		super(CriteriaSetEditorDialog, self).Destroy()
