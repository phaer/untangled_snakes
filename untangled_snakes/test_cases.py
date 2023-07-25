import json
import gzip


def start_test_case(app_context, requirements):
    path = app_context.test_case_path
    path.mkdir(exist_ok=True)
    (path / "index").mkdir(exist_ok=True)
    (path / "metadata").mkdir(exist_ok=True)
    inputs = {"requirements": [str(r) for r in requirements]}
    with open(path / "inputs.json", "w") as f:
        json.dump(inputs, f, indent=2)


def record_index(app_context, identifier, data):
    path = (app_context.test_case_path / "index" / identifier.name).with_suffix(
        ".json.gz"
    )
    with gzip.open(path, "wt") as f:
        json.dump(data, f, indent=2)


def record_metadata(app_context, filename, metadata):
    path = app_context.test_case_path / "metadata" / f"{filename}.metadata.gz"
    with gzip.open(path, "wb") as f:
        f.write(metadata.as_bytes())


def finish_test_case(app_context, lock):
    path = app_context.test_case_path
    with open(path / "lock.json", "w") as f:
        json.dump(lock, f, indent=2)
    print(f"Wrote fixture to {path}.")
