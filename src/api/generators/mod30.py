from __future__ import annotations

import random
from typing import Final

# charset из практики OpenMRS Mod-30 (без B I O Q S Z)
MOD30_ALPHABET: Final[str] = "0123456789ACDEFGHJKLMNPRTUVWXY"

def luhn_mod_n_check_char(body: str, alphabet: str = MOD30_ALPHABET) -> str:
    """
    Возвращает check-character для Luhn mod N (N = len(alphabet)),
    предполагая что body состоит ТОЛЬКО из символов alphabet.
    """
    n = len(alphabet)
    if n % 2 != 0:
        raise ValueError("Luhn mod N requires even N (alphabet length must be even).")

    # индекс символа -> code point
    idx = {ch: i for i, ch in enumerate(alphabet)}

    factor = 2
    total = 0

    # идём справа налево по body
    for ch in reversed(body):
        try:
            code_point = idx[ch]
        except KeyError:
            raise ValueError(f"Invalid char {ch!r} for alphabet") from None

        addend = factor * code_point
        factor = 1 if factor == 2 else 2

        # "сумма цифр" в базе n
        addend = (addend // n) + (addend % n)
        total += addend

    remainder = total % n
    check_code_point = (n - remainder) % n
    return alphabet[check_code_point]


def luhn_mod_n_is_valid(value: str, alphabet: str = MOD30_ALPHABET) -> bool:
    """
    Проверяет строку, где последний символ — check-character.
    """
    n = len(alphabet)
    if n % 2 != 0 or len(value) < 2:
        return False

    idx = {ch: i for i, ch in enumerate(alphabet)}
    factor = 1
    total = 0

    for ch in reversed(value):
        if ch not in idx:
            return False
        code_point = idx[ch]
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        addend = (addend // n) + (addend % n)
        total += addend

    return (total % n) == 0


def generate_mod30_identifier(total_len: int = 10, alphabet: str = MOD30_ALPHABET) -> str:
    """
    total_len — полная длина идентификатора (включая check-character).
    """
    if total_len < 2:
        raise ValueError("total_len must be >= 2")

    body_len = total_len - 1
    body = "".join(random.choice(alphabet) for _ in range(body_len))
    check = luhn_mod_n_check_char(body, alphabet)
    return body + check
