from Parcer import Error, Parcer
from llm_sdk import Small_LLM_Model as llm
from typing import Any
import os
import json
from Gen_model import generate_args_with_retry, generate_func_name, extra_semantic_heuristic
from Validate import validate_func_name, validate_args


def main():
	try:
		parce = Parcer()
		model = llm()
		prompt, function = parce.parce()
		updated_prompts = []
		script_dir = os.path.dirname(os.path.abspath(__file__))
		project_dir = os.path.dirname(script_dir)
		output_dir = os.path.join(project_dir, "data", "output")
		os.makedirs(output_dir, exist_ok=True)
		output_file = os.path.join(output_dir, "function_calls.join")
		for index, prompt_item in enumerate(prompt):
			if not isinstance(prompt_item, dict):
				raise ValueError(f"il prompt {index} non e' un oggetto JSON")
			request = prompt_item.get("prompt")
			if not isinstance(request, str):
				raise ValueError(f"il prompt {index} non contiene testo valido")
			func_name = generate_func_name(model, request, function)
			name_ok, name_msg = validate_func_name(func_name, function)
			if not name_ok:
				raise ValueError(name_msg)
			selected_func = next(
				(
					item for item in function
					if item.get("name") == func_name
				),
				None,
			)
			if selected_func is None:
				raise ValueError(f"Funzione non trovata: {func_name}")
			args, retry_errors = generate_args_with_retry(model, request, selected_func)
			schema_ok, schema_errors = validate_args(args, selected_func)
			heuristic_errors = extra_semantic_heuristic(request, func_name, args)
			if not schema_ok:
				print(f"[AVVISO] Prompt {index} ({func_name}) non valido per schema: {schema_errors}")
			all_errors = schema_errors + heuristic_errors if retry_errors else []
			updated_item = dict(prompt_item)
			updated_item.update({
				"name": func_name,
				"arguments": args,
			})
			if all_errors:
				updated_item["validation_warnings"] = all_errors
			updated_prompts.append(updated_item)
			with open(output_file, "w", encoding="utf-8") as f:
				json.dump(updated_prompts, f, ensure_ascii=False, indent=2)
				f.write("\n")
	except Error as error:
		print(error)


if __name__ == "__main__":
	main()
