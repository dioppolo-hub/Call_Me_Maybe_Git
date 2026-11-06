import sys


class Error(Exception):
	pass


def parce_prompt():
	prompt_list: list[str] = sys.argv
	if "--input" not in prompt_list:
		input_path = "data/input/function_calling_tests.json"
	i = 0
	for _ in prompt_list:
		if prompt_list[i].startswith("--input"):
			input_path = prompt_list[i + 1]
		i += 1
	with open(input_path) as f:
		lines = f.readlines()
	last_line = len(lines)
	for j, line in enumerate(lines):
		j += 1
		print(j, line)
		if j == 1 and line != "[":
			raise Error(
				f"[ERROR], line {j}, prompt "
				"does not follow .json standard"
				)
		if line.lstrip().startswith('"prompt"'):
			if lines[j - 1] != "{":
				raise Error(
					f"[ERROR], line {j - 1}, prompt "
					"does not follow .json standard"
				)
			if lines[j + 1] != "},":
				raise Error(
					f"[ERROR], line {j + 1}, prompt "
					"does not follow .json standard"
				)
			prompt = line.split(":")[1]
			if not prompt or not isinstance(prompt, str):
				raise Error(
					f"[ERROR], line {j}, prompt "
					"is not a valid string"
				)
		elif line.lstrip().startswith("{"):
			continue
		elif line.lstrip().startswith("},"):
			continue
		elif j == last_line and not line.lstrip().startswith("]"):
			raise Error(
				f"[ERROR], line {j}, prompt "
				"does not follow .json standard"
			)
		else:
			raise Error(
				f"[ERROR], line {j}, input "
				"value is not a prompt"
			)

