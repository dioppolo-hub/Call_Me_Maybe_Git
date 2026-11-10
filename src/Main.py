from Prompt import take_prompt
from Parcer import Error, Parcer
import sys


def main():
	try:
		parce = Parcer()
		parce.parce_prompt()
	except Error as error:
		print(error)




if __name__ == "__main__":
	main()