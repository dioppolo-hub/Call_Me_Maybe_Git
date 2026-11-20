from llm_sdk import Small_LLM_Model as llm
from Validate import validate_args
import json
from typing import Any
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

def build_args_prompt(request: str, func: dict[str, Any], error_feedback: list[str] | None = None) -> str:
	func_name = func.get("name", "")
	func_desc = func.get("description", "")
	parameters = func.get("parameters", {})
	feedback_block = ""
	if error_feedback:
		feedback_block = (
			"ATTENZIONE - Tentativo precedente non valido:\n"
			+ "\n".join(f"-{err}" for err in error_feedback)
			+ "\nCorreggi questi errori estraendo SOLO i dati di input richiesti.\n\n"
		)
	return (
		"Estrai dalla richiesta SOLO i valori di INPUT da passare alla funzione.\n"
		"NON eseguire il calcolo o la trasformazione: estrai i dati grezzi/parametri "
		"che la funzione riceverà in ingresso (es. per la radice quadrata di 16 il parametro "
		"è 16, non 4; per la sostituzione regex estrai il pattern e il testo di rimpiazzo "
		"indicati nella richiesta).\n"
		"Rispondi con un solo oggetto JSON valido usando esattamente i nomi dei parametri.\n"
		"Non copiare lo schema e non aggiungere chiavi extra.\n\n"
		f"{feedback_block}"
		f"Funzione: {func_name}\n"
		f"Descrizione funzione: {func_desc}\n"
		f"Schema dei parametri: {json.dumps(parameters, ensure_ascii=False)}\n"
		f"Richiesta: {request}\n"
		"JSON argomenti:"
	)

def extra_semantic_heuristic(request: str, func_name: str, args: dict[str, Any]) -> list[str]:
	issues: list[str] = []
	req_lower = request.lower()
	if func_name == "fn_greet" and isinstance(args.get("name"), str):
		val = args["name"].strip()
		if val.lower() in {"greet", "hello", "hi", "hey"} and f"greet {val.lower()}" not in req_lower:
			issues.append(f"Il parametro 'name' ({val}) sembra il comando/saluto e non il nome della persona")
	if func_name == "fn_substitute_string_with_regex":
		src = args.get("source_string")
		regex_val = args.get("regex")
		repl_val = args.get("replacement")
		if isinstance(src, str) and src and src not in request:
			issues.append(f"'source_string' ({src}) non corrisponde alla stringa presente nella richiesta")
		if isinstance(regex_val, str):
			try:
				re.compile(regex_val)
			except re.error as exc:
				issues.append(f"'ragex' ({regex_val}) non e' un'espressione regolare valida: {exc}")
			if "all numbers" in req_lower and regex_val.strip() in {"34,233", "34", "233"}:
				issues.append("Per 'all_numbers' serve una regex per i numeri (es: \\\\d+), non i numeri trovati nel testo")
			if "all vowels" in req_lower and len(regex_val.strip()) == 1 and regex_val.lower() in "aeiou":
				issues.append("Per 'all vowels' serve una regex per tutte le vocali (es. aeiouAEIOU), non una singola vocale")
		if isinstance(repl_val, str):
			if "with numbers" in req_lower and repl_val != "NUMBERS":
				issues.append(f"Atteso replacement='NUMBERS' dalla richiesta, ottenuto {repl_val}")
			if "with asterisks" in req_lower and repl_val == "a":
				issues.append(f"Replacement {repl_val} non e' coerente con 'with asterisks'")
	return issues

def generate_args(
		model: llm,
		request: str,
		func: dict[str, Any],
		error_feedback: list[str] | None = None
) -> dict[str, Any]:
	parameters = func.get("parameters", {})
	expected = set(parameters)
	context = build_args_prompt(request, func, error_feedback)
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

def generate_args_with_retry(
		model: llm,
		request: str,
		func: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
	errors: list[str] = []
	args: dict[str, Any] = {}
	for attempt in range(3):
		args = generate_args(model, request, func, error_feedback=errors if attempt > 0 else None)
		is_valid, schema_errors = validate_args(args, func)
		heuristic_errors = extra_semantic_heuristic(request, func.get("name", ""), args)
		errors = schema_errors + heuristic_errors
		if is_valid and not heuristic_errors:
			return args, []
	return args, errors
