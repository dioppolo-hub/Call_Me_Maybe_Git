### uv venv
### uv sync


# Call Me Maybe

Basandoci sul documento del progetto "Call Me Maybe" della scuola 42, ti trovi di fronte a un'esperienza stimolante: costruire un sistema di *function calling* per un Modello Linguistico di Grandi Dimensioni (LLM) di ridotte dimensioni (0.6 miliardi di parametri), sfruttando una tecnica avanzata chiamata *constrained decoding* (decodifica vincolata).

Dato che parti da zero con gli LLM, i token e i file JSON, ecco una guida strutturata con gli argomenti chiave che devi studiare e approfondire per affrontare con successo questo progetto.

## 1. Fondamenti di JSON e manipolazione dei dati in Python

Il progetto ruota attorno alla lettura, validazione e scrittura di file in formato JSON.

### Cosa studiare

- La struttura del formato JSON: oggetti, array, chiavi e tipi di dati come stringhe, numeri e booleani.
- Il modulo integrato `json` di Python per caricare (`json.load`, `json.loads`) e salvare dati (`json.dump`, `json.dumps`).
- La libreria Pydantic (obbligatoria da specifica): impara a definire modelli di dati (`BaseModel`) per validare automaticamente gli input, gli output e i parametri delle funzioni in base a uno schema.

## 2. Architettura di un LLM e concetti di tokenizzazione

Prima di scrivere codice, devi capire come un computer "legge" e "genera" testo tramite un modello di linguaggio.

### Cosa studiare

- **Token e tokenizer:** come il testo viene spezzato in unità più piccole (token) tramite algoritmi come BPE o SentencePiece e come ogni token corrisponde a un ID numerico (`token_id`).
- **Vocabolario:** il file di vocabolario (fornito dal modello o dall'SDK) che mappa gli ID numerici alle stringhe corrispondenti.
- **Logits:** cosa sono i logits (i punteggi di probabilità grezzi che il modello assegna a ogni token del vocabolario come possibile token successivo).
- **SDK del progetto (`llm_sdk`):** studia i metodi messi a disposizione (come `get_logits_from_input_ids`, `get_path_to_vocab_file`, `encode`) per capire come interagire con il modello `Qwen/Qwen3-0.6B` senza usare librerie pesanti come Hugging Face o PyTorch (che sono esplicitamente vietate).

## 3. Il cuore del progetto: il constrained decoding

I modelli piccoli come quello da 0.6B tendono a sbagliare la sintassi o la struttura quando gli si chiede di generare un JSON. Il *constrained decoding* risolve questo problema.

### Cosa studiare

- Come funziona la generazione token per token in un LLM.
- Il meccanismo di filtraggio dei logits: a ogni passo della generazione, devi controllare quali token del vocabolario mantengono la struttura JSON valida e rispettano lo schema definito in `functions_definition.json`.
- Come impostare a meno infinito (`-float('inf')`) i logit dei token non validi, forzando il modello a scegliere solo tra i token che mantengono il codice sintatticamente corretto e coerente con i tipi di dati attesi (numeri, stringhe, ecc.).

## 4. Strumenti di sviluppo e buone pratiche (standard 42)

Il progetto richiede rigore ingegneristico e l'uso di specifici strumenti di automazione e controllo qualità.

### Cosa studiare

- **Python 3.10+:** uso rigoroso dei type hints (annotazioni dei tipi) e del modulo `typing`.
- **Mypy:** controllo statico dei tipi (il codice deve passare senza errori con flag specifici come `--disallow-untyped-defs`).
- **Flake8:** rispetto dello standard di stile del codice Python (PEP 8).
- **UV:** gestore di pacchetti e ambienti virtuali (richiesto per la gestione delle dipendenze e il comando `uv sync`).
- **Makefile:** come automatizzare i comandi di installazione, esecuzione, pulizia e linting.

## Prossimo passo consigliato

Ti consiglio di procedere per gradi:

1. Prendi confidenza con il parsing dei file JSON di input (`functions_definition.json` e `function_calling_tests.json`) usando Pydantic.
2. Esplora l'SDK del modello (`llm_sdk`) per capire come trasformare un prompt in token e ottenere i logits grezzi.
3. Affronta la logica del *constrained decoding*, iniziando a mappare i token del vocabolario per capire quali possono essere ammessi passo dopo passo nella costruzione del JSON finale.
