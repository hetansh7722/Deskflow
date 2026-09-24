import os
import tempfile

# isolate the test DB before project modules are imported
_TEST_DB = os.path.join(tempfile.gettempdir(), "deskflow_pytest.db")
os.environ["DESKFLOW_DB"] = _TEST_DB
os.environ["DISCORD_WEBHOOK_URL"] = ""
os.environ["SMTP_HOST"] = ""

if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
