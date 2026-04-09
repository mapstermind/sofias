"""Terminal I/O primitives. All user input goes through this module."""

from typing import Any

_SENTINEL = "__create__"


def ask(prompt: str, default: str | None = None, required: bool = True) -> str:
    hint = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{hint}: ").strip()
        if raw:
            return raw
        if default is not None:
            return default
        if not required:
            return ""
        print("  This field is required.")


def ask_int(prompt: str, default: int | None = None, required: bool = True) -> int | None:
    hint = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{hint}: ").strip()
        if not raw:
            if default is not None:
                return default
            if not required:
                return None
            print("  This field is required.")
            continue
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number.")


def ask_bool(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        raw = input(f"{prompt} {hint}: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes", "1"):
            return True
        if raw in ("n", "no", "0"):
            return False
        print("  Please enter yes or no.")


def confirm(prompt: str, default: bool = False) -> bool:
    return ask_bool(prompt, default=default)


def choose(prompt: str, options: list[tuple[str, Any]], allow_back: bool = False) -> Any:
    print(f"\n{prompt}")
    if allow_back:
        print("  0. Back")
    for i, (label, _) in enumerate(options, 1):
        print(f"  {i}. {label}")
    while True:
        raw = input("Choice: ").strip()
        if allow_back and raw == "0":
            return None
        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1][1]
        except ValueError:
            pass
        print(f"  Please enter a number between {'0' if allow_back else '1'} and {len(options)}.")


def choose_or_create(
    prompt: str,
    options: list[tuple[str, Any]],
    create_label: str = "Create new",
    allow_none: bool = False,
    none_label: str = "None",
) -> Any | None:
    """Returns a value from options, None (if allow_none), or '__create__' sentinel."""
    extended: list[tuple[str, Any]] = list(options)
    if allow_none:
        extended.append((none_label, None))
    extended.append((create_label, _SENTINEL))
    return choose(prompt, extended)
