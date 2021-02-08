from .common import *
from .club import club_output

_user_output = common_output.copy()
_user_output.update(
    {
        'school_number': fields.String,
        'email': fields.String,
        'sex': fields.Boolean,
        'phone': fields.String,
        'membered_clubs': fields.List(fields.Nested(club_output))
    }
)
