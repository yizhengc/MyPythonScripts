
# This function only accept YYYY-MM-DD format
def GetDatetimeFromString(dateString) :
	subTokens = dateString.split('-')
	if len(subToksn) != 3:
		raise NameError('Input string is a invalid date string: ' + dateString)
	else:
		return datetime.date(subTokens[0], subTokens[1], subTokens[2])