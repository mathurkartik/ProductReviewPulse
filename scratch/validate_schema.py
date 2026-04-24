import json
import jsonschema
from pathlib import Path

run_id = "f6c8e2b797aad2f7e45a56e8745b04852d9850b8"
doc_requests_path = Path("data/artifacts") / run_id / "doc_requests.json"
schema_path = Path("templates/doc_section.schema.json")

with open(doc_requests_path) as f:
    requests = json.load(f)

with open(schema_path) as f:
    schema = json.load(f)

# Fast hack for validation since the schema might be simple or missing parts.
# Let's just run it and see.
try:
    jsonschema.validate(instance=requests, schema=schema)
    print("Validation passed!")
except jsonschema.exceptions.ValidationError as e:
    print(f"Validation failed: {e}")
