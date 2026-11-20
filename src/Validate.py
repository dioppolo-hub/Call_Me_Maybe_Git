from typing import Any
from llm_sdk import Small_LLM_Model as llm
import json


def matches_json_type(value: Any, expected_type: str | None) -> bool:
	if expected_type == None:
		return True
	if expected_type == "string":
		return isinstance(value, str)
	if expected_type == "number":
		return isinstance(value, (int, float)) and not isinstance(value, bool)
	if expected_type == "integer":
		return isinstance(value, int) and not isinstance(value, bool)
	if expected_type == "boolean":
		return isinstance(value, bool)
	if expected_type == "array":
		return isinstance(value, list)
	if expected_type == "object":
		return isinstance(value, dict)
	return True


def get_param_schema(func_def: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
	params = func_def.get("parameters", {})
	if not isinstance(params, dict):
		return {}, []
	if isinstance(params.get("properties"), dict):
		properties = params["properties"]
		required = params.get("required", [])
		if not isinstance(required, list):
			required = []
		return properties, required
	ignored_keys = {"type", "properties", "required", "description", "title"}
	properties = {k: v for k, v in params.items() if k not in ignored_keys}
	return properties, list(properties.keys())

def validate_func_name(func_name: str, available_funcs: list[dict[str, Any]]) -> tuple[bool, str]:
	if not isinstance(func_name, str) or not func_name.strip():
		return False, "Il nome della funzione e' vuoto o non e' una stringa"
	valid_names = {f.get("name") for f in available_funcs if isinstance(f.get("name"), str)}
	if func_name not in valid_names:
		return False, f"Funzione '{func_name}' non presente tra quelle disponibili: {sorted(valid_names)}"
	return True, "OK"

def validate_args(args: Any, func_def: dict[str, Any]) -> tuple[bool, list[str]]:
	errors: list[str] = []
	if not isinstance(args, dict):
		return False, ["Gli argomenti devono essere un oggetto JSON (dict)"]
	properties, required = get_param_schema(func_def)
	for req_key in required:
		if req_key not in args or args[req_key] is None:
			errors.append(f"Parametro obbligatorio mancante o nullo: '{req_key}'")
	if properties:
		unexpected = set(args.keys()) - set(properties.keys())
		if unexpected:
			errors.append(f"Parametri non previsti dallo schema: {sorted(unexpected)}")
	for key, val in args.items():
		if key not in properties:
			continue
		prop_schema = properties[key]
		if not isinstance(prop_schema, dict):
			continue
		expected_type = prop_schema.get("type")
		if val is not None and not matches_json_type(val, expected_type):
			errors.append(
				f"Parametro '{key}': valore {val} non ammesso.\n"
				f"Valori validi: {prop_schema['enum']}"
			)
	return len(errors) == 0, errors
