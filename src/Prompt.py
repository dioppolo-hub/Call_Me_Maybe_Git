import sys
from llm_sdk.llm_sdk import Small_LLM_Model

def take_prompt():
	prompt_list: list[str] = sys.argv
	model = Small_LLM_Model()
	if "--input" not in prompt_list:
		input_path = "data/input/function_calling_tests.json"
	i = 0
	for _ in prompt_list:
		if prompt_list[i].startswith("--input"):
			input_path = prompt_list[i + 1]
		i += 1
	with open(input_path) as f:
		for line in f:
			if line.lstrip().startswith('"prompt"'):
				prompt = line.split(":")[1]
				tensor = model.encode(prompt)
				print(tensor)