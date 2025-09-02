#!/usr/bin/env python3
"""Test Supabase connection to debug connection issues"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def test_connection():
    """Test the database connection"""
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    print(f"Testing connection to: {database_url}")
    
    try:
        # Parse the connection string manually
        if database_url.startswith('postgresql+asyncpg://'):
            database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        print(f"Modified URL: {database_url}")
        
        # Try to connect with a longer timeout
        conn = await asyncio.wait_for(
            asyncpg.connect(database_url),
            timeout=30.0
        )
        
        print("✅ Connection successful!")
        
        # Test a simple query
        result = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {result}")
        
        await conn.close()
        
    except asyncio.TimeoutError:
        print("❌ Connection timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
