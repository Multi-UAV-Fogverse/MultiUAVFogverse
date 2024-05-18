import logging
from fogverse.fogverse_logging import get_logger, FogVerseLogging
import time
from uuid import uuid4


headers = [
            "timestamp",
            "frame_id"
        ]

fogverse_logger = FogVerseLogging(
            name="test-log-"+str(uuid4()),
            dirname="test-logs",
            csv_header=headers,
            level= logging.INFO + 2
        )

for i in range(100):
    fogverse_logger.csv_log(
            [time.time(), i]
        )