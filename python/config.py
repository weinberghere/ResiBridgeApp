from datetime import datetime
from flask_config import *
from acp_config import *
from splynx_config import *

# SAC CODES Configuration
SAC_CODES = {
    "NY": "815160",
    "KY": "826163"
}

# Footer Date
days = datetime.now().strftime('%d')
day = int(days)
if 4 <= day <= 20 or 24 <= day <= 30:
    suffix = "th"
else:
    suffix = ["st", "nd", "rd"][day % 10 - 1]
date_format=datetime.now().strftime('%A %B') + " " +days+suffix

