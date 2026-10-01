"""Pure PromptPay payload generation and validation."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

PROMPTPAY_AID = "A000000677010111"


def tlv(tag: str, value: str) -> str:
    if not re.fullmatch(r"\d{2}", tag):
        raise ValueError("tag must contain exactly two digits")
    if len(value) > 99:
        raise ValueError(f"field {tag} too long")
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    try:
        raw = data.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("EMV payload must contain ASCII characters") from exc
    for byte in raw:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def normalize_target(target: str) -> tuple[str, str]:
    digits = re.sub(r"\D", "", target)
    if len(digits) == 13:
        return "02", digits
    if len(digits) == 10 and digits.startswith("0"):
        return "01", "0066" + digits[1:]
    if len(digits) == 11 and digits.startswith("66"):
        return "01", "00" + digits
    raise ValueError("PromptPay ID must be a Thai mobile number or a 13-digit ID")


def payload(target: str, amount: Decimal | float | int | None = None) -> str:
    sub_tag, value = normalize_target(target)
    fields = [tlv("00", "01"), tlv("01", "12" if amount is not None else "11"),
              tlv("29", tlv("00", PROMPTPAY_AID) + tlv(sub_tag, value)), tlv("53", "764"), tlv("58", "TH")]
    if amount is not None:
        try:
            money = Decimal(str(amount)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("amount must be a finite positive number") from exc
        if not money.is_finite() or money <= 0:
            raise ValueError("amount must be a finite positive number")
        fields.append(tlv("54", f"{money:.2f}"))
    body = "".join(fields) + "6304"
    return body + crc16_ccitt(body)


def parse(data: str) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(data):
        if i + 4 > len(data) or not data[i:i + 4].isdigit():
            raise ValueError("malformed EMV TLV")
        tag, length = data[i:i + 2], int(data[i + 2:i + 4])
        end = i + 4 + length
        if end > len(data):
            raise ValueError("truncated EMV TLV")
        out[tag] = data[i + 4:end]
        i = end
    return out


def is_valid(data: str) -> bool:
    return len(data) > 8 and data[-8:-4] == "6304" and crc16_ccitt(data[:-4]) == data[-4:]
