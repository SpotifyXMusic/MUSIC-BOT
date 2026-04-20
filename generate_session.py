"""Run this LOCALLY to get your STRING_SESSION"""
from pyrogram import Client

API_ID   = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with Client("temp", api_id=API_ID, api_hash=API_HASH) as app:
    session = app.export_session_string()
    print("\n" + "="*60)
    print("STRING_SESSION:")
    print("="*60)
    print(session)
    print("="*60)
    print("\nCopy this and put in Railway Variables as STRING_SESSION")
    print("Delete temp.session file after copying!")
