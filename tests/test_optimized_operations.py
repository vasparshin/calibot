"""
Integration tests for the optimized operation-based architecture.
Tests all operation classes to ensure they work correctly with the new structure.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import operation classes
from app.operations.create_operation import CreateOperation
from app.operations.query_operation import QueryOperation
from app.operations.update_operation import UpdateOperation
from app.operations.delete_operation import DeleteOperation
from app.operations.operation_factory import OperationFactory
from app.core.response_manager import ResponseManager

@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    telegram_service = MagicMock()
    telegram_service.send_telegram_message = AsyncMock()

    conversation_state = MagicMock()
    conversation_state.add_message = MagicMock()
    conversation_state.get_conversation_history = MagicMock(return_value=[])

    calendar_service = MagicMock()
    calendar_service.query_events = AsyncMock()
    calendar_service.create_event = AsyncMock()
    calendar_service.update_event = AsyncMock()
    calendar_service.delete_event = AsyncMock()
    calendar_service.is_authenticated = MagicMock(return_value=True)

    calendar_agent = MagicMock()

    return {
        'telegram': telegram_service,
        'conversation': conversation_state,
        'calendar': calendar_service,
        'calendar_agent': calendar_agent
    }

@pytest.fixture
def response_manager():
    """Create response manager instance."""
    return ResponseManager()

class TestCreateOperation:
    """Test cases for CreateOperation."""

    @pytest.mark.asyncio
    async def test_create_single_event_success(self, mock_services):
        """Test successful single event creation."""
        services = mock_services

        # Mock successful calendar response
        services['calendar'].create_event.return_value = {
            'success': True,
            'event_link': 'https://calendar.google.com/event123',
            'calendar_used': 'Primary Calendar',
            'event_id': 'event123'
        }

        # Mock calendar selection
        services['calendar'].calendar_agent.select_calendar = AsyncMock(return_value={
            'success': True,
            'calendar_id': 'primary',
            'calendar_name': 'Primary Calendar'
        })

        operation = CreateOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'create',
            'event_name': 'Test Meeting',
            'date': '2025-01-20',
            'start_time': '14:00',
            'end_time': '15:00',
            'calendar_name': 'Work'
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == True
        assert 'Event created successfully' in result['message']
        services['calendar'].create_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_batch_events(self, mock_services):
        """Test batch event creation."""
        services = mock_services

        # Mock successful calendar responses for batch creation
        services['calendar'].create_event.side_effect = [
            {
                'success': True,
                'event_link': 'https://calendar.google.com/event1',
                'calendar_used': 'Primary Calendar',
                'event_id': 'event1'
            },
            {
                'success': True,
                'event_link': 'https://calendar.google.com/event2',
                'calendar_used': 'Primary Calendar',
                'event_id': 'event2'
            }
        ]

        operation = CreateOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'create',
            'events': [
                {
                    'event_name': 'Meeting 1',
                    'date': '2025-01-20',
                    'start_time': '09:00',
                    'end_time': '10:00'
                },
                {
                    'event_name': 'Meeting 2',
                    'date': '2025-01-20',
                    'start_time': '14:00',
                    'end_time': '15:00'
                }
            ]
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == True
        assert result['successful_count'] == 2
        assert len(services['calendar'].create_event.call_args_list) == 2

    @pytest.mark.asyncio
    async def test_create_no_events_found(self, mock_services):
        """Test handling when no valid events are found."""
        services = mock_services

        operation = CreateOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'create'
            # Missing required fields
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == False
        assert 'No valid events to create' in result['message']

class TestQueryOperation:
    """Test cases for QueryOperation."""

    @pytest.mark.asyncio
    async def test_query_today_schedule(self, mock_services):
        """Test querying today's schedule."""
        services = mock_services

        # Mock successful query response
        services['calendar'].query_events.return_value = {
            'success': True,
            'events': [
                {
                    'summary': 'Meeting 1',
                    'start': '2025-01-20T09:00:00',
                    'end': '2025-01-20T10:00:00',
                    'calendar_name': 'Work',
                    'htmlLink': 'https://calendar.google.com/event1'
                },
                {
                    'summary': 'Meeting 2',
                    'start': '2025-01-20T14:00:00',
                    'end': '2025-01-20T15:00:00',
                    'calendar_name': 'Work',
                    'htmlLink': 'https://calendar.google.com/event2'
                }
            ]
        }

        operation = QueryOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'query',
            'original_message': 'what\'s my schedule today',
            'date': '2025-01-20'
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == True
        assert 'you have 2 events' in result['message']
        services['calendar'].query_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_no_events_found(self, mock_services):
        """Test handling when no events are found."""
        services = mock_services

        services['calendar'].query_events.return_value = {
            'success': True,
            'events': []
        }

        operation = QueryOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'query',
            'event_name': 'Nonexistent Event',
            'date': '2025-01-20'
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == False
        assert 'No matching events found' in result['message']

class TestUpdateOperation:
    """Test cases for UpdateOperation."""

    @pytest.mark.asyncio
    async def test_update_single_event(self, mock_services):
        """Test updating a single event."""
        services = mock_services

        # Mock query to find event
        services['calendar'].query_events.return_value = {
            'success': True,
            'events': [
                {
                    'id': 'event123',
                    'summary': 'Original Meeting',
                    'calendar_id': 'primary'
                }
            ]
        }

        # Mock successful update
        services['calendar'].update_event.return_value = {
            'success': True,
            'updated_event': {
                'summary': 'Updated Meeting',
                'start': '2025-01-20T15:00:00',
                'end': '2025-01-20T16:00:00',
                'calendar_name': 'Work',
                'htmlLink': 'https://calendar.google.com/event123'
            }
        }

        operation = UpdateOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'update',
            'event_name': 'Original Meeting',
            'new_start_time': '15:00',
            'new_end_time': '16:00'
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == True
        assert 'Successfully updated event' in result['message']
        services['calendar'].update_event.assert_called_once()

    def test_parse_time_shift(self, mock_services):
        """Test time shift parsing."""
        services = mock_services

        operation = UpdateOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        # Test various time shift formats
        assert operation.parse_time_shift("1 hour later") == 60
        assert operation.parse_time_shift("30 minutes") == 30
        assert operation.parse_time_shift("2 hours earlier") == -120
        assert operation.parse_time_shift("45 minutes back") == -45

class TestDeleteOperation:
    """Test cases for DeleteOperation."""

    @pytest.mark.asyncio
    async def test_delete_single_event(self, mock_services):
        """Test deleting a single event."""
        services = mock_services

        # Mock query to find event
        services['calendar'].query_events.return_value = {
            'success': True,
            'events': [
                {
                    'id': 'event123',
                    'summary': 'Meeting to Delete',
                    'calendar_id': 'primary'
                }
            ]
        }

        # Mock successful deletion
        services['calendar'].delete_event.return_value = {
            'success': True
        }

        operation = DeleteOperation(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        event_data = {
            'intent': 'delete',
            'event_name': 'Meeting to Delete',
            'date': '2025-01-20'
        }

        result = await operation.execute(123, event_data)

        assert result['success'] == True
        assert 'Successfully deleted' in result['message']
        services['calendar'].delete_event.assert_called_once()

class TestOperationFactory:
    """Test cases for OperationFactory."""

    def test_create_operation_factory(self, mock_services):
        """Test creating operation factory."""
        services = mock_services

        factory = OperationFactory(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        assert factory is not None
        assert 'create' in factory.operations
        assert 'query' in factory.operations
        assert 'update' in factory.operations
        assert 'delete' in factory.operations

    def test_supported_intents(self, mock_services):
        """Test getting supported intents."""
        services = mock_services

        factory = OperationFactory(
            services['telegram'],
            services['conversation'],
            services['calendar'],
            services['calendar_agent']
        )

        intents = factory.get_supported_intents()
        assert 'create' in intents
        assert 'query' in intents
        assert 'update' in intents
        assert 'delete' in intents

class TestResponseManager:
    """Test cases for ResponseManager."""

    def test_format_single_event_display(self, response_manager):
        """Test single event formatting."""
        event_data = {
            'summary': 'Test Meeting',
            'start': '2025-01-20T14:00:00',
            'end': '2025-01-20T15:00:00',
            'calendar_name': 'Work Calendar',
            'htmlLink': 'https://calendar.google.com/event123'
        }

        formatted = response_manager.format_single_event_display(event_data, include_hyperlink=True)

        assert 'Test Meeting' in formatted
        assert 'Work Calendar' in formatted
        assert 'https://calendar.google.com/event123' in formatted

    def test_format_event_list_display(self, response_manager):
        """Test event list formatting."""
        events = [
            {
                'summary': 'Meeting 1',
                'start': '2025-01-20T09:00:00',
                'calendar_name': 'Work'
            },
            {
                'summary': 'Meeting 2',
                'start': '2025-01-20T14:00:00',
                'calendar_name': 'Personal'
            }
        ]

        formatted = response_manager.format_event_list_display(events, numbered=True)

        assert '1. Meeting 1' in formatted
        assert '2. Meeting 2' in formatted
        assert 'Work' in formatted
        assert 'Personal' in formatted

    def test_format_confirmation_message(self, response_manager):
        """Test confirmation message formatting."""
        events = [
            {'summary': 'Meeting 1', 'start': '2025-01-20T09:00:00'},
            {'summary': 'Meeting 2', 'start': '2025-01-20T14:00:00'}
        ]

        message = response_manager.format_confirmation_message("delete", events, 2)

        assert 'Found 2 events to delete' in message
        assert 'Meeting 1' in message
        assert 'Meeting 2' in message

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
