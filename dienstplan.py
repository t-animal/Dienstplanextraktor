#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import subprocess
import sys
import os

_months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
_weekdays = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
_translationMatrix = {
	"0": "Frei ",
	"U": "Urlaub ",
	"F": "Frühschicht ",
	"S": "Spätschicht ",
	"N": "Nachtschicht "
}

def extractRawInfo(pdfFilename):
	try:
		curDir = os.path.dirname(os.path.abspath(__file__))
		rawText = subprocess.check_output([curDir + "/dependencies/pdftotext", "-layout", "-nopgbrk", pdfFilename, "-"])
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

def extractShifts(pdfFilename, translate=False):
	month, year, lines = extractRawInfo(pdfFilename)

	shifts = {}
	curWorkerName = ""
	curShifts = []

	def translateShiftName(origShiftName):
		for length in range(1, len(origShiftName)+1):
			if origShiftName[:length] in _translationMatrix:
				return _translationMatrix[origShiftName[:length]] + origShiftName[length:]

		return origShiftName

	for line in lines:
		if line == "":
			if curWorkerName.strip(" ") in shifts:
				break

			if curWorkerName != "":
				if translate:
					curShifts = map(translateShiftName, curShifts)
				shifts[curWorkerName.strip(" ")] = curShifts

			curWorkerName = ""
			curShifts = []
			continue

		tokens = [token for token in line.split(" ") if token != ""]
		curWorkerName = tokens[0] + " " + curWorkerName
		curShifts = tokens[1:]

	return month, year, shifts

def main():

	import argparse
	from datetime import date
	from calendarConnection import insertEvent

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
	month, year, shifts = extractShifts(args.filename, args.translate)

	if args.listWorkers:
		print("\n".join(shifts.keys()))

	if args.workerInfo:
		if args.workerInfo in shifts:
			daysShifts = list(enumerate(shifts[args.workerInfo], 1))
			if args.latex:
				print("""\documentclass{{article}}
						\\usepackage[utf8]{{inputenc}}
						\\begin{{document}}
						\\title{{Schichtplan für {} für {} {} }}
						\\date{{}}
						\maketitle""".format(args.workerInfo, _months[month-1], year))
				print("\\begin{tabular}{rl}")
				for day, shift in daysShifts:
					weekday = date(year, month, day).weekday()
					if weekday in [5, 6]:
						print("\\textbf{", end="")

					print("{}, {}".format(_weekdays[weekday], day), end="")

					if weekday in [5, 6]:
						print("}", end="")

					print("& {}".format(shift))

					print("\\\\")
				print("\\end{tabular}\\end{document}")
			else:
				print("Schichtplan für {} für {} {}".format(args.workerInfo, _months[month-1], year))
				print("\n".join(map(lambda x: _weekdays[date(year, month, x[0]).weekday()][0:3] + " " + (": ".join(map(str, x))), daysShifts)))


			if args.calendar:
				for day, shift in daysShifts:
					print("Adding to google calendar... Event no {}".format(day), end="\r")
					insertEvent(year, month, day, shift)
				print("\nDone")

		else:
			print("Mitarbeiter unbekannt (nutze -l!)")


if __name__ == "__main__":
	main()