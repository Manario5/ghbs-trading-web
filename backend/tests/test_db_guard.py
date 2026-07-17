import os
import pytest
from backend.db.database import get_db_path

def test_db_path_guard():
    # Store originals to restore later
    orig_db_path = os.environ.get("DB_PATH")
    orig_allow = os.environ.get("ALLOW_PRODUCTION_DB")

    try:
        # 1. Unset DB_PATH uses default
        os.environ.pop("DB_PATH", None)
        assert get_db_path() == "tasi_ledger_test.db"
        
        # 2. tasi_ledger.db without allow override raises error
        os.environ["DB_PATH"] = "tasi_ledger.db"
        os.environ["ALLOW_PRODUCTION_DB"] = "false"
        from fastapi import HTTPException
        from backend.db.database import assert_db_allowed
        with pytest.raises(HTTPException) as exc_info:
            assert_db_allowed()
        assert exc_info.value.status_code == 503
        assert "Database access blocked by safety guard" in exc_info.value.detail
            
        # 3. tasi_ledger.db with override works
        os.environ["ALLOW_PRODUCTION_DB"] = "true"
        assert get_db_path() == "tasi_ledger.db"
        
        # 4. Another path works without override
        os.environ["DB_PATH"] = "my_custom_db.sqlite"
        os.environ.pop("ALLOW_PRODUCTION_DB", None)
        assert get_db_path() == "my_custom_db.sqlite"
        
    finally:
        # Restore environment
        if orig_db_path is not None:
            os.environ["DB_PATH"] = orig_db_path
        else:
            os.environ.pop("DB_PATH", None)
            
        if orig_allow is not None:
            os.environ["ALLOW_PRODUCTION_DB"] = orig_allow
        else:
            os.environ.pop("ALLOW_PRODUCTION_DB", None)
