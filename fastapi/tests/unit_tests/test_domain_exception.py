from src.exceptions.base import DomainException


def test_domain_exception_stores_detail_and_status_code():
    exc = DomainException(detail="boom", status_code=422)

    assert str(exc) == "boom"
    assert exc.detail == "boom"
    assert exc.status_code == 422


def test_domain_exception_uses_default_status_code():
    exc = DomainException(detail="default")

    assert exc.status_code == 400
