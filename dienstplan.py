#!/usr/bin/python
# encoding: utf-8

import calendar
import gettext
import re
import subprocess
import sys
import os

from calendarConnection import insertEvent
from calendar import monthrange
from datetime import date
from util import _PDFTOTEXT, _LAYOUT_PARAM, setupLocalization

def translateAble_(string):return string
_german_months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
_months = calendar.month_name
_weekdays = calendar.day_name
_translationMatrix = {
	"0": translateAble_("Free "),
	"U": translateAble_("Vacation "),
	"F": translateAble_("Morning shift "),
	"S": translateAble_("Evening shift "),
	"N": translateAble_("Night shift ")
}

class PlausibilityError(RuntimeWarning):

	pass

class Dienstplan:

	def __init__(self, pdfFilename, useSecondLine=False):
		self.pdfFilename = pdfFilename
		self.warnings = {}
		self.month, self.year, self.shifts = self._extractShifts(useSecondLine)

	def _extractRawInfo(self):
		try:
			rawText = subprocess.check_output([_PDFTOTEXT, _LAYOUT_PARAM, "-nopgbrk", self.pdfFilename, "-"], universal_newlines=True)
		except subprocess.CalledProcessError as e:
			if e.returncode == 1:
				print(_("There was an error opening the PDF file."))
			elif e.returncode == 3:
				print(_("There was an error related to PDF permissions."))
			else:
				print(_("An unknown error occured."))
			sys.exit(1)

		dateInfo = re.search(r"(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) *([0-9]{4})", rawText).group()
		month = dateInfo[:-4].strip()
		year = dateInfo[-4:].strip()

		rawText = list(filter(lambda x: x != "" and year not in x, rawText.split("\n")))

		return _german_months.index(month) + 1, int(year), rawText

	def _extractShifts(self, useSecondLine=False):
		month, year, lines = self._extractRawInfo()

		expectedDays = monthrange(year, month)[1]

		shifts = {}
		curWorkerName = ""
		curShifts = []
		self.warnings = {}

		lineOffset = 1 if useSecondLine else 0

		for lineno, line in enumerate(lines):
			if lineno % 2 == lineOffset:
				if curWorkerName.strip(" ") in shifts:
					break

				if curWorkerName != "":
					shifts[curWorkerName.strip(" ")] = curShifts

					if len(curShifts) != expectedDays:
						import warnings
						warningText = _("Number of shifts ({}) of {} does not match number of days ({}) in month ({})!").\
										format(len(curShifts), curWorkerName, expectedDays, month)
						self.warnings[curWorkerName.strip(" ")] = PlausibilityError(warningText)
						warnings.warn(warningText, PlausibilityError)

				curWorkerName = ""
				curShifts = []


			tokens = [token for token in line.split(" ") if token != ""]
			curWorkerName = tokens[0] + " " + curWorkerName
			if not len(tokens[1:]) == 0:
				#extract shift information only, if information is present
				curShifts = tokens[1:]

		return month, year, shifts


	def _translateShiftName(self, origShiftName):
		for length in range(1, len(origShiftName)+1):
			if origShiftName[:length] in _translationMatrix:
				return _(_translationMatrix[origShiftName[:length]]) + origShiftName[length:]

		return origShiftName

	def getText(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			daysShifts = enumerate(map(self._translateShiftName, self.shifts[name]), 1)
		else:
			daysShifts = enumerate(self.shifts[name], 1)
		return _("Roster of {} for {} {}\n").format(name, _months[self.month], self.year) + \
				"\n".join(map(lambda x: _weekdays[date(self.year, self.month, x[0]).weekday()][0:3]
											+ " " + (": ".join(map(str, x))), daysShifts))

	def getLatex(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			daysShifts = enumerate(map(self._translateShiftName, self.shifts[name]), 1)
		else:
			daysShifts = enumerate(self.shifts[name], 1)
		result = """
\\documentclass{{article}}
\\usepackage[table]{{xcolor}}
\\usepackage[utf8]{{inputenc}}
\\definecolor{{weekend}}{{rgb}}{{0.85,0.85,0.85}}
\\begin{{document}}
	\\title{{{} {} {} {} {} }}
	\\date{{}}
	\maketitle

	\\begin{{table}}[h]
		\centering
		\\begin{{tabular}}{{ | r @{{\hspace{{1.8mm}}}} r l | }}
			\\hline\n""".format(_("Roster of"), name, _("for"), _months[self.month], self.year)

		for day, shift in daysShifts:
			weekday = date(self.year, self.month, day).weekday()
			result += "\t\t\t\t"
			if weekday in [5, 6]:
				result += "\\rowcolor{{weekend}}\\textbf{{{}}},\t& \\textbf{{{}}}".format(_weekdays[weekday], day)
			else:
				result += "{},\t& {}".format(_weekdays[weekday], day)

			result += "\t& {}\\\\\n".format(shift)
		result += """
			\\hline
		\\end{tabular}
	\\end{table}
\\end{document}"""

		return result

	def getShifts(self, name, translate=False):
		if name not in self.shifts:
			raise KeyError()

		if translate:
			return list(map(self._translateShiftName, self.shifts[name]))
		else:
			return self.shifts[name]

	def hasWarning(self, name):
		return name in self.warnings

	def getWarning(self, name):
		return self.warnings[name]

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

	parser = argparse.ArgumentParser(description=_('Extract roster info'))
	commandGroup = parser.add_mutually_exclusive_group()
	commandGroup.required = True
	commandGroup.add_argument("--listWorkers", "-l", action="store_true",
									help=_("Show all workers."))
	commandGroup.add_argument("--workerInfo", "-w", metavar='W', type=str,
		help=_("Show infos for worker W"))
	parser.add_argument("--latex", action="store_true", help=_("Output latex code (only -w)"))
	parser.add_argument("--translate", action="store_true", help=_("Unshorten abbreviations (only -w)"))
	parser.add_argument("--calendar", action="store_true", help=_("Save to google calendar (only -w)"))
	parser.add_argument("--secondLine", action="store_true", help=_("Extract every second line (use, if desired name is cut off)"))
	parser.add_argument("filename", help=_("Path to roster PDF"))

	args = parser.parse_args()
	plan = Dienstplan(args.filename, args.secondLine)

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
					print(_("Adding to google calendar... Event no {}").format(day), end="\r")

				print(_("Done"))

		else:
			print(_("Unknown worker (use -l!)"))


if __name__ == "__main__":
	import locale
	setupLocalization()
	main()
