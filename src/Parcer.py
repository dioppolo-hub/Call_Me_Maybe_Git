import sys
import json
from typing import Any
from pydantic import BaseModel, Field


class Error(Exception):
	pass


class Parcer(BaseModel):
	prompt_list_file: list[str] = sys.argv
	prompt_list: list[str] = []
	function_list: list[dict[Any, str]] = []

	def parce_function(self):
		if "--function_definition" not in self.prompt_list_file:
			func_path = "data/input/functions_definition.json"
		i = 0
		for _ in self.prompt_list_file:
			if self.prompt_list_file[i].startswith("--function_definition"):
				func_path = self.prompt_list_file[i + 1]
			i += 1
		try:
			with open(func_path) as f:
				lines = json.load(f)
		except FileNotFoundError:
			raise Error(
				"[ERROR], file function_def not found"
			)
		except json.JSONDecodeError:
			raise Error(
				"[ERROR], function definition file does not"
				"follow JSON standard"
			)
		if not isinstance(lines, list) or not all(
			isinstance(func, dict) for func in lines 
		):
			raise Error(
				"[ERROR], function definition must follow"
				" JSON standard"
			)
		self.function_list = lines			

	def parce_prompt(self):
		if "--input" not in self.prompt_list_file:
			input_path = "data/input/function_calling_tests.json"
		i = 0
		for _ in self.prompt_list_file:
			if self.prompt_list_file[i].startswith("--input"):
				input_path = self.prompt_list_file[i + 1]
			i += 1
		try:
			with open(input_path) as f:
				lines = json.load(f)
		except FileNotFoundError:
			raise Error(
				"[ERROR], file input not found"
			)
		except json.JSONDecodeError:
			raise Error(
				"[ERROR], function definition file does not"
				"follow JSON standard"
			)
		if not isinstance(lines, list) or not all(
			isinstance(func, dict) for func in lines
		):
			raise Error(
				"[ERROR], prompt definition must follow"
				" JSON standard"
			)
		self.prompt_list = lines
