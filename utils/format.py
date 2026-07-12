import json
from datetime import datetime, date, timedelta
from decimal import Decimal


def default_encoder(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, timedelta):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    return None


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        result = default_encoder(obj)
        if result is not None:
            return result
        return super().default(obj)
