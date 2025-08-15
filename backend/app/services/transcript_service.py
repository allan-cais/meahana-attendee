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
        logger.info(f"🌐 Starting transcript fetch for bot {bot_id}")
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {settings.attendee_api_key}",
                "Content-Type": "application/json",
            }
            
            try:
                api_url = f"{settings.attendee_api_base_url}/api/v1/bots/{bot_id}/transcript"
                logger.info(f"📡 Making request to: {api_url}")
                
                response = await client.get(
                    api_url,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"📥 Received response from Attendee API: {type(data)}")
                
                # Handle different response formats from Attendee API
                if isinstance(data, list):
                    # API returned transcript list directly
                    transcript_chunks = data
                    logger.info(f"📋 API returned list with {len(data)} items")
                elif isinstance(data, dict):
                    # API returned JSON object with transcript key
                    transcript_chunks = data.get("transcript", [])
                    logger.info(f"📋 API returned dict with transcript key containing {len(transcript_chunks)} items")
                else:
                    logger.error(f"❌ Unexpected response format from Attendee API: {type(data)}")
                    transcript_chunks = []
                
                logger.info(f"🔧 About to process {len(transcript_chunks)} transcript chunks")
                
                # Process and store transcript chunks using a new database session
                await self._process_transcript_chunks_new_session(bot_id, transcript_chunks)
                
                logger.info(f"✅ Successfully fetched transcript for bot {bot_id}")
                return transcript_chunks
                
            except httpx.HTTPError as e:
                logger.error(f"❌ HTTP error fetching transcript: {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Error fetching transcript: {e}")
                import traceback
                logger.error(f"📚 Traceback: {traceback.format_exc()}")
                raise

    async def _process_transcript_chunks_new_session(
        self,
        bot_id: str,
        transcript_chunks: List[Dict[str, Any]]
    ):
        """Process and store transcript chunks using a new database session"""
        logger.info(f"🔧 Processing {len(transcript_chunks)} transcript chunks for bot {bot_id}")
        
        # Create a new database session
        async for db in get_db():
            try:
                # Get meeting by bot_id
                from app.services.bot_service import BotService
                logger.info(f"🔍 Looking up meeting for bot_id: {bot_id}")
                meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
                
                if not meeting:
                    logger.error(f"❌ Meeting not found for bot_id: {bot_id}")
                    return
                
                logger.info(f"✅ Found meeting {meeting.id} for bot {bot_id}")
                
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
                            logger.warning(f"⚠️ Skipping chunk with None text: speaker={speaker}, timestamp={timestamp_str}")
                            continue
                            
                        if timestamp_str is None:
                            logger.warning(f"⚠️ Skipping chunk with None timestamp: speaker={speaker}, text={text[:50] if text else 'None'}...")
                            continue
                        
                        # Safe logging - only slice text if it exists
                        text_preview = text[:50] + "..." if text and len(text) > 50 else text
                        logger.info(f"📝 Processing chunk: speaker={speaker}, text={text_preview}, timestamp={timestamp_str}")
                        
                        if not text or not timestamp_str:
                            logger.warning(f"⚠️ Skipping chunk with missing data: speaker={speaker}, text={text}, timestamp={timestamp_str}")
                            continue
                        
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Check if chunk already exists
                        logger.info(f"🔍 Checking if chunk already exists for meeting {meeting.id}")
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
                            logger.info(f"➕ Creating new transcript chunk for meeting {meeting.id}")
                            chunk = TranscriptChunk(
                                meeting_id=meeting.id,
                                speaker=speaker,
                                text=text,
                                timestamp=timestamp
                            )
                            db.add(chunk)
                            processed_count += 1
                            logger.info(f"✅ Added new transcript chunk: {speaker}: {text_preview}")
                        else:
                            logger.info(f"ℹ️ Transcript chunk already exists, skipping")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing transcript chunk: {e}")
                        import traceback
                        logger.error(f"📚 Chunk processing traceback: {traceback.format_exc()}")
                        continue
                
                logger.info(f"💾 Committing {processed_count} new transcript chunks to database")
                await db.commit()
                logger.info(f"✅ Successfully processed {processed_count} new transcript chunks for meeting {meeting.id}")
                
            except Exception as e:
                logger.error(f"❌ Error in _process_transcript_chunks_new_session: {e}")
                import traceback
                logger.error(f"📚 Full traceback: {traceback.format_exc()}")
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
        logger.info(f"🔧 Processing {len(transcript_chunks)} transcript chunks for bot {bot_id}")
        
        try:
            # Get meeting by bot_id
            from app.services.bot_service import BotService
            logger.info(f"🔍 Looking up meeting for bot_id: {bot_id}")
            meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
            
            if not meeting:
                logger.error(f"❌ Meeting not found for bot_id: {bot_id}")
                return
            
            logger.info(f"✅ Found meeting {meeting.id} for bot {bot_id}")
            
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
                    
                    logger.info(f"📝 Processing chunk: speaker={speaker}, text={text[:50]}..., timestamp={timestamp_str}")
                    
                    if not text or not timestamp_str:
                        logger.warning(f"⚠️ Skipping chunk with missing data: speaker={speaker}, text={text}, timestamp={timestamp_str}")
                        continue
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Check if chunk already exists
                    logger.info(f"🔍 Checking if chunk already exists for meeting {meeting.id}")
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
                        logger.info(f"➕ Creating new transcript chunk for meeting {meeting.id}")
                        chunk = TranscriptChunk(
                            meeting_id=meeting.id,
                            speaker=speaker,
                            text=text,
                            timestamp=timestamp
                        )
                        db.add(chunk)
                        processed_count += 1
                        logger.info(f"✅ Added new transcript chunk: {speaker}: {text[:50]}...")
                    else:
                        logger.info(f"ℹ️ Transcript chunk already exists, skipping")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing transcript chunk: {e}")
                    import traceback
                    logger.error(f"📚 Chunk processing traceback: {traceback.format_exc()}")
                    continue
            
            logger.info(f"💾 Committing {processed_count} new transcript chunks to database")
            await db.commit()
            logger.info(f"✅ Successfully processed {processed_count} new transcript chunks for meeting {meeting.id}")
            
        except Exception as e:
            logger.error(f"❌ Error in _process_transcript_chunks: {e}")
            import traceback
            logger.error(f"📚 Full traceback: {traceback.format_exc()}")
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