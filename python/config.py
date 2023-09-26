from datetime import datetime
from configurations.flask_config import *
from configurations.acp_config import *
from configurations.splynx_config import *

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

