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
		if j == 0:
			if line.strip() != "[":
				raise Error(
					f"[ERROR], line {j}, prompt "
					"does not follow .json standard"
					)
			else:
				continue
		if line.lstrip().startswith('"prompt"'):
			if lines[j - 1].strip() != "{":
				raise Error(
					f"[ERROR], line {j - 1}, prompt "
					"does not follow .json standard"
				)
			if lines[j + 1].strip() != "}," and lines[j + 1].strip() != "}":
				raise Error(
					f"[ERROR], line {j + 1}, prompt "
					"does not follow .json standard"
				)
			prompt = line.strip(":")[1]
			if not prompt or not isinstance(prompt, str):
				raise Error(
					f"[ERROR], line {j}, prompt "
					"is not a valid string"
				)
		elif line.strip().startswith("{"):
			continue
		elif line.strip().startswith("},"):
			continue
		elif line.strip().startswith("}"):
			if (lines[j].strip() == "}" and
			lines[j + 1].strip() != "]"):
				raise Error(
					f"[ERROR], line {j}, prompt "
					"does not follow .json standard "
					"'}' must be followed by ']'"
				)
			else:
				continue
		elif line.strip().startswith("]"):
			if j != last_line - 1:
				raise Error(
					f"[ERROR], line {j}, prompt "
					"does not follow .json standard"
				)
			else:
				continue
		else:
			raise Error(
				f"[ERROR], line {j}, input "
				"value is not a prompt"
			)

