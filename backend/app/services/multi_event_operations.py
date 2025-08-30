"""
Simplified Multi-event operation handler.
LLM-driven approach: Give LLM context about current events, let it determine operations.
NO MANUAL PARSING - All logic handled by LLM with proper prompt engineering.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
from litellm import acompletion
from app.config import LITELLM_MODEL
from app.prompts.multi_event_operation_prompt import MULTI_EVENT_OPERATION_PROMPT

logger = logging.getLogger(__name__)

class MultiEventOperationHandler:
    def __init__(self, calendar_service, telegram_service, conversation_state, event_queue_handler=None):
        self.calendar_service = calendar_service
        self.telegram_service = telegram_service
        self.conversation_state = conversation_state
        self.event_queue_handler = event_queue_handler
        self.pending_operations = {}
        self.model = LITELLM_MODEL
    
    async def handle_delete_operation(self, chat_id: int, event_data: Dict) -> Dict:
        """LLM-driven delete operations - no manual parsing"""
        try:
            # Get current calendar events for LLM context
            calendar_events = await self._get_calendar_events_context(event_data)

            # Let LLM determine what to delete
            operations_data = await self._analyze_with_llm(
                event_data.get('user_message', ''),
                calendar_events,
                "delete"
            )

            if operations_data.get('intent') == 'none':
                return {
                    "success": False,
                    "message": operations_data.get('message', 'LLM failed to provide message for none intent'),
                    "requires_user_action": False
                }
            
            # Store operations for confirmation
            operation_id = self.store_pending_operation(chat_id, operations_data)

            return {
                "success": True,
                "message": self._format_operations_summary(operations_data),
                "requires_user_action": operations_data.get('confirmation_needed', True),
                "operation_id": operation_id,
                "keyboard": None  # LLM handles confirmation logic
            }
                
        except Exception as e:
            logger.error(f"Error in delete operation: {e}")
            return {
                "success": False,
                "message": f"Error processing delete request: {str(e)}",
                "requires_user_action": False
            }
    
    async def handle_update_operation(self, chat_id: int, event_data: Dict) -> Dict:
        """LLM-driven update operations - no manual parsing"""
        try:
            # Get current calendar events for LLM context
            calendar_events = await self._get_calendar_events_context(event_data)

            # Let LLM determine what to update and how
            operations_data = await self._analyze_with_llm(
                event_data.get('user_message', ''),
                calendar_events,
                "update"
            )

            if operations_data.get('intent') == 'none':
                return {
                    "success": False,
                    "message": operations_data.get('message', 'LLM failed to provide message for none intent'),
                    "requires_user_action": False
                }
            
            # Store operations for confirmation
            operation_id = self.store_pending_operation(chat_id, operations_data)
            
            return {
                "success": True,
                "message": self._format_operations_summary(operations_data),
                "requires_user_action": operations_data.get('confirmation_needed', True),
                "operation_id": operation_id,
                "keyboard": None
            }
            
        except Exception as e:
            logger.error(f"Error in update operation: {e}")
            return {
                "success": False,
                "message": f"Error processing update request: {str(e)}",
                "requires_user_action": False
            }
    
    async def _get_calendar_events_context(self, event_data: Dict) -> str:
        """Get current calendar events for LLM context"""
        try:
            # Query calendar for events based on the request date
            date = event_data.get('date', datetime.now().strftime("%Y-%m-%d"))
            query_params = {'date': date}

            events_response = await self.calendar_service.query_events(query_params)

            if not events_response.get('success'):
                return "No calendar events available"

            events = events_response.get('events', [])

            # Format events for LLM context
            context = ""
            for i, event in enumerate(events, 1):
                event_name = event.get('summary', 'Untitled')
                start_time = self._extract_time_from_datetime(event.get('start', ''))
                date = self._extract_date_from_datetime(event.get('start', ''))
                calendar_name = event.get('calendar_name', 'Unknown')

                context += f"{i}. {event_name} - {date} at {start_time} ({calendar_name}) [ID: {event.get('id', 'unknown')}]\n"

            return context if context else "No calendar events available"

        except Exception as e:
            logger.error(f"Error getting calendar context: {e}")
            return "Error retrieving calendar events"

    async def _analyze_with_llm(self, user_message: str, calendar_context: str, operation_type: str) -> Dict:
        """Send request to LLM for analysis"""
        try:
            prompt = MULTI_EVENT_OPERATION_PROMPT.format(
                user_message=user_message,
                calendar_events=calendar_context,
                total_events=len(calendar_context.split('\n')) - 1 if calendar_context != "No calendar events available" else 0
            )

            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.1
            )

            result = response['choices'][0]['message']['content']
            logger.info(f"LLM analysis result: {result}")

            # Parse and validate JSON
            operations_data = json.loads(result.strip())
            return operations_data
                
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "intent": "none",
                "message": f"Failed to analyze request: {str(e)}"
            }

    def _format_operations_summary(self, operations_data: Dict) -> str:
        """Format operations summary for user confirmation"""
        operations = operations_data.get('operations', [])
        intent = operations_data.get('intent', 'unknown')

        if not operations:
            return "No operations to perform"

        summary = f"Found {len(operations)} events to {intent}:\n\n"

        for i, op in enumerate(operations, 1):
            op_type = op.get('type', intent)
            event_name = op.get('event_name', 'Unknown Event')
            reason = op.get('reason', '')

            summary += f"{i}. {event_name}"
            if reason:
                summary += f" - {reason}"
            summary += "\n"

        return summary

    def _extract_time_from_datetime(self, datetime_str: str) -> str:
        """Extract time in HH:MM format from datetime string"""
        try:
            if 'T' in datetime_str:
                time_part = datetime_str.split('T')[1]
                if '+' in time_part:
                    time_part = time_part.split('+')[0]
                elif 'Z' in time_part:
                    time_part = time_part.split('Z')[0]
                return time_part[:5]  # HH:MM
            return "00:00"
        except:
            return "00:00"
    
    def _extract_date_from_datetime(self, datetime_str: str) -> str:
        """Extract date in YYYY-MM-DD format from datetime string"""
        try:
            if 'T' in datetime_str:
                return datetime_str.split('T')[0]
            elif len(datetime_str) >= 10:
                return datetime_str[:10]
            return datetime.now().strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")
    
    async def confirm_operation(self, chat_id: int, user_confirmation: str) -> Dict:
        """Simple confirmation processing - LLM has already determined operations"""
        try:
            # Find the most recent pending operation
            pending_op = None
            operation_id = None

            chat_operations = [
                (op_id, op_data) for op_id, op_data in self.pending_operations.items()
                if op_data["chat_id"] == chat_id
            ]

            if chat_operations:
                operation_id, pending_op = chat_operations[-1]

            if not pending_op:
                return {
                    "success": False,
                    "message": "No pending operation found.",
                    "requires_user_action": False
                }
            
            user_response = user_confirmation.lower().strip()

            if user_response in ['yes', 'y', 'confirm', 'proceed', 'all']:
                # Execute operations determined by LLM
                result = await self._execute_llm_operations(pending_op)
                del self.pending_operations[operation_id]
                return result

            elif user_response in ['no', 'n', 'cancel', 'abort']:
                # Cancel operation
                del self.pending_operations[operation_id]
                return {
                    "success": True,
                    "message": "Operation cancelled.",
                    "requires_user_action": False
                }
            
            else:
                return {
                    "success": False,
                    "message": "Please respond with 'yes' to confirm or 'cancel' to abort.",
                    "requires_user_action": True
                }
                
        except Exception as e:
            logger.error(f"Error confirming operation: {e}")
            return {
                "success": False,
                "message": f"Error processing confirmation: {str(e)}",
                "requires_user_action": False
            }
    
    async def _execute_llm_operations(self, operations_data: Dict) -> Dict:
        """Execute operations determined by LLM"""
        try:
            operations = operations_data.get('operations', [])
            intent = operations_data.get('intent', 'unknown')

            if not operations:
                return {
                    "success": False,
                    "message": "No operations to execute"
                }

            successful = 0
            failed = 0
            results = []

            for op in operations:
                try:
                    op_type = op.get('type', intent)
                    event_id = op.get('event_id')

                    if not event_id:
                        failed += 1
                        results.append(f"Missing event ID for {op.get('event_name', 'Unknown')}")
                        continue

                    if op_type == 'delete':
                        result = await self.calendar_service.delete_event(event_id)
                        if result.get('success'):
                            successful += 1
                            results.append(f"✓ Deleted {op.get('event_name', 'Unknown')}")
                        else:
                            failed += 1
                            results.append(f"✗ Failed to delete {op.get('event_name', 'Unknown')}")

                    elif op_type == 'update':
                        # Build update data from LLM response
                        update_data = {
                            'event_id': event_id,
                            'event_name': op.get('new_event_name', op.get('event_name')),
                        }

                        # Add optional update fields
                        for field in ['new_date', 'time_shift', 'new_start_time', 'new_end_time']:
                            if field in op:
                                update_data[field] = op[field]

                        result = self.calendar_service.update_event(event_id, update_data, op.get('calendar_id', 'primary'))
                        if result.get('success'):
                            successful += 1
                            results.append(f"✓ Updated {op.get('event_name', 'Unknown')}")
                        else:
                            failed += 1
                            results.append(f"✗ Failed to update {op.get('event_name', 'Unknown')}")

                except Exception as e:
                    failed += 1
                    results.append(f"✗ Error processing {op.get('event_name', 'Unknown')}: {str(e)}")

            # Format final response
            message = f"Operation complete: {successful} successful, {failed} failed\n\n"
            message += "\n".join(results)

            return {
                "success": successful > 0,
                "message": message
            }

        except Exception as e:
            logger.error(f"Error executing LLM operations: {e}")
            return {
                "success": False,
                "message": f"Error executing operations: {str(e)}"
            }
    

    
    def has_pending_operation(self, chat_id: int) -> bool:
        """Check if there's a pending operation for this chat"""
        return any(op["chat_id"] == chat_id for op in self.pending_operations.values())
    
    def store_pending_operation(self, chat_id: int, operation_data: Dict):
        """Store a pending operation for later processing"""
        import time
        timestamp = time.time()
        operation_id = f"{operation_data.get('intent', 'unknown')}_{chat_id}_{timestamp}"
        self.pending_operations[operation_id] = {
            "chat_id": chat_id,
            "operation_id": operation_id,
            "timestamp": timestamp,
            **operation_data
        }
        logger.debug(f"Stored pending {operation_data.get('intent', 'unknown')} operation {operation_id} for chat {chat_id}")
        return operation_id
    
    def clear_pending_operations(self, chat_id: int):
        """Clear all pending operations for a chat (useful for cleanup)"""
        to_remove = [
            op_id for op_id, op_data in self.pending_operations.items()
            if op_data["chat_id"] == chat_id
        ]
        for op_id in to_remove:
            del self.pending_operations[op_id]
        logger.debug(f"Cleared {len(to_remove)} pending operations for chat {chat_id}")
    
    def clear_all_pending_operations(self):
        """Clear all pending operations (useful for startup cleanup)"""
        self.pending_operations.clear()
        logger.info("Cleared all pending operations on startup")
