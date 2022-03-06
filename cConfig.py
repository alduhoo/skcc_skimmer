import sys
import getopt

from typing  import Any, Literal, NoReturn

from cCommon import cCommon

class cConfig:
	class cProgressDots:
		ENABLED:         bool
		DISPLAY_SECONDS: int
		DOTS_PER_LINE:   int
	PROGRESS_DOTS = cProgressDots()

	class cLogFile:
		FILE_NAME:         str
		ENABLED:           bool
		LOG_FILE:          str
		DELETE_ON_STARTUP: bool
	LOG_FILE = cLogFile()

	class cHighWpm:
		ACTION:    Literal['suppress', 'warn', 'always-display']
		THRESHOLD: int
	HIGH_WPM = cHighWpm

	class cOffFrequency:
		ACTION:    Literal['suppress', 'warn']
		TOLERANCE: int
	OFF_FREQUENCY = cOffFrequency()

	class cSked:
		ENABLED:       bool
		CHECK_SECONDS: int
	SKED = cSked

	class cNotification:
		ENABLED:                      bool
		CONDITION:                    Literal['goals', 'targets', 'friends']
		RENOTIFICATION_DELAY_SECONDS: int
	NOTIFICATION = cNotification


	MY_CALLSIGN:              str
	ADI_FILE:                 str
	MY_GRIDSQUARE:            str
	GOALS:                    list[str]
	TARGETS:                  list[str]
	BANDS:                    list[int]
	FRIENDS:                  list[str]
	EXCLUSIONS:               list[str]
	DISTANCE_UNITS:           int
	SPOT_PERSISTENCE_MINUTES: int
	VERBOSE:                  bool
	LOG_BAD_SPOTS:            bool

	configFile: dict[str, Any]

	def __init__(self, ArgV: list[str]):
		def ReadSkccSkimmerCfg() -> dict[str, Any]:
			try:
				with open('skcc_skimmer.cfg', 'r', encoding='utf-8') as File:
					ConfigFileString = File.read()
					exec(ConfigFileString)
			except IOError:
				print("Unable to open configuration file 'skcc_skimmer.cfg'.")
				sys.exit()

			return locals()

		self.configFile = ReadSkccSkimmerCfg()

		if 'MY_CALLSIGN' in self.configFile:
			self.MY_CALLSIGN = self.configFile['MY_CALLSIGN']

		if 'ADI_FILE' in self.configFile:
			self.ADI_FILE = self.configFile['ADI_FILE']

		if 'MY_GRIDSQUARE' in self.configFile:
			self.MY_GRIDSQUARE = self.configFile['MY_GRIDSQUARE']

		if 'GOALS' in self.configFile:
			self.GOALS = self.configFile['GOALS']

		if 'TARGETS' in self.configFile:
			self.TARGETS = self.configFile['TARGETS']

		if 'BANDS' in self.configFile:
			self.BANDS = [int(Band)  for Band in cCommon.Split(self.configFile['BANDS'])]

		if 'FRIENDS' in self.configFile:
			self.FRIENDS = [friend  for friend in cCommon.Split(self.configFile['FRIENDS'])]

		if 'EXCLUSIONS' in self.configFile:
			self.EXCLUSIONS = [friend  for friend in cCommon.Split(self.configFile['EXCLUSIONS'])]

		if 'LOG_FILE' in self.configFile:
			logFile = self.configFile['LOG_FILE']

			if 'ENABLED' in logFile:
				self.LOG_FILE.ENABLED = logFile['ENABLED']

			if 'FILE_NAME' in logFile:
				self.LOG_FILE.FILE_NAME = logFile['FILE_NAME']

			if 'DELETE_ON_STARTUP' in logFile:
				self.LOG_FILE.DELETE_ON_STARTUP = logFile['DELETE_ON_STARTUP']

		if 'SKED' in self.configFile:
			sked = self.configFile['SKED']

			if 'ENABLED' in sked:
				self.SKED.ENABLED = sked['ENABLED']

			if 'CHECK_SECONDS' in sked:
				self.SKED.ENABLED = sked['CHECK_SECONDS']

		if 'OFF_FREQUENCY' in self.configFile:
			offFrequency = self.configFile['OFF_FREQUENCY']

			if 'ACTION' in offFrequency:
				self.OFF_FREQUENCY.ACTION = offFrequency['ACTION']

			if 'TOLERANCE' in offFrequency:
				self.OFF_FREQUENCY.TOLERANCE = offFrequency['TOLERANCE']

		if 'HIGH_WPM' in self.configFile:
			highWpm = self.configFile['HIGH_WPM']

			if 'ACTION' in highWpm:
				self.HIGH_WPM.ACTION = highWpm['ACTION']

			if 'THRESHOLD' in highWpm:
				self.HIGH_WPM.THRESHOLD = highWpm['THRESHOLD']

		if 'VERBOSE' in self.configFile:
			self.VERBOSE = bool(self.configFile['VERBOSE'])
		else:
			self.VERBOSE = False

		if 'LOG_BAD_SPOTS' in self.configFile:
			self.LOG_BAD_SPOTS = self.configFile['LOG_BAD_SPOTS']
		else:
			self.LOG_BAD_SPOTS = False

		self.ParseArgs(ArgV)

		self.ValidateConfig()

	def ParseArgs(self, ArgV: list[str]):
		try:
			Options, _ = getopt.getopt(ArgV, \
					'a:   b:     B:           c:        d:              g:     h    i           l:       m:          n:            r:      s:    t:       v'.replace(' ', ''), \
					'adi= bands= brag-months= callsign= distance-units= goals= help interactive logfile= maidenhead= notification= radius= sked= targets= verbose'.split())
		except getopt.GetoptError as e:
			print(e)
			self.Usage()

		self.INTERACTIVE = False

		for Option, Arg in Options:
			if Option in ('-a', '--adi'):
				self.ADI_FILE = Arg

			elif Option in ('-b', '--bands'):
				self.BANDS = [int(Band)  for Band in cCommon.Split(Arg)]

			elif Option in ('-B', '--brag-months'):
				self.BRAG_MONTHS = int(Arg)

			elif Option in ('-c', '--callsign'):
				self.MY_CALLSIGN = Arg.upper()

			elif Option in ('-d', '--distance-units'):
				argLower = Arg.lower()

				if Arg not in ('mi', 'km'):
					print("DISTANCE_UNITS option must be either 'mi' or 'km'.")
					sys.exit()

				self.DISTANCE_UNITS = int(argLower)

			elif Option in ('-g', '--goals'):
				self.GOALS = self.Parse(Arg,   'C CXN T TXN S SXN WAS WAS-C WAS-T WAS-S P BRAG K3Y', 'goal')

			elif Option in ('-h', '--help'):
				self.Usage()

			elif Option in ('-i', '--interactive'):
				self.INTERACTIVE = True

			elif Option in ('-l', '--logfile'):
				self.LOG_FILE.ENABLED           = True
				self.LOG_FILE.DELETE_ON_STARTUP = True
				self.LOG_FILE.FILE_NAME         = Arg

			elif Option in ('-m', '--maidenhead'):
				self.MY_GRIDSQUARE = Arg

			elif Option in ('-n', '--notification'):
				Arg = Arg.lower()

				if Arg not in ('on', 'off'):
					print("Notificiation option must be either 'on' or 'off'.")
					sys.exit()

				self.NOTIFICATION.ENABLED = Arg == 'on'

			elif Option in ('-r', '--radius'):
				self.SPOTTER_RADIUS = int(Arg)

			elif Option in ('-s', '--sked'):
				Arg = Arg.lower()

				if Arg not in ('on', 'off'):
					print("SKED option must be either 'on' or 'off'.")
					sys.exit()

				self.SKED.ENABLED = Arg == 'on'

			elif Option in ('-t', '--targets'):
				self.TARGETS = self.Parse(Arg, 'C CXN T TXN S SXN', 'target')

			elif Option in ('-v', '--verbose'):
				self.VERBOSE = True


	def ValidateConfig(self):
		#
		# MY_CALLSIGN can be defined in skcc_skimmer.cfg.  It is not required
		# that it be supplied on the command line.
		#
		if not self.MY_CALLSIGN:
			print("You must specify your callsign, either on the command line or in 'skcc_skimmer.cfg'.")
			print('')
			self.Usage()

		if not self.ADI_FILE:
			print("You must supply an ADI file, either on the command line or in 'skcc_skimmer.cfg'.")
			print('')
			self.Usage()

		if not self.GOALS and not self.TARGETS:
			print('You must specify at least one goal or target.')
			sys.exit()

		if not self.MY_GRIDSQUARE:
			print("'MY_GRIDSQUARE' in skcc_skimmer.cfg must be a 4 or 6 character maidenhead grid value.")
			sys.exit()

		if 'SPOTTER_RADIUS' not in self.configFile:
			print("'SPOTTER_RADIUS' must be defined in skcc_skimmer.cfg.")
			sys.exit()

		if 'QUALIFIERS' in self.configFile:
			print("'QUALIFIERS' is no longer supported and can be removed from 'skcc_skimmer.cfg'.")
			sys.exit()

		if 'NEARBY' in self.configFile:
			print("'NEARBY' has been replaced with 'SPOTTERS_NEARBY'.")
			sys.exit()

		if 'SPOTTER_PREFIXES' in self.configFile:
			print("'SPOTTER_PREFIXES' has been deprecated.")
			sys.exit()

		if 'SPOTTERS_NEARBY' in self.configFile:
			print("'SPOTTERS_NEARBY' has been deprecated.")
			sys.exit()

		if 'SKCC_FREQUENCIES' in self.configFile:
			print("'SKCC_FREQUENCIES' is now caluclated internally.  Remove it from 'skcc_skimmer.cfg'.")
			sys.exit()

		if 'HITS_FILE' in self.configFile:
			print("'HITS_FILE' is no longer supported.")
			sys.exit()

		if 'HitCriteria' in self.configFile:
			print("'HitCriteria' is no longer supported.")
			sys.exit()

		if 'StatusCriteria' in self.configFile:
			print("'StatusCriteria' is no longer supported.")
			sys.exit()

		if 'SkedCriteria' in self.configFile:
			print("'SkedCriteria' is no longer supported.")
			sys.exit()

		if 'SkedStatusCriteria' in self.configFile:
			print("'SkedStatusCriteria' is no longer supported.")
			sys.exit()

		if 'SERVER' in self.configFile:
			print('SERVER is no longer supported.')
			sys.exit()

		if 'SPOT_PERSISTENCE_MINUTES' not in self.configFile:
			self.SPOT_PERSISTENCE_MINUTES = 15

		if 'GOAL' in self.configFile:
			print("'GOAL' has been replaced with 'GOALS' and has a different syntax and meaning.")
			sys.exit()

		if 'GOALS' not in self.configFile:
			print("GOALS must be defined in 'skcc_skimmer.cfg'.")
			sys.exit()

		if 'TARGETS' not in self.configFile:
			print("TARGETS must be defined in 'skcc_skimmer.cfg'.")
			sys.exit()

		if 'HIGH_WPM' not in self.configFile:
			print("HIGH_WPM must be defined in 'skcc_skimmer.cfg'.")
			sys.exit()

		if self.HIGH_WPM.ACTION not in ('suppress', 'warn', 'always-display'):
			print("HIGH_WPM['ACTION'] must be one of ('suppress', 'warn', 'always-display')")
			sys.exit()

		if 'OFF_FREQUENCY' not in self.configFile:
			print("OFF_FREQUENCY must be defined in 'skcc_skimmer.cfg'.")
			sys.exit()

		if self.OFF_FREQUENCY.ACTION not in ('suppress', 'warn'):
			print("OFF_FREQUENCY['ACTION'] must be one of ('suppress', 'warn')")
			sys.exit()

	def Usage(self) -> NoReturn:
		print('Usage:')
		print('')
		print('   skcc_skimmer.py')
		print('                   [--adi <adi-file>]')
		print('                   [--bands <comma-separated-bands>]')
		print('                   [--brag-months <number-of-months-back>]')
		print('                   [--callsign <your-callsign>]')
		print('                   [--goals <goals>]')
		print('                   [--help]')
		print('                   [--interactive]')
		print('                   [--logfile <logfile-name>]')
		print('                   [--maidenhead <grid-square>]')
		print('                   [--notification <on|off>]')
		print('                   [--radius <distance-in-miles>]')
		print('                   [--targets <targets>]')
		print('                   [--verbose]')
		print(' or...')
		print('')
		print('   skcc_skimmer.py')
		print('                   [-a <adi-file>]')
		print('                   [-b <comma-separated-bands>]')
		print('                   [-c <your-callsign>]')
		print('                   [-g <goals>]')
		print('                   [-h]')
		print('                   [-i]')
		print('                   [-l <logfile-name>]')
		print('                   [-m <grid-square>]')
		print('                   [-n <on|off>]')
		print('                   [-r <distance-in-miles>]')
		print('                   [-t <targets>]')
		print('                   [-v]')
		print('')
		sys.exit()

	def Parse(self, String: str, ALL_str: str, Type: str) -> list[str]:
		ALL: list[str] = ALL_str.split()
		List = cCommon.Split(String.upper())

		for x in List:
			if x == 'ALL':
				return ALL

			if x == 'NONE':
				return []

			if x == 'CXN' and 'C' not in List:
				List.append('C')

			if x == 'TXN' and 'T' not in List:
				List.append('T')

			if x == 'SXN' and 'S' not in List:
				List.append('S')

			if x not in ALL:
				print(f"Unrecognized {Type} '{x}'.")
				sys.exit()

		return List