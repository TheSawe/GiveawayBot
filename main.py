from telethon import TelegramClient, events
from telethon.tl import types
import webbrowser
import subprocess
import pyautogui
import asyncio
import time
import re
from telethon import utils

api_id = 23857603
api_hash = '9be22fb9244d6b0cc71e968ce198029a'
phone = '+79224274002'

button_in_miniapp_x = 657
button_in_miniapp_y = 743

close_miniapp_x = 471
close_miniapp_y = 111

client = TelegramClient('giveaway_bot', api_id, api_hash)

processing_counter = 0
cooldown_active = False
cooldown_task = None

async def reset_cooldown():
    global processing_counter, cooldown_active, cooldown_task
    await asyncio.sleep(1000)  # Таймер 1000 секунд
    processing_counter = 0
    cooldown_active = False
    cooldown_task = None
    print("Таймер сброшен, обработка возобновлена")

async def main():
    try:
        await client.start(phone)
        print("Client started")
        await client.run_until_disconnected()
    except Exception as e:
        print("Error connecting to Telegram", e)
    finally:
        if client.is_connected():
            await client.disconnect()
            print("Disconnected")


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

        if tab_count >= 10:
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
            print("Вкладки Brave Browser закрыты (оставлена одна).")
        else:
            print(f"Количество вкладок в Brave Browser: {tab_count}.  Закрытие не требуется.")


    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения AppleScript: {e}")
    except ValueError as e:
        print(
            f"Ошибка преобразования результата AppleScript в число: {e} (result: {result.stdout.strip() if 'result' in locals() else 'Нет результата'})")

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


def extract_links_from_entities(message):

    links = []
    if message.entities:
        for entity in message.entities:
            if isinstance(entity, types.MessageEntityTextUrl):
                links.append(entity.url)

            elif isinstance(entity, types.MessageEntityUrl):
                links.append(utils.get_text(message)[entity.offset:entity.offset + entity.length])
    return links


async def process_giveaway_message(message):
    if message.text:
        usernames = re.findall(r'@([a-zA-Z0-9_]+)', message.text)
        if usernames:
            print("Найдены упоминания каналов/пользователей:")
            for username in usernames:
                full_username = '@' + username
                print(f"  - {full_username}")
                try:
                    entity = await client.get_entity(full_username)
                    if isinstance(entity, types.Channel): # Исправлено: убрано types.Group
                        from telethon.tl.functions.channels import JoinChannelRequest
                        await client(JoinChannelRequest(entity))
                        print(f"    Успешно подписался на канал: {full_username}")
                    elif isinstance(entity, types.User): # Добавлено: проверка на types.User
                        print(f"    {full_username} - это пользователь, подписка не требуется.")
                    else:
                        print(f"    {full_username} - это не канал и не пользователь, подписка пропущена.")  # Изменен вывод
                except Exception as e:
                    print(f"    Ошибка при подписке на {full_username}: {e}")

    if "Gift Giveaway" in message.text:
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if isinstance(button, types.KeyboardButtonUrl):
                        print(f"\nURL: {button.url}")
                        webbrowser.open(button.url)
        time.sleep(6)
        pyautogui.click(button_in_miniapp_x, button_in_miniapp_y)
        close_brave_tabs()
        time.sleep(1)
        pyautogui.click(close_miniapp_x, close_miniapp_y)

    if "Розыгрыш" in message.text and "GiveShareBot" in extract_links_from_entities(message)[0]:
        print(f"Найдено сообщение со словом 'Розыгрыш': {message.text}")
        links = extract_links_from_entities(message)
        for link in links:
            print(link)
            webbrowser.open(link)


@client.on(events.NewMessage)
async def new_message_handler(event):
    global processing_counter, cooldown_active, cooldown_task

    chat = await event.get_chat()
    if hasattr(chat, 'username') and str(chat.username).lower() == 'gift3111' and "первым" in str(event.message.text).lower() :

        try:
            await event.reply('f')
            print("Отправлен комментарий 'f' в канале gift3111")
        except Exception as e:
            print(f"Ошибка при отправке комментария: {e}")
        return

    if not cooldown_active:

        message = event.message
        if "Gift Giveaway" in message.text and "joining fee" not in str(message.text).lower():
            processing_counter += 1
            await process_giveaway_message(message)

        if processing_counter >= 30 and not cooldown_task:
            cooldown_active = True
            cooldown_task = asyncio.create_task(reset_cooldown())
            print("Достигнут лимит 30 обработок, запущен таймер 1000 сек")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except Exception as e:
        print(f"Exception caught in loop: {e}")
    finally:
        loop.close()
        print("Program ended")