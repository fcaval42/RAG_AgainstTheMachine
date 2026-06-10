from src.chunker import chunk_choice, chunk_python, chunk_text


def print_chunks(title, chunks):
    print(f"\n=== {title} ===")
    print(f"chunks: {len(chunks)}")
    for i, (file_path, start, end, text) in enumerate(chunks, 1):
        print(f"[{i}] {file_path} | {start}:{end} | {text!r}")


def run_test(title, func, *args):
    print(f"\n--- {title} ---")
    try:
        chunks = func(*args)
        print_chunks(title, chunks)
    except Exception as exc:
        print(f"ERROR in {title}: {exc.__class__.__name__}: {exc}")


def main():
    print("=== chunker test runner ===")

    run_test("chunk_text", chunk_text, "docs/example.md", 80)
    run_test("chunk_python", chunk_python, "src/example.py", 120)
    run_test("chunk_choice (.py)", chunk_choice, "src/example.py", 120)
    run_test("chunk_choice (.md)", chunk_choice, "docs/example.md", 80)


if __name__ == "__main__":
    main()
