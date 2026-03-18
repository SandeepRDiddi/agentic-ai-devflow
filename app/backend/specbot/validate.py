"""SpecBot — validates content against an OpenSpec YAML schema using Claude."""
import os, json, yaml
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def load_spec(spec_path: str) -> dict:
    with open(spec_path) as f:
        return yaml.safe_load(f)


def build_prompt(spec: dict, content: str) -> str:
    fields_desc = "\n".join(
        f"- {f['name']} ({f['type']}, {'required' if f.get('required') else 'optional'}): {f.get('prompt', '')}"
        for f in spec.get("fields", [])
    )
    return (
        f"You are validating content against the '{spec['name']}' spec.\n\n"
        f"SPEC FIELDS:\n{fields_desc}\n\n"
        f"CONTENT TO VALIDATE:\n{content}\n\n"
        "Return a JSON object with:\n"
        "- valid (boolean)\n"
        "- violations (list of strings, empty if valid)\n"
        "- suggestions (list of strings)\n"
        "Return ONLY valid JSON, no markdown fences."
    )


def validate(spec_path: str, content: str) -> dict:
    spec = load_spec(spec_path)
    prompt = build_prompt(spec, content)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"valid": False, "violations": ["Claude returned non-JSON output"], "suggestions": []}


if __name__ == "__main__":
    result = validate("spec/pr-spec.yaml", "Added login endpoint with JWT auth and unit tests.")
    print(json.dumps(result, indent=2))
