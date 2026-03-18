"""CommitCraft — parses a git diff and generates a PR description via Claude + OpenSpec."""
import os, argparse, yaml
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def load_spec(spec_path: str) -> dict:
    with open(spec_path) as f:
        return yaml.safe_load(f)


def build_prompt(spec: dict, diff: str) -> str:
    sections = "\n".join(
        f"## {f['name'].replace('_', ' ').title()}\n{f.get('prompt', '')}"
        for f in spec.get("fields", [])
    )
    return (
        f"You are CommitCraft. Generate a PR description from this git diff.\n\n"
        f"Include these sections (use ## headings):\n{sections}\n\n"
        f"GIT DIFF:\n```diff\n{diff[:6000]}\n```\n\n"
        "Write clean Markdown. Be specific — reference actual file names and function names from the diff."
    )


def generate(diff_path: str, spec_path: str, output_path: str) -> None:
    with open(diff_path) as f:
        diff = f.read()
    spec = load_spec(spec_path)
    prompt = build_prompt(spec, diff)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    description = response.content[0].text
    with open(output_path, "w") as f:
        f.write(description)
    print(f"✅ PR description → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CommitCraft — generate PR descriptions from diffs")
    parser.add_argument("--diff",   required=True, help="Path to git diff file")
    parser.add_argument("--spec",   required=True, help="Path to OpenSpec YAML")
    parser.add_argument("--output", required=True, help="Output Markdown file path")
    args = parser.parse_args()
    generate(args.diff, args.spec, args.output)
