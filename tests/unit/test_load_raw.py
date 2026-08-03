from datetime import datetime

from src.ingestion.load_raw import record_hash, parse_updated_at, filter_incremental


class TestRecordHash:
    def test_same_record_produces_same_hash(self):
        record = {"customer_id": "CUST001", "email": "a@b.com"}
        assert record_hash(record) == record_hash(record)

    def test_different_records_produce_different_hash(self):
        r1 = {"customer_id": "CUST001", "email": "a@b.com"}
        r2 = {"customer_id": "CUST002", "email": "a@b.com"}
        assert record_hash(r1) != record_hash(r2)

    def test_key_order_does_not_affect_hash(self):
        r1 = {"a": 1, "b": 2}
        r2 = {"b": 2, "a": 1}
        assert record_hash(r1) == record_hash(r2)


class TestParseUpdatedAt:
    def test_parses_iso_format(self):
        result = parse_updated_at("2026-08-02T10:30:00.123456")
        assert result == datetime(2026, 8, 2, 10, 30, 0)

    def test_truncates_microseconds(self):
        result = parse_updated_at("2026-08-02T10:30:00.999999")
        assert result.microsecond == 0


class TestFilterIncremental:
    def test_no_watermark_returns_all_records(self):
        records = [
            {"updated_at": "2026-01-01T00:00:00"},
            {"updated_at": "2026-06-01T00:00:00"},
        ]
        result = filter_incremental(records, watermark=None)
        assert len(result) == 2

    def test_watermark_filters_older_records(self):
        records = [
            {"updated_at": "2026-01-01T00:00:00"},
            {"updated_at": "2026-06-01T00:00:00"},
        ]
        watermark = datetime(2026, 3, 1)
        result = filter_incremental(records, watermark)
        assert len(result) == 1
        assert result[0]["updated_at"] == "2026-06-01T00:00:00"

    def test_watermark_excludes_equal_timestamp(self):
        records = [{"updated_at": "2026-03-01T00:00:00"}]
        watermark = datetime(2026, 3, 1)
        result = filter_incremental(records, watermark)
        assert len(result) == 0