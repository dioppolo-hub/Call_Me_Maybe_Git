from Parcer import Error, Parcer
from llm_sdk import Small_LLM_Model
import sys


def main():
	try:
		parce = Parcer()
		prompt, function = parce.parce()
		for p in function:
			print(p)
	except Error as error:
		print(error)




if __name__ == "__main__":
	main()