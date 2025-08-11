"""Handler package for decomposed routing logic (phase 1 extraction)."""

from .event_query import query_and_filter_events
from .duplicate_detection import find_duplicates
from .batch_creation import process_batch_creation
from .single_creation import create_single_event
from .intent_dispatcher import IntentDispatcher
from .update_delete import process_update_delete  # unified handler
