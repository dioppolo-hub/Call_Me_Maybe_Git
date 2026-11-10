from Parcer import Error, Parcer
import sys


def main():
	try:
		parce = Parcer()
		prompt, function = parce.parce()
	except Error as error:
		print(error)




if __name__ == "__main__":
	main()