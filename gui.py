#!/usr/bin/python
# -*- coding: UTF-8 -*-

import gettext
import json
import os
import subprocess
import warnings

from tkinter import *
import tkinter.filedialog as filedialog
from tkinter import messagebox
from tkinter.ttk import *

from datetime import date
from dienstplan import Dienstplan
from util import _PDFLATEX, _CONFIG_DIR, printing, setupLocalization

class Application(Frame):
	def createPDF(self):
		jobName = _("Roster-") + str(self.dienstplan.year) + "-" + str(self.dienstplan.month)
		if self.pdfCreated:
			printing(jobName+".pdf")

		if self.dienstplan and self.selectedName:
			latex = self.dienstplan.getLatex(self.selectedName, self.translateVar.get() == 1)

			curDir = os.path.dirname(os.path.abspath(__file__))
			pdflatex = subprocess.Popen([_PDFLATEX, "-jobname="+jobName, "--"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			(stdout, stderr) = pdflatex.communicate(latex.encode('utf8'))
			os.remove(jobName+".log")
			os.remove(jobName+".aux")

			self.pdfCreated = True
			self.pdfButton.config(text=_("Print (default printer)"))


	def exportToCalendar(self):
		if self.dienstplan and self.selectedName:
			self.progressBar.pack(fill=X, pady=5)
			self.progressBar.configure(maximum=len(self.dienstplan.shifts), value=0)
			self.calendarButton.pack_forget()
			for day, event in enumerate(self.dienstplan.addToCalendar(self.selectedName, self.translateVar.get() == 1), 1):
				self.progressBar.step()
				self.update_idletasks()

			self.progressBar.pack_forget()
			self.calendarButton.pack()

	def selectFile(self):
		filename = filedialog.askopenfilename(filetypes=[(_("Rosters"), "SPX*.pdf"), (_("All PDF files"), "*.pdf")])
		self.filenameVar.set(filename)

		if self.selectedName is not None:
			self.lastSelectedName = self.selectedName
		self.selectedName = None
		self.dienstplan = None
		self.pdfCreated = False
		self.resultText.delete(1.0, END)
		self.nameList.delete(0, END)

		if not filename == "":
			self.openFile(filename)

	def openFile(self, filename):
		with warnings.catch_warnings(record=True) as warningsList:
			self.dienstplan = Dienstplan(filename)
			self.nameList.insert(END, *sorted(self.dienstplan.shifts.keys()))

			if self.lastSelectedName in self.dienstplan.shifts:
				self.nameList.selection_set(sorted(self.dienstplan.shifts.keys()).index(self.lastSelectedName))
				self.updateResults()

			for warning in warningsList:
				messagebox.showwarning(warning.category.__name__,  warning.category.__name__ + ": " + str(warning.message))

	def selectName(self, event):
		w = event.widget
		if w == self.nameList:
			self.updateResults()

	def updateResults(self):
		if self.nameList.curselection():
			index = int(self.nameList.curselection()[0])
			self.selectedName = self.nameList.get(index)

			self.resultText.delete(1.0, END)
			self.resultText.insert(END, self.dienstplan.getText(self.selectedName, self.translateVar.get() == 1))

			self.pdfCreated = False
			self.pdfButton.config(text=_("Create PDF"))

	def _loadConfig(self):
		try:
			with open(_CONFIG_DIR + "/config.json") as configFile:
				config = json.load(configFile)
		except:
			config = {}

		if "translate" in config and config["translate"]:
			self.translateVar.set(1)

		if "lastSelectedName" in config:
			self.lastSelectedName = config["lastSelectedName"]

	def _saveConfig(self):
		config = {}
		config["translate"] = self.translateVar.get() == 1
		config["lastSelectedName"] = self.selectedName

		with open(_CONFIG_DIR + "/config.json", "w") as configFile:
			json.dump(config, configFile)

	def onClose(self):
		self._saveConfig()
		self.master.destroy()

	def createWidgets(self):
		self.translateVar = IntVar()
		filenameFrame = Frame(self)
		actionsFrame = Frame(self)
		calendarFrame = Frame(actionsFrame)

		self.filenameVar= StringVar()
		self.filenameVar.set(_("No file selected"))
		self.filenameLabel = Label(filenameFrame, textvariable=self.filenameVar, wraplength=250)

		self.openButton = Button(filenameFrame, text=_("Open File"), command=self.selectFile)
		self.translateButton = Checkbutton(actionsFrame, text=_("Translate"), var=self.translateVar, command=self.updateResults)
		self.pdfButton = Button(actionsFrame, text=_("Create PDF"), command=self.createPDF)
		self.calendarButton = Button(calendarFrame, text=_("Export to calendar"), command=self.exportToCalendar)
		self.progressBar = Progressbar(calendarFrame, maximum=30)

		self.nameList = Listbox(self, width=30, height=39)
		self.resultText = Text(self, width=40, height=40)
		self.nameList.bind('<<ListboxSelect>>', self.selectName)

		self.pdfButton.pack(fill=X)
		self.calendarButton.pack(fill=X, pady=1)
		self.progressBar.pack(fill=X, pady=6)
		calendarFrame.pack()
		self.translateButton.pack()
		self.openButton.pack()
		self.filenameLabel.pack()

		self.progressBar.pack_forget()

		filenameFrame.grid(row=0, column=0, padx=10, pady=10)
		actionsFrame.grid(row=0, column=1, padx=10, pady=10)
		self.nameList.grid(row=1, column=0, sticky=(N, S, E, W))
		self.resultText.grid(row=1, column=1, sticky=(N, S, E, W))
		self.nameList.columnconfigure(1, weight=1)
		self.resultText.columnconfigure(1, weight=1)

	def __init__(self, master=None):
		Frame.__init__(self, master)
		self.pack()
		self.createWidgets()
		self.master.title(_("Rosterextractor"))
		self.master.protocol("WM_DELETE_WINDOW", self.onClose)

		self.selectedName = None
		self.lastSelectedName = None
		self.dienstplan = None
		self.pdfCreated = False

		self._loadConfig()

if __name__ == "__main__":
	if sys.platform.lower().startswith('win') and  getattr(sys, 'frozen', False):
		from util import hideConsole
		hideConsole()

	setupLocalization()

	root = Tk()
	app = Application(master=root)

	if len(sys.argv) > 1:
		app.openFile(sys.argv[1])

	app.mainloop()
	sys.exit(0)
	# root.destroy()