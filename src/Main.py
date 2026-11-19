from Parcer import Error, Parcer
from llm_sdk import Small_LLM_Model as llm
from typing import Any
import os
import json
import re
from Validate import review_and_repair_call, validate_call


def generate_func_name(
		model: llm,
		request: str,
		func: list[dict[str, Any]],
) -> str:
	context = (
		"Scegli la funzione piu' adatta alla richiesta. "
		'Rispondi con JSOn nel formato {"name": "nome_funzione"}".\n'
		f"Funzioni disponibili {json.dumps(func, ensure_ascii=False)}\n"
		f"Richiesta: {request}\n"
		"Nome:"
	)
	token_ids = model.encode(context)[0].tolist()
	generated_ids = []
	valid_names = {item["name"] for item in func if "name" in item}
	for _ in range(128):
		logits = model.get_logits_from_input_ids(token_ids + generated_ids)
		next_id = max(range(len(logits)), key=logits.__getitem__)
		generated_ids.append(next_id)
		text = model.decode(generated_ids)
		match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
		if match:
			name = match.group(1)
			if name not in valid_names:
				raise ValueError(f"Funzione non disponibile: {name}")
			return name
	raise RuntimeError(
		"Il modello non ha identificato una funzione. Testo:"
		f"{model.decode(generated_ids)}"
	)

def generate_args(
		model: llm,
		request: str,
		func: dict[str, Any],
) -> dict[str, Any]:
	parameters = func.get("parameters", {})
	expected = set(parameters)
	context = (
		"Estrai dalla richiesta i valori dei parametri della funzione.\n"
		"Lo schema indica i tipi attesi: non copiare lo schema nella risposta.\n"
		"Rispondi con un solo oggetto JSON. Le chiavi devono essere "
		"esattamente i nomi dei parametri; i valori devono essere "
		"quelli estratti dalla richiesta.\n"
		"Non aggiungere chiavi come 'type', 'description' o 'parameters'.\n"
		f"Schema dei parametri: "
		f"{json.dumps(parameters, ensure_ascii=False)}\n"
		f"Richiesta: {request}\n"
		"Valori:"
	)
	token_ids = model.encode(context)[0].tolist()
	generated_ids = []
	decoder = json.JSONDecoder()
	for _ in range(128):
		logits = model.get_logits_from_input_ids(token_ids + generated_ids)
		next_id = max(range(len(logits)), key=logits.__getitem__)
		generated_ids.append(next_id)
		text = model.decode(generated_ids)
		start = text.find("{")
		if start == -1:
			continue
		try:
			arguments, _ = decoder.raw_decode(text, start)
		except json.JSONDecodeError:
			continue
		if not isinstance(arguments, dict):
			raise ValueError("Gli argomenti generati non sono un oggetto JSON")
		expected = set(func.get("parameters", {}))
		missing = expected - set(arguments)
		if missing:
			raise ValueError(
				f"Parametri mancanti: {missing}\n"
				f"Argomenti generati: {arguments}\n"
				f"Testo prodotto: {text}"
			)
		arguments = {
			key: arguments[key]
			for key in expected
		}
		return arguments
	raise RuntimeError(
		"Il modello non ha identificato una funzione. Testo:"
		f"{model.decode(generated_ids)}"
	)

def main():
	try:
		parce = Parcer()
		model = llm()
		prompt, function = parce.parce()
		updated_prompts = []
		for index, prompt_item in enumerate(prompt):
			if not isinstance(prompt_item, dict):
				raise ValueError(f"il prompt {index} non e' un oggetto JSON")
			request = prompt_item.get("prompt")
			if not isinstance(request, str):
				raise ValueError(f"il prompt {index} non contiene testo valido")
			selected_func = next(
				(
					item for item in function
					if item.get("name") == func_name
				),
				None,
			)
			if selected_func is None:
				raise ValueError(f"Funzione non trovata: {func_name}")
			func_name, args = review_and_repair_call(model, request, function)
			updated_item = dict(prompt_item)
			updated_item.update({
				"name": func_name,
				"arguments": args,
			})
			updated_prompts.append(updated_item)
			script_dir = os.path.dirname(os.path.abspath(__file__))
			project_dir = os.path.dirname(script_dir)
			output_dir = os.path.join(project_dir, "data", "output")
			os.makedirs(output_dir, exist_ok=True)
			output_file = os.path.join(
				output_dir, "function_calls.join"
			)
			with open(output_file, "w", encoding="utf-8") as f:
				json.dump(updated_prompts, f, ensure_ascii=False, indent=2)
				f.write("\n")
	except Error as error:
		print(error)


if __name__ == "__main__":
	main()
