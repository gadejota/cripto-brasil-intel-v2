from __future__ import annotations

import uvicorn

from app.config import get_settings
from app.main import app


if __name__ == '__main__':
    settings = get_settings()
    uvicorn.run('server:app', host='0.0.0.0', port=settings.port, reload=False)
