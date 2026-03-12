"""Integration test suite for the MTL preprocessor.

USAGE
-----
Run from the project root (kroatoanjp_fukuin/):

    python -m preprocess.tests.integration.test_preprocessor

FIRST RUN
---------
If no expected output exists for an input file, the preprocessor output is
saved to `expected/<filename>` and the test is marked as GENERATED (not a
failure). Re-run to compare on subsequent runs.

REGENERATING EXPECTED OUTPUTS
------------------------------
Delete one or all files from the `expected/` directory, then run again.

SETUP
-----
1. Place input .txt files in:
       preprocess/tests/integration/inputs/

2. Create preprocess/tests/integration/config.json

CONFIG.JSON — basic preprocessor
    {
        "preprocessor": "basic",
        "replacement_table": "replacement_table/yourfile.json",
        "single_kanji_filter": true
    }

CONFIG.JSON — NLP preprocessor
    {
        "preprocessor": "nlp",
        "tokenizer": "fugashi",
        "replacement_table": "replacement_table/yourfile.json",
        "tag_potential_proper_nouns": false,
        "single_kanji_filter": true,
        "use_user_dict": false,
        "user_dict_path": null
    }

Paths in config.json are relative to the project root, or can be absolute.
"""

import json
import sys
import difflib
from pathlib import Path

INTEGRATION_DIR = Path(__file__).parent
INPUTS_DIR = INTEGRATION_DIR / "inputs"
EXPECTED_DIR = INTEGRATION_DIR / "expected"
CONFIG_FILE = INTEGRATION_DIR / "config.json"
PROJECT_ROOT = INTEGRATION_DIR.parent.parent.parent  # kroatoanjp_fukuin/


def load_config():
    if not CONFIG_FILE.exists():
        print(f"ERROR: No config.json found at {CONFIG_FILE}")
        print("       See the file docstring for setup instructions.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_path(path_str):
    p = Path(path_str)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_replacement_table(config):
    table_path_str = config.get("replacement_table")
    if not table_path_str:
        print("ERROR: No 'replacement_table' key in config.json.")
        sys.exit(1)
    p = resolve_path(table_path_str)
    if not p.exists():
        print(f"ERROR: Replacement table not found: {p}")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def build_tagger(config, replacement_table):
    from preprocess.nlp_mtl_preprocess import NLP_MTL_Preprocess
    from preprocess.tagger import Tagger

    tokenizer_name = config.get("tokenizer", "fugashi")
    use_user_dict = config.get("use_user_dict", False)
    user_dict_path = config.get("user_dict_path")

    if tokenizer_name == "fugashi":
        from preprocess.tokenizer.fugashi_tokenizer import FugashiTokenizer
        tokenizer = FugashiTokenizer(user_dic_path=user_dict_path) if use_user_dict else FugashiTokenizer()
    elif tokenizer_name == "sudachi":
        from preprocess.tokenizer.sudachi_tokenizer import SudachiTokenizer
        tokenizer = SudachiTokenizer(user_dic_path=user_dict_path) if use_user_dict else SudachiTokenizer()
    elif tokenizer_name == "spacy":
        from preprocess.tokenizer.spacy_tokenizer import SpacyTokenizer
        tokenizer = SpacyTokenizer(user_dic_path=user_dict_path) if use_user_dict else SpacyTokenizer()
    else:
        print(f"ERROR: Unknown tokenizer: {tokenizer_name!r}")
        sys.exit(1)

    proper_noun_list = NLP_MTL_Preprocess.generate_name_list_from_replacement_table(replacement_table)
    return Tagger(
        tokenizer=tokenizer,
        tag_potential_proper_nouns=config.get("tag_potential_proper_nouns", False),
        proper_noun_list=proper_noun_list,
    )


def run_preprocessor(text, config, replacement_table, tagger):
    preprocessor_type = config.get("preprocessor", "basic")
    single_kanji_filter = config.get("single_kanji_filter", True)

    if preprocessor_type == "basic":
        from preprocess.mtl_preprocess import MTL_Preprocess
        preprocess = MTL_Preprocess(
            text=text,
            replacement=replacement_table,
            single_kanji_filter=single_kanji_filter,
        )
    elif preprocessor_type == "nlp":
        from preprocess.nlp_mtl_preprocess import NLP_MTL_Preprocess
        preprocess = NLP_MTL_Preprocess(
            text=text,
            tagger=tagger,
            replacement_table=replacement_table,
            single_kanji_filter=single_kanji_filter,
        )
    else:
        print(f"ERROR: Unknown preprocessor type: {preprocessor_type!r}")
        sys.exit(1)

    return preprocess.replace()


def run_tests():
    config = load_config()
    replacement_table = load_replacement_table(config)

    input_files = sorted(INPUTS_DIR.glob("*.txt")) if INPUTS_DIR.exists() else []
    if not input_files:
        print(f"No .txt files found in {INPUTS_DIR}")
        print("Add input files to that directory and run again.")
        sys.exit(0)

    # Build tagger once (expensive) if running NLP mode
    tagger = None
    if config.get("preprocessor", "basic") == "nlp":
        print("Initializing NLP tokenizer...")
        tagger = build_tagger(config, replacement_table)

    EXPECTED_DIR.mkdir(exist_ok=True)

    passed = []
    failed = []
    generated = []

    print(f"\nRunning {len(input_files)} test(s)...\n")

    for input_file in input_files:
        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()

        print(f"  {input_file.name} ... ", end="", flush=True)
        actual = run_preprocessor(text, config, replacement_table, tagger)

        expected_file = EXPECTED_DIR / input_file.name

        if not expected_file.exists():
            with open(expected_file, "w", encoding="utf-8") as f:
                f.write(actual)
            print("GENERATED")
            generated.append(input_file.name)
            continue

        with open(expected_file, "r", encoding="utf-8") as f:
            expected = f.read()

        if actual == expected:
            print("PASS")
            passed.append(input_file.name)
        else:
            print("FAIL")
            diff = difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile=f"expected/{input_file.name}",
                tofile=f"actual/{input_file.name}",
                n=3,
            )
            print("".join(diff))
            failed.append(input_file.name)

    # Summary
    print("\n" + "-" * 40)
    parts = []
    if passed:
        parts.append(f"{len(passed)} passed")
    if failed:
        parts.append(f"{len(failed)} failed")
    if generated:
        parts.append(f"{len(generated)} generated (run again to compare)")
    print(", ".join(parts) if parts else "No tests ran.")

    if generated:
        print("\nGenerated expected outputs for:")
        for name in generated:
            print(f"  expected/{name}")

    if failed:
        print("\nFailed tests:")
        for name in failed:
            print(f"  {name}  (delete expected/{name} to regenerate)")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
