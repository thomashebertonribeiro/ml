"""
Custom SQLAlchemy column types shared across models.
"""

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import TIMESTAMP

# TIMESTAMPTZ — PostgreSQL TIMESTAMP WITH TIME ZONE
# Using the PostgreSQL-specific dialect type for timezone awareness.
TIMESTAMPTZ = TIMESTAMP(timezone=True)
