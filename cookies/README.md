# YouTube Cookies Setup

YouTube blocks many VPS IPs. Use one of these two methods:

## Method 1: Online URL (Recommended for Railway/Heroku)

1. Export your YouTube cookies in **Netscape format** using a browser extension
   - Chrome: "Get cookies.txt LOCALLY" extension
   - Firefox: "cookies.txt" extension

2. Upload the `.txt` file to [batbin.me](https://batbin.me) or [pastebin.com](https://pastebin.com)

3. Copy the raw URL and add it to your `.env`:
   ```
   COOKIES_URL=https://batbin.me/your_paste_url
   ```

4. For multiple cookie files (space separated):
   ```
   COOKIES_URL=https://batbin.me/url1 https://batbin.me/url2
   ```

## Method 2: Local File (For VPS)

1. Export cookies in Netscape format
2. Save the file as `cookies/cookies.txt`
3. The bot will automatically detect and use it

## Notes
- Cookies must be in **Netscape format**
- Keep cookies fresh - YouTube cookies expire
- Never share your cookie file publicly
