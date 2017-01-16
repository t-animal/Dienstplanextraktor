#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import subprocess

from tkinter import *
import tkinter.filedialog as filedialog

from datetime import date
from dienstplan import Dienstplan
from util import _PDFLATEX

class Application(Frame):
	def createPDF(self):
		if self.dienstplan and self.selectedName:
			latex = self.dienstplan.getLatex(self.selectedName, self.translateVar.get() == 1)

			curDir = os.path.dirname(os.path.abspath(__file__))
			pdflatex = subprocess.Popen([_PDFLATEX, "-jobname=Dienstplan-"+ str(self.dienstplan.year) + "-" + str(self.dienstplan.month), "--"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			(stdout, stderr) = pdflatex.communicate(latex.encode('utf8'))


	def exportToCalendar(self):
		self.resultText.delete(1.0, END)

		if self.dienstplan and self.selectedName:
			for day, event in enumerate(self.dienstplan.addToCalendar(self.selectedName, self.translateVar.get() == 1), 1):
				self.resultText.delete(1.0, END)
				self.resultText.insert(END, "Adding to google calendar... Event no {}\n".format(day))
				self.update_idletasks()

			self.resultText.insert(END, "Done")

	def selectFile(self):
		filename = filedialog.askopenfilename(filetypes=[("Schichtpläne", "SPX*.pdf"), ("Alle PDF Dateien", "*.pdf")])
		self.filenameVar.set(filename)

		self.selectedName = None
		self.dienstplan = None
		self.resultText.delete(1.0, END)
		self.nameList.delete(0, END)

		if not filename == "":
			self.dienstplan = Dienstplan(filename)
			self.nameList.insert(END, *self.dienstplan.shifts.keys())

	def selectName(self, event):
		w = event.widget
		index = int(w.curselection()[0])
		self.selectedName = w.get(index)

		self.resultText.delete(1.0, END)
		self.resultText.insert(END, self.dienstplan.getText(self.selectedName, self.translateVar.get() == 1))

	def createWidgets(self):
		self.translateVar = IntVar()
		filenameFrame = Frame(self)
		actionsFrame = Frame(self)

		self.filenameVar= StringVar()
		self.filenameVar.set("No file selected")
		self.filenameLabel = Label(filenameFrame, textvariable=self.filenameVar, wraplength=250)

		self.openButton = Button(filenameFrame, text="Open File", command=self.selectFile)
		self.translateButton = Checkbutton(actionsFrame, text="Translate", var=self.translateVar)
		self.pdfButton = Button(actionsFrame, text="Create PDF", command=self.createPDF)
		self.calendarButton = Button(actionsFrame, text="Export to calendar", command=self.exportToCalendar)

		self.nameList = Listbox(self, width=30, height=39)
		self.resultText = Text(self, width=40, height=40)
		self.nameList.bind('<<ListboxSelect>>', self.selectName)

		self.pdfButton.pack(fill=X)
		self.calendarButton.pack(fill=X)
		self.translateButton.pack()
		self.openButton.pack()
		self.filenameLabel.pack()

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

		self.selectedName = None
		self.dienstplan = None

if __name__ == "__main__":
	root = Tk()
	app = Application(master=root)
	app.mainloop()
	# root.destroy()