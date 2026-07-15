import logging
from app.core.logger import NoiseLogFilter

def test_noise_log_filter():
    filt = NoiseLogFilter()
    
    # Noise records that should be filtered out (return False)
    record1 = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1 - "GET /api/tasks HTTP/1.1" 200',
        args=("127.0.0.1", "GET", "/api/tasks", "1.1", 200),
        exc_info=None
    )
    assert not filt.filter(record1)
    
    record2 = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1 - "GET /static/main.js HTTP/1.1" 200',
        args=("127.0.0.1", "GET", "/static/main.js", "1.1", 200),
        exc_info=None
    )
    assert not filt.filter(record2)

    # Valid record that should NOT be filtered out (return True)
    record3 = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='127.0.0.1 - "POST /api/other HTTP/1.1" 200',
        args=("127.0.0.1", "POST", "/api/other", "1.1", 200),
        exc_info=None
    )
    assert filt.filter(record3)
    
    # Non-uvicorn.access record should NOT be filtered out (return True)
    record4 = logging.LogRecord(
        name="whisperMe",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Some random log",
        args=(),
        exc_info=None
    )
    assert filt.filter(record4)
