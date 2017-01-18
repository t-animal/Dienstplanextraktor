#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import subprocess
import sys
import os

from calendarConnection import insertEvent
from datetime import date
from util import _PDFTOTEXT, _LAYOUT_PARAM

_months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
_weekdays = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
_translationMatrix = {
	"0": "Frei ",
	"U": "Urlaub ",
	"F": "Frühschicht ",
	"S": "Spätschicht ",
	"N": "Nachtschicht "
}

class Dienstplan:

	def __init__(self, pdfFilename):
		self.pdfFilename = pdfFilename
		self.month, self.year, self.shifts = self._extractShifts()

	def _extractRawInfo(self):
		try:
			rawText = subprocess.check_output([_PDFTOTEXT, _LAYOUT_PARAM, "-nopgbrk", self.pdfFilename, "-"], universal_newlines=True)
		except subprocess.CalledProcessError as e:
			if e.returncode == 1:
				print("There was an error opening the PDF file.")
			elif e.returncode == 3:
				print("There was an error related to PDF permissions.")
			else:
				print("An unknown error occured.")
			sys.exit(1)

		rawText = str(rawText, encoding='UTF-8')

		dateInfo = re.search(r"(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) +([0-9]{4})", rawText).group()
		dateInfo = dateInfo.split(" ")
		month = dateInfo[0]
		year = dateInfo[-1]

		rawText = [ "" if year in line else line for line in rawText.split("\n") ]

		return _months.index(month) + 1, int(year), rawText

	def _extractShifts(self):
		month, year, lines = self._extractRawInfo()

		shifts = {}
		curWorkerName = ""
		curShifts = []

		for line in lines:
			if line == "":
				if curWorkerName.strip(" ") in shifts:
					break

				if curWorkerName != "":
					shifts[curWorkerName.strip(" ")] = curShifts

				curWorkerName = ""
				curShifts = []
				continue

			tokens = [token for token in line.split(" ") if token != ""]
			curWorkerName = tokens[0] + " " + curWorkerName
			curShifts = tokens[1:]

		return month, year, shifts


	def _translateShiftName(self, origShiftName):
		for length in range(1, len(origShiftName)+1):
			if origShiftName[:length] in _translationMatrix:
				return _translationMatrix[origShiftName[:length]] + origShiftName[length:]

		return origShiftName

	def getText(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			daysShifts = enumerate(map(self._translateShiftName, self.shifts[name]), 1)
		else:
			daysShifts = enumerate(self.shifts[name], 1)
		return "Schichtplan für {} für {} {}\n".format(name, _months[self.month - 1], self.year) + \
				"\n".join(map(lambda x: _weekdays[date(self.year, self.month, x[0]).weekday()][0:3]
											+ " " + (": ".join(map(str, x))), daysShifts))

	def getLatex(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			daysShifts = enumerate(map(self._translateShiftName, self.shifts[name]), 1)
		else:
			daysShifts = enumerate(self.shifts[name], 1)
		result = """\documentclass{{article}}
						\\usepackage[utf8]{{inputenc}}
						\\begin{{document}}
						\\title{{Schichtplan für {} für {} {} }}
						\\date{{}}
						\maketitle\n""".format(name, _months[self.month - 1], self.year)
		result += "\\begin{tabular}{rl}\n"

		for day, shift in daysShifts:
			weekday = date(self.year, self.month, day).weekday()
			if weekday in [5, 6]:
				result += "\\textbf{"

			result += "{}, {}".format(_weekdays[weekday], day)

			if weekday in [5, 6]:
				result += "}"

			result += "& {}\n".format(shift)

			result += "\\\\\n"
		result += "\\end{tabular}\\end{document}"

		return result

	def getShifts(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			return list(map(self._translateShiftName, self.shifts[name]))
		else:
			return self.shifts[name]


	def addToCalendar(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			daysShifts = enumerate(map(self._translateShiftName, self.shifts[name]), 1)
		else:
			daysShifts = enumerate(self.shifts[name], 1)
		for day, shift in daysShifts:
			yield insertEvent(self.year, self.month, day, shift)

def main():

	import argparse

	parser = argparse.ArgumentParser(description='Extrahiere Schichtplaninfo')
	commandGroup = parser.add_mutually_exclusive_group()
	commandGroup.required = True
	commandGroup.add_argument("--listWorkers", "-l", action="store_true",
									help="Zeige alle Mitarbeiter an.")
	commandGroup.add_argument("--workerInfo", "-w", metavar='W', type=str,
		help="Zeige Info zu Mitarbeiter W")
	parser.add_argument("--latex", action="store_true", help="Gib Latex code aus (nur -w)")
	parser.add_argument("--translate", action="store_true", help="Übersetze Abkürzungen (nur -w)")
	parser.add_argument("--calendar", action="store_true", help="Speichere in Google Calendar (nur -w)")
	parser.add_argument("filename", help="Pfad zum Schichtplan PDF")


	args = parser.parse_args()
	plan = Dienstplan(args.filename)

	if args.listWorkers:
		print("\n".join(plan.shifts.keys()))

	if args.workerInfo:
		if args.workerInfo in plan.shifts:
			if args.latex:
				print(plan.getLatex(args.workerInfo))
			else:
				print(plan.getText(args.workerInfo))

			if args.calendar:
				for day, event in enumerate(plan.addToCalendar(args.workerInfo), 1):
					print("Adding to google calendar... Event no {}".format(day), end="\r")

				print("Done")

		else:
			print("Mitarbeiter unbekannt (nutze -l!)")


if __name__ == "__main__":
	main()