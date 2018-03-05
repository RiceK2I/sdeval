import csv          # package for working with csv files
import numpy as np 
import glob         # Allows us to find files
import progressbar  # Add a command-line progress bar
import re           # package for regular expressions

# Column indexes into the csv file for informatino we want to copy
PI = 2
EMAIL = 3
DEPT = 4
USERS = 16
HRS = 17
TOT = 20

# regular expression for cleaing input data
MONEY_PATTERN = re.compile(r"""
	[\$,]			# match dollar or comma char
	""", flags=re.VERBOSE)
EMAIL_PATTERN = re.compile(r"""
	(?P<id>			# start id group
		.* 			# id pattern
	) 				# end id group
	@ 				# email delimiter
	(?P<domain>		# start domain group
		.*			# domain pattern
	) 				# end domain group
	""", flags=re.VERBOSE)

# Import additiuonal search keys
PI_list = np.empty((0, 8), dtype="<U23")
with open("PI_list.csv", 'r') as csvfile:
	reader = csv.reader(csvfile)
	next(reader)

	for row in reader:
		# Each row contains 7 elemtns: [FullName, First, Last, Email, Dept, NetID, PIDM, EmployeeID]
		PI_list = np.append(PI_list, np.array(row).reshape((1,PI_list.shape[1])), axis=0)
		
# print(PI_list)

#	for i in range(0,PI_list.shape[0]):
#		print(PI_list[i,1], PI_list[i,2])

sd = np.empty((0,8), dtype="<U23")
raw = []

#bar = progressbar.ProgressBar()
for i, filename in enumerate((glob.glob("*_2017_SD.csv"))):
	raw = []
	sd = np.append(sd, np.zeros((sd.shape[0], 3), dtype="int_"), axis=1)

	with open(filename, 'r') as csvfile:
		reader = csv.reader(csvfile)
		next(reader)	# skip title row

		for row in reader:
			# extract the elements from full row that we need to save 
			row = [row[j] for j in [EMAIL, USERS, HRS, TOT]]
			# remove "," and "$" from strings
			row = [MONEY_PATTERN.sub("", word) for word in row]
			# remove "@" and emial domain from strings
			row[0] = EMAIL_PATTERN.fullmatch(row[0]).groupdict()["id"]
			try:
				ind = np.where(PI_list[:,3] == row[0])[0][0]
			except:
				raise Exception("Missing PI email in PI_list {}".format(row[0]))

			if row[0] not in sd[:,3]:
				# this is a new PI currently not in the list
				tmp = np.empty((1, 8), dtype="<U23")
				# add zeros for all prior years
				tmp = np.append(tmp, np.zeros((1, sd.shape[1]-8), dtype="int_"), axis=1)
				tmp[0, 0:8] = PI_list[ind,0:8]
				sd = np.append(sd, tmp, axis=0)

			# Now we just add the new information we just read in
			index = np.where(sd[:,3] == row[0])[0][0]
			sd[index,-3:] = row[1:]

# Pick out [FullName, First, Last, Email, Dept, NetID, PIDM, EmployeeID] 
PI = sd[:, [0, 1, 2, 3, 4, 5, 6, 7]]

# Select total number of users supported per month for each PI
PI_users_mnt = sd[:, 8::3]
PI_users_mnt = PI_users_mnt.astype("int_")
PI_users = np.average(PI_users_mnt, axis=1)

# Select total core hours computed per month for each PI
PI_hrs_mnt = sd[:, 9::3]
PI_hrs_mnt = PI_hrs_mnt.astype("float_")
PI_hrs = np.sum(PI_hrs_mnt, axis=1)

# Select total amount paid per month for each PI
PI_tot_mnt = sd[:, 10::3]
PI_tot_mnt = PI_tot_mnt.astype("float_")
PI_tot = np.sum(PI_tot_mnt, axis=1)

PI = np.append(PI, PI_users.reshape((PI.shape[0], 1)), axis=1)
PI = np.append(PI, PI_hrs.reshape((PI.shape[0], 1)), axis=1)
PI = np.append(PI, PI_tot.reshape((PI.shape[0], 1)), axis=1)

PI = PI[PI_tot.argsort()]
PI = PI[-1::-1]

core_hrs_year = PI[:, -2].astype("float_")

# Create cloud pricing tuples [Cloud_type, core_hr_cost]
AWS_OnDemand = ["AWS_OnDemand", 0.0425]
AWS_Reserved = ["AWS_Reserved", 0.015333]
GCP_Default = ["GCP_Default", 0.03545]
GCP_Sustaianed = ["GCP_Sustaianed", GCP_Default[1] * 0.4]
Azure_Default = ["Azure_Default", 0.0445]
Azure_Reserved = ["Azure_Reserved", 0.0155]
AWS_OnDemand_Total = AWS_OnDemand[1] * core_hrs_year
AWS_Reserved_Total = AWS_Reserved[1] * core_hrs_year
GCP_Default_Total = GCP_Default[1] * core_hrs_year
GCP_Sustaianed_Total = GCP_Sustaianed[1] * core_hrs_year
Azure_Default_Total = Azure_Default[1] * core_hrs_year
Azure_Reserved_Total = Azure_Reserved[1] * core_hrs_year

PI = np.append(PI, AWS_OnDemand_Total.reshape((PI.shape[0], 1)), axis=1)
PI = np.append(PI, AWS_Reserved_Total.reshape((PI.shape[0], 1)), axis=1)

PI = np.append(PI, GCP_Default_Total.reshape((PI.shape[0], 1)), axis=1)
PI = np.append(PI, GCP_Sustaianed_Total.reshape((PI.shape[0], 1)), axis=1)

PI = np.append(PI, Azure_Default_Total.reshape((PI.shape[0], 1)), axis=1)
PI = np.append(PI, Azure_Reserved_Total.reshape((PI.shape[0], 1)), axis=1)

with open("Awards_by_Calendar_Year_data.csv", 'r') as csvfile:
	reader = csv.reader(csvfile)
	next(reader)

	for row in reader:
		# Each row contains 7 elemtns: [FullName, First, Last, Email, Dept, NetID, PIDM, EmployeeID]
		PI_list = np.append(PI_list, np.array(row).reshape((1,PI_list.shape[1])), axis=0)



headers = np.array([
	"PI",
	"First",
	"Last",
	"Email",
	"DEPT",
	"NetID",
	"PIDM",
	"EmployeeID",
	"USERS",
	"HRS",
	"TOT",
	"AWS_OnDemand",
	"AWS_Reserved",
	"GCP_Default",
	"GCP_Sustaianed",
	"Azure_Default",
	"Azure_Reserved"])

PI = np.concatenate((headers.reshape((1, PI.shape[1])), PI), axis=0)

with open('Analysis.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)    # Create the writer object
            writer.writerows(PI)            # Right the sponsorData
