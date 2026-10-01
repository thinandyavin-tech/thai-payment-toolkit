from decimal import Decimal

import pytest

from thai_payment_toolkit import crc16_ccitt, is_valid, normalize_target, parse, payload


def test_crc_ccitt_published_vector():
    assert crc16_ccitt("123456789") == "29B1"


def test_phone_normalization_accepts_common_formats():
    assert normalize_target("081-234-5678") == ("01", "0066812345678")
    assert normalize_target("66812345678") == ("01", "0066812345678")


def test_dynamic_payload_contains_thb_amount_and_valid_crc():
    data = payload("0812345678", Decimal("185"))
    fields = parse(data)
    assert fields["01"] == "12" and fields["53"] == "764" and fields["54"] == "185.00"
    assert is_valid(data)


def test_static_payload_has_no_amount():
    assert "54" not in parse(payload("0812345678"))


@pytest.mark.parametrize("target", ["", "12345", "08123"])
def test_invalid_target_is_rejected(target):
    with pytest.raises(ValueError):
        payload(target)


@pytest.mark.parametrize("amount", [0, -1, "NaN", "Infinity"])
def test_invalid_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        payload("0812345678", amount)


def test_tampering_breaks_checksum():
    data = payload("0812345678", 100)
    assert not is_valid(data.replace("100.00", "900.00"))


def test_parser_rejects_truncated_data():
    with pytest.raises(ValueError):
        parse("000201")
