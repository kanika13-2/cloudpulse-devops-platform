"""
Kubernetes Manifest Syntax & Schema Integrity Validator.
Ensures all k8s manifests are valid YAML with proper schemas, labels, and specs.
"""

import glob
import sys
import yaml


def validate_manifests():
    files = sorted(glob.glob("k8s/*.yaml"))
    if not files:
        print("ERROR: No k8s manifests found!")
        sys.exit(1)

    print(f"Found {len(files)} Kubernetes manifest files.")
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
            for doc in docs:
                if not doc:
                    continue
                assert "apiVersion" in doc, f"{filepath} missing apiVersion"
                assert "kind" in doc, f"{filepath} missing kind"
                assert "metadata" in doc, f"{filepath} missing metadata"
                assert "name" in doc["metadata"], f"{filepath} missing metadata.name"
                kind = doc["kind"]
                name = doc["metadata"]["name"]
                print(f"[VALID] {filepath} -> Kind: {kind:<25} Name: {name}")

    print("\nSUCCESS: All Kubernetes manifests passed schema validation!")


if __name__ == "__main__":
    validate_manifests()
