"""
Run this script LOCALLY to generate your Pyrogram String Session.
Needed for voice calls (userbot).

Usage:
    python generate_session.py
"""

from pyrogram import Client

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with Client("temp_session", api_id=API_ID, api_hash=API_HASH) as app:
    session_string = app.export_session_string()
    print("\n" + "=" * 60)
    print("YOUR STRING SESSION:")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print("\nCopy the above string and paste it in STRING_SESSION variable.")
    print("Delete temp_session.session file after copying.")
