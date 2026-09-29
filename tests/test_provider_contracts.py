from datetime import datetime, timezone
from decimal import Decimal
import pytest
from arya.providers.contracts import *

def p(): return DataProvenance("fixture","API",datetime.now(timezone.utc),"1")
def f(status=FreshnessStatus.FRESH):
    now=datetime.now(timezone.utc); return Freshness(now,now,30,0.0,status,DataQuality.VALID)
def test_success_is_available(): assert ProviderResult(["AAA"],p(),f()).available is DataAvailability.AVAILABLE
def test_failure_cannot_contain_data():
    with pytest.raises(ValueError): ProviderResult(["AAA"],p(),f(),error=ProviderError(ProviderErrorCode.TIMEOUT,"timeout",True,datetime.now(timezone.utc)))
def test_success_cannot_hide_empty_failure():
    with pytest.raises(ValueError): ProviderResult(None,p(),f())
def test_stale_is_not_current(): assert ProviderResult(["AAA"],p(),f(FreshnessStatus.STALE)).available is DataAvailability.STALE
def test_invalid_candle_is_rejected():
    with pytest.raises(ValueError): NormalizedCandle("AAA","stock","1d",datetime.now(timezone.utc),Decimal("10"),Decimal("9"),Decimal("8"),Decimal("10"),Decimal("1"),None,"IRR",p(),f())
