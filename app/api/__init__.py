import decimal
import json

# Helper class to convert a DynamoDB item to JSON.


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


ALLOC_APPROVE_CONFIRM_TYPES = ['Approved', 'Denied', 'Approved in part']
RC_SMALL_LOGO_URL = 'https://staging.rc.virginia.edu/images/logos/uva_rc_logo_full_340x129.png'
RC_LARGE_LOGO_URL = 'https://staging.rc.virginia.edu/images/logos/uva_rc_logo_full_1000x380.png'
BII_COST_CENTERS = ['CC0896','CC1524','CC1525','CC1526','CC1527','CC1528','CC1529']
DS_COST_CENTERS = []