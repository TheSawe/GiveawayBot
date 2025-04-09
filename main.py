from telethon.tl.functions.channels import JoinChannelRequest
from telethon import TelegramClient, events
from telethon.tl import types
import webbrowser
import subprocess
import pyautogui
from datetime import datetime
import asyncio
import re
from config import *

client = TelegramClient(session_name, api_id, api_hash)

async def reset_cooldown():
    global processing_counter, cooldown_active
    await asyncio.sleep(time2sleep)
    processing_counter = 0
    cooldown_active = False
    print("Non-spamblock break ended")

async def main():
    try:
        await client.start(phone)
        print(f"[{str(datetime.now())[:-7]}] Client started")
        await client.run_until_disconnected()
    except Exception as e:
        print("Wrong phone number or security code", e)
    finally:
        if client.is_connected():
            await client.disconnect()
            print(f"[{str(datetime.now())[:-7]}] Client ended")


def close_brave_tabs():
    try:
        count_tabs_script = """
        tell application "Brave Browser"
            set window_count to count of windows
            set tab_count to 0
            repeat with i from 1 to window_count
                set tab_count to tab_count + (count of tabs of window i)
            end repeat
            return tab_count
        end tell
        """

        result = subprocess.run(['osascript', '-e', count_tabs_script], capture_output=True, text=True, check=True)
        tab_count = int(result.stdout.strip())

        if tab_count >= max_tabs2open:
            close_tabs_script = """
            tell application "Brave Browser"
                set window_count to count windows
                repeat with i from 1 to window_count
                    set tab_count to (count of tabs of window i)

                    -- Закрываем все вкладки, кроме последней в каждом окне
                    repeat while tab_count > 1
                        close tab 1 of window i
                        set tab_count to (count of tabs of window i)
                     end repeat
                end repeat
            end tell
            """
            subprocess.run(['osascript', '-e', close_tabs_script], check=True)


    except subprocess.CalledProcessError as ae:
        print(f"[{str(datetime.now())[:-7]}] AppleScript error: {ae}")
    except ValueError as ve:
        print(f"[{str(datetime.now())[:-7]}] AppleScript value error: {ve}")
    except Exception as ex:
        print(f"[{str(datetime.now())[:-7]}] Unexpected error: {ex}")


def extract_giveaway_link(message):
    if message.reply_markup:
        for row in message.reply_markup.rows:
            for button in row.buttons:
                if isinstance(button, types.KeyboardButtonUrl):
                    url = button.url
                    return url


async def join_channels(message):
    if message.text:
        usernames = re.findall(r'@([a-zA-Z0-9_]+)', message.text)
        if usernames:
            for username in usernames:
                full_username = '@' + username
                try:
                    entity = await client.get_entity(full_username)
                    if isinstance(entity, types.Channel):
                        await client(JoinChannelRequest(entity))
                except Exception as se:
                    print(f"[{str(datetime.now())[:-7]}] Subscribe {full_username} error: {se}")

async def process_giveaway_message(message):
    await join_channels(message)

    if "Gift Giveaway" in message.text:
        url = extract_giveaway_link(message)
        print(f"[{str(datetime.now())[:-7]}] Tonnel: {url}")
        webbrowser.open(url)
        await asyncio.sleep(6)
        pyautogui.click(participate_button_x, participate_button_y)
        close_brave_tabs()
        await asyncio.sleep(1)
        pyautogui.click(close_button_x, close_button_y)

    if "https://t.me/BestRandom_bot?start=" in extract_giveaway_link(message):
        url = extract_giveaway_link(message)
        print(f"[{str(datetime.now())[:-7]}] BestRandom: {url}")
        webbrowser.open(url)
        close_brave_tabs()


@client.on(events.NewMessage(incoming=True))
async def new_message_handler(event):
    global processing_counter, cooldown_active, cooldown_task

    if not event.message.text:
        return

    # if "первым" in str(event.message.text).lower():
    #     try:
    #         for i in range(3):
    #             await client.send_message(
    #                 entity=-1002555136778,
    #                 message='f',
    #                 reply_to=event.message.id
    #             )
    #             print("Комментарий 'f' отправлен в группу обсуждений")
    #     except Exception as e:
    #         print(f"Ошибка: {e}")

    message = event.message
    if "https://t.me/BestRandom_bot?start=" in str(extract_giveaway_link(message)):
        await process_giveaway_message(message)

    if not cooldown_active:

        message = event.message
        if "Gift Giveaway" in message.text and "joining fee" not in str(message.text).lower():
            processing_counter += 1
            await process_giveaway_message(message)

        if processing_counter >= participate2sleep:
            cooldown_active = True
            cooldown_task = asyncio.create_task(reset_cooldown())
            print(f"[{str(datetime.now())[:-7]}] Достигнут лимит {participate2sleep} обработок, запущен таймер {time2sleep} сек")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        print(f"[{str(datetime.now())[:-7]}] {e}")
    finally:
        loop.close()