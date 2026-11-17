from Parcer import Error, Parcer
from llm_sdk import Small_LLM_Model as llm
from typing import Any
import os
import json
import re


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
		"Rispondi solo con un oggetto JSON: nessun nome funzione, "
		"descrizione o schema.\n"
		"Parametri richiesti e tipi: "
		f"{json.dumps(parameters, ensure_ascii=False)}\n"
		f"Richiesta: {request}\n"
		"Argomenti:"
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
		if set(arguments) != expected:
			raise ValueError(
				f"Parametri non corretti, attesi: {expected}\n"
				f"ricevuti: {set(arguments)}"
			)
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
		updated_prompts = [dict(item) for item in prompt]
		request = updated_prompts[0]["prompt"]
		func_name = generate_func_name(model, request, function)
		selected_func = next(
			item for item in function
			if item.get("name") == func_name
		)
		args = generate_args(model, request, selected_func)
		updated_prompts[0].update({
			"name": func_name,
			"arguments": args,
		})
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
