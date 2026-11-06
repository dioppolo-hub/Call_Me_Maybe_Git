from Prompt import take_prompt
from Parcer import Error, parce_prompt


def main():
	try:
		parce_prompt()
	except Error as error:
		print(error)




if __name__ == "__main__":
	main()