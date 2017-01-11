#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import subprocess
import sys

_months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
_weekdays = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")

def extractRawInfo(pdfFilename):
	try:
		rawText = subprocess.check_output(["pdftotext", "-layout", "-nopgbrk", pdfFilename, "-"])
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

def extractShifts(pdfFilename):
	month, year, lines = extractRawInfo(pdfFilename)

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

def main():

	import argparse
	from datetime import date

	parser = argparse.ArgumentParser(description='Extrahiere Schichtplaninfo')
	commandGroup = parser.add_mutually_exclusive_group()
	commandGroup.required = True
	commandGroup.add_argument("--listWorkers", "-l", action="store_true",
									help="Zeige alle Mitarbeiter an.")
	commandGroup.add_argument("--workerInfo", "-w", metavar='W', type=str,
		help="Zeige Info zu Mitarbeiter W")
	parser.add_argument("--latex", action="store_true", help="Gib Latex code aus (nur -w)")
	parser.add_argument("filename", help="Pfad zum Schichtplan PDF")


	args = parser.parse_args()
	month, year, shifts = extractShifts(args.filename)

	if args.listWorkers:
		print("\n".join(shifts.keys()))

	if args.workerInfo:
		if args.workerInfo in shifts:
			if args.latex:
				print("""\documentclass{{article}}
						\\usepackage[utf8]{{inputenc}}
						\\begin{{document}}
						\\title{{Schichtplan für {} für {} {} }}
						\\date{{}}
						\maketitle""".format(args.workerInfo, _months[month-1], year))
				print("\\begin{tabular}{rl}")
				for day, shift in enumerate(shifts[args.workerInfo], 1):
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
				print("\n".join(map(lambda x: _weekdays[date(year, month, x[0]).weekday()][0:3] + " " + (": ".join(map(str, x))), enumerate(shifts[args.workerInfo], 1))))
		else:
			print("Mitarbeiter unbekannt (nutze -l!)")


if __name__ == "__main__":
	main()