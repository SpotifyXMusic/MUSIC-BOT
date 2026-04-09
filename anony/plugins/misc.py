"""Misc Plugin - Inline mode"""
from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from anony.helpers.youtube import youtube_search, format_views

@Client.on_inline_query()
async def inline_query_handler(client: Client, inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        return await inline_query.answer([], cache_time=1)
    results_data = await youtube_search(query, limit=5)
    results = []
    for r in results_data:
        results.append(InlineQueryResultArticle(
            title=r["title"][:64],
            description=f"{r['duration']} | {r['channel']} | {format_views(r['views'])} views",
            input_message_content=InputTextMessageContent(f"/play {r['url']}"),
            thumb_url=r["thumbnail"],
        ))
    await inline_query.answer(results, cache_time=5)
