import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, TranscriptChunk
from app.core.config import settings
from app.core.database import get_db
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TranscriptService:
    async def fetch_full_transcript(
        self, 
        db: AsyncSession, 
        bot_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch full transcript from Attendee API"""
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {settings.attendee_api_key}",
                "Content-Type": "application/json",
            }
            
            try:
                api_url = f"{settings.attendee_api_base_url}/api/v1/bots/{bot_id}/transcript"
                
                response = await client.get(
                    api_url,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle different response formats from Attendee API
                if isinstance(data, list):
                    # API returned transcript list directly
                    transcript_chunks = data
                elif isinstance(data, dict):
                    # API returned JSON object with transcript key
                    transcript_chunks = data.get("transcript", [])
                else:
                    logger.error(f"Unexpected response format from Attendee API: {type(data)}")
                    transcript_chunks = []
                
                # Process and store transcript chunks using a new database session
                await self._process_transcript_chunks_new_session(bot_id, transcript_chunks)
                
                return transcript_chunks
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching transcript: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching transcript: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

    async def _process_transcript_chunks_new_session(
        self,
        bot_id: str,
        transcript_chunks: List[Dict[str, Any]]
    ):
        """Process and store transcript chunks using a new database session"""
        
        # Create a new database session
        async for db in get_db():
            try:
                # Get meeting by bot_id
                from app.services.bot_service import BotService
                meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
                
                if not meeting:
                    logger.error(f"Meeting not found for bot_id: {bot_id}")
                    return
                
                processed_count = 0
                for chunk_data in transcript_chunks:
                    try:
                        # Handle Attendee API response format
                        speaker = chunk_data.get("speaker_name") or chunk_data.get("speaker")
                        text = chunk_data.get("transcription", {}).get("transcript") or chunk_data.get("text")
                        timestamp_ms = chunk_data.get("timestamp_ms")
                        timestamp_str = chunk_data.get("timestamp")
                        
                        # Convert timestamp_ms to ISO format if available
                        if timestamp_ms and not timestamp_str:
                            from datetime import datetime
                            timestamp_str = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
                        
                        # Better validation - check for None values before logging
                        if text is None:
                            logger.warning(f"Skipping chunk with None text: speaker={speaker}, timestamp={timestamp_str}")
                            continue
                            
                        if timestamp_str is None:
                            logger.warning(f"Skipping chunk with None timestamp: speaker={speaker}, text={text[:50] if text else 'None'}...")
                            continue
                        
                        if not text or not timestamp_str:
                            logger.warning(f"Skipping chunk with missing data: speaker={speaker}, text={text}, timestamp={timestamp_str}")
                            continue
                        
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Check if chunk already exists
                        result = await db.execute(
                            select(TranscriptChunk).where(
                                TranscriptChunk.meeting_id == meeting.id,
                                TranscriptChunk.timestamp == timestamp,
                                TranscriptChunk.speaker == speaker
                            )
                        )
                        existing_chunk = result.scalar_one_or_none()
                        
                        if not existing_chunk:
                            # Create new chunk
                            chunk = TranscriptChunk(
                                meeting_id=meeting.id,
                                speaker=speaker,
                                text=text,
                                timestamp=timestamp
                            )
                            db.add(chunk)
                            processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing transcript chunk: {e}")
                        import traceback
                        logger.error(f"Chunk processing traceback: {traceback.format_exc()}")
                        continue
                
                # Don't commit here - let the calling transaction handle it
                
            except Exception as e:
                logger.error(f"Error in _process_transcript_chunks_new_session: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise
            finally:
                # Ensure the session is closed
                await db.close()
            break

    async def _process_transcript_chunks(
        self,
        db: AsyncSession,
        bot_id: str,
        transcript_chunks: List[Dict[str, Any]]
    ):
        """Process and store transcript chunks (legacy method - kept for compatibility)"""
        
        try:
            # Get meeting by bot_id
            from app.services.bot_service import BotService
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            
            if not meeting:
                logger.error(f"Meeting not found for bot_id: {bot_id}")
                return
            
            processed_count = 0
            for chunk_data in transcript_chunks:
                try:
                    # Handle Attendee API response format
                    speaker = chunk_data.get("speaker_name") or chunk_data.get("speaker")
                    text = chunk_data.get("transcription", {}).get("transcript") or chunk_data.get("text")
                    timestamp_ms = chunk_data.get("timestamp_ms")
                    timestamp_str = chunk_data.get("timestamp")
                    
                    # Convert timestamp_ms to ISO format if available
                    if timestamp_ms and not timestamp_str:
                        from datetime import datetime
                        timestamp_str = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
                    
                    if not text or not timestamp_str:
                        logger.warning(f"Skipping chunk with missing data: speaker={speaker}, text={text}, timestamp={timestamp_str}")
                        continue
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Check if chunk already exists
                    result = await db.execute(
                        select(TranscriptChunk).where(
                            TranscriptChunk.meeting_id == meeting.id,
                            TranscriptChunk.timestamp == timestamp,
                            TranscriptChunk.speaker == speaker
                        )
                    )
                    existing_chunk = result.scalar_one_or_none()
                    
                    if not existing_chunk:
                        # Create new chunk
                        chunk = TranscriptChunk(
                            meeting_id=meeting.id,
                            speaker=speaker,
                            text=text,
                            timestamp=timestamp
                        )
                        db.add(chunk)
                        processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing transcript chunk: {e}")
                    import traceback
                    logger.error(f"Chunk processing traceback: {traceback.format_exc()}")
                    continue
            
            # Don't commit here - let the calling transaction handle it
            
        except Exception as e:
            logger.error(f"Error in _process_transcript_chunks: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def get_transcript_chunks(
        self, 
        db: AsyncSession, 
        meeting_id: int
    ) -> List[TranscriptChunk]:
        """Get transcript chunks for a meeting"""
        result = await db.execute(
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.timestamp)
        )
        return result.scalars().all() 