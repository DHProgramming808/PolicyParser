import os
from openai import OpenAI

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": "Return JSON: {\"ok\": true}"}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    print(resp.choices[0].message.content)

if __name__ == "__main__":
    main()
