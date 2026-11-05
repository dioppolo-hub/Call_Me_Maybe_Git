from Prompt import take_prompt
from Parcer import Error


def main():
	try:
		take_prompt()
	except Error as error:
		print(error)




if __name__ == "__main__":
	main()