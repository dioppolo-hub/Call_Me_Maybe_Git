from typing import Any
from llm_sdk import Small_LLM_Model as llm
import json


def validate_call(
		name: str,
		functions: list[dict[str, Any]],
		arguments: dict[str, Any]
) -> dict[str, Any]:
	function = next(
		(item for item in functions if item.get("name") == name), None,
	)
	if function is None:
		raise ValueError(f"Funzione non disponibile: {name}")
	parameters = function.get("parameters", {})
	if not isinstance(parameters, dict):
		raise ValueError(f"Schema parametri non valido per {name}")
	expected_keys = set(parameters)
	actual_keys = set(arguments)
	if expected_keys != actual_keys:
		raise ValueError(
			f"Parametri non corretti per {name}"
			f"attesi: {expected_keys}, ricevuti: {actual_keys}"
		)
	for key, schema in parameters.items():
		value = arguments[key]
		expected_type = schema.get("type")
		valid = (
			expected_type == "string"
			and isinstance(value, str)
			or expected_type == "number"
			and isinstance(value, (int, float))
			and not isinstance(value, bool)
			or expected_type == "integer"
			and isinstance(value, int)
			and not isinstance(value, bool)
			or expected_type == "boolean"
			and isinstance(value, bool)
			or expected_type == "array"
			and isinstance(value, list)
			or expected_type == "object"
			and isinstance(value, dict)
		)
		if not valid:
			raise ValueError(
				f"Tipo non valido pr '{key}': atteso: "
				f"{expected_type}, ricvuto: {type(value).__name__}"
			)

def review_and_repair_call(
		model: llm,
		request: str,
		functions: list[dict[str, Any]]
) -> tuple[str, dict[str, Any]]:
	decoder = json.JSONDecoder()
	last_error = "Nessun tentativo effettuato"
	for attempt in range(3):
		context = (
			"seleziona la funzione piu' adatta ed estrai i valori dei suoi "
			"parametri dalla richiesta. Restituisci gli input della funzione, "
			"non il risultato che la funzione calcolerebbe.\n"
			'rispondi solo con JSON nel formato: '
			'{"name": "nome_funzione",'
			'"arguments": {"parametro": "valore"}}.\n'
			"Definizioni disponibili: "
			f"{json.dumps(functions, ensure_ascii=False)}\n"
			f"Richiesta: {request}\n"
		)
		if attempt:
			context += (
				f"La risposta precedente non era valida: {last_error}\n"
				"Rigenera da zero l'intero oggetto JSON rispettando "
				"le definizioni.\n"
			)
		context += "Chiamata:"
		token_ids = model.encode(context)[0].tolist()
		result = None
		generated_ids = []
		for _ in range(128):
			logits = model.get_logits_from_input_ids(
				token_ids + generated_ids
			)
			next_id = max(range(len(logits)), key=logits.__getitem__)
			generated_ids.append(next_id)
			text = model.decode(generated_ids)
			start = text.find("{")
			if start == -1:
				continue
			try:
				candidate, _ = decoder.raw_decode(text, start)
			except json.JSONDecodeError:
				continue
			if (
				isinstance(candidate, dict)
				and isinstance(candidate.get("name"), str)
				and isinstance(candidate.get("arguments"), dict)
				):
					result = candidate
					break
		if result is None:
			last_error = (
				"Risposta senza i campi richiesti. Testo generato:"
				f"{model.decode(generated_ids)}"
			)
			continue
		name = result.get("name")
		args = result.get("arguments")
		if (
			not isinstance(name, str)
			or not isinstance(args, dict)
		):
			last_error = (
				"La risposta deve avere 'name' testuale e "
				"'arguments' come oggetto JSON"
			)
			continue
		try:
			validate_call(name, functions, args)
		except ValueError as error:
			last_error = str(error)
			continue
		return (name, args)
	raise ValueError(
		f"Chiamata non valida dopo 3 tentativi: {last_error}"
	)
