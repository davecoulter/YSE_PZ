import os
import time
from slackclient import SlackClient
import TNS_Synopsis

# constants
SLACK_BOT_TOKEN="xoxb-122297221971-0W2RXCRa5Sm6yekdDPDeAc4H"
BOT_NAME = "tns_update"
BOT_ID = "U3L8R6HUK"
AT_BOT = "<@" + BOT_ID + ">"
COMMAND = "do"
JOKE = "open the pod bay doors"
READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose

def get_username_by_id(user_id):
	username = None

	api_call = slack_client.api_call("users.list")

	if api_call.get('ok'):
		# retrieve all users so we can find our bot
		users = api_call.get('members')
		user_match = [u for u in users if user_id and u['id'] == user_id]

		if user_match and len(user_match) > 0:
			username = user_match[0]['name']

	return username

def handle_command(command, channel, username=None):
	"""
	Receives commands directed at the bot and determines if they
	are valid commands. If so, then acts on the commands. If not,
	returns back what it needs for clarification.
	"""
	response = "I don't know how to do that.\n\nUse the *" + COMMAND + "* command."
	if command.startswith(COMMAND):
		response = ""
		try:
			slack_client.api_call("chat.postMessage", channel=channel, text="Working...", as_user=True)

			TNS_Synopsis.ProcessTNSEmails()
			with open("TNS_Outputs.txt") as f:
				files = f.read()
				fnames = files.split(",")

				file_to_open = fnames[0]

				print(file_to_open)

				with open(file_to_open) as f1:
					response = f1.read()

				response = "...Nothing to report." if response == "" else (response+"\n\n...Done.")
				print(response)

		except Exception as e:
			response = e.args
	elif command.lower().startswith(JOKE):

		uname = "Dave" if not username else "@"+username
		response = ("I'm sorry %s. I can't do that." % uname)

	slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
	"""
	    The Slack Real Time Messaging API is an events firehose.
	    this parsing function returns None unless a message is
	    directed at the Bot, based on its ID.
	"""
	output_list = slack_rtm_output
	# print(output_list)
	if output_list and len(output_list) > 0:

		for output in output_list:
			# Parse user output
			if output and 'text' in output and AT_BOT in output['text']:

				# User is actually slack user id
				username = get_username_by_id(output['user'])

				# return text after the @ mention, whitespace removed
				return output['text'].split(AT_BOT)[1].strip().lower(), output['channel'], username

			elif output and 'content' in output and 'IFTTT (bot): @tns_update do' in output['content']:
				return 'do', output['channel'], None

	return None, None, None


if __name__ == "__main__":
	# execute only if run as a script
	slack_client = SlackClient(SLACK_BOT_TOKEN)

	if slack_client.rtm_connect():
		print("@<%s> connected and running!" % BOT_NAME)
		while True:
			command, channel, username = parse_slack_output(slack_client.rtm_read())

			if command and channel:
				handle_command(command, channel, username)

			time.sleep(READ_WEBSOCKET_DELAY)
	else:
		print("Connection failed. Invalid Slack token or bot ID?")