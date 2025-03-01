from pyrogram import Client, types
from pyvis.network import Network

import asyncio
import networkx as nx
import signal
import sys
from data import API_ID, API_HASH, tel
# Создание графа
G = nx.Graph()

# Цвета для узлов
CHANNEL_COLOR = "lightblue"
USER_COLOR = "lightgreen"
REPOSTED_CHANNEL_COLOR = "coral"

# Создание интерактивного графа
net = Network(notebook=True, height="750px", width="100%")

# Флаг для graceful shutdown
shutdown = False


def create_ascii():
    ___= """

 _              ___                                          
( )_           (  _`\                                        
| ,_)   __     | (_(_)   ___    _ _  ___    ___     __  _ __ 
| |   /'_ `\   `\__ \  /'___) /'_` )' _ `\/' _ `\ /'__`( '__)
| |_ ( (_) |   ( )_) |( (___ ( (_| | ( ) || ( ) |(  ___/ |   
`\__)`\__  |   `\____)`\____)`\__,_|_) (_)(_) (_)`\____|_)   
     ( )_) |                                                 
      \___/' 


   _______
  /        \\
 /          \\
|   АНАЛИЗ   |
 _______/
  |       |
  |  START  |
  |_______|
    """
    print(___)



def signal_handler(sig, frame):
    """
    Обработчик сигнала для graceful shutdown.
    """
    global shutdown
    print("\nЗавершение работы...")
    shutdown = True
    # Сохраняем граф перед выходом
    save_graph()
    sys.exit(0)

def save_graph():
    """
    Сохраняет граф в HTML-файл.
    """
    print("Сохранение графа...")
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])
    net.show("граф.html")
    print("Граф успешно сохранен в файл 'граф.html'.")

# Регистрируем обработчик сигнала
signal.signal(signal.SIGINT, signal_handler)

async def get_dialogues(app):
    """
    Функция для получения списка каналов и их ID.
    """
    list_ = []
    async for dialogue in app.get_dialogs():
        chat = dialogue.chat
        if chat.title:
            list_.append([len(list_), chat.id, chat.title])

        # if str(chat.type) == 'ChatType.CHANNEL':
        #     print([len(list_), chat.title, chat.id])
        # else:
        #     pass

    return list_

async def scan_channel(app, number_):
    """
    Функция для сканирования канала и добавления данных в граф.
    """
    try:
        # Получаем информацию о канале
        channel = await app.get_chat(number_)
        channel_title = channel.title
        print(f"Канал найден: {channel_title}")

        # Добавляем узел для сканируемого канала
        G.add_node(channel_title, title=f"Информация о {channel_title}", color=CHANNEL_COLOR)

        # Сканируем сообщения в канале
        async for message in app.get_chat_history(number_, limit=1000):
            if shutdown:
                break  # Прерываем, если получен сигнал завершения

            if message.forward_from:
                # Репост от пользователя
                if isinstance(message.forward_from, types.User):
                    user = message.forward_from
                    user_name = user.first_name
                    user_id = user.id
                    username = user.username if user.username else "Нет username"

                    # Добавляем узел для пользователя
                    G.add_node(user_name, title=f"ID: {user_id}, Username: {username}", color=USER_COLOR)
                    # Добавляем ребро между каналом и пользователем
                    G.add_edge(channel_title, user_name)

                    print(f"Репост от пользователя: {user_name}, ID: {user_id}, Username: {username}")

            elif message.forward_from_chat:
                # Репост из другого канала/группы
                if isinstance(message.forward_from_chat, types.Chat):
                    reposted_chat = message.forward_from_chat
                    reposted_chat_title = reposted_chat.title
                    reposted_chat_id = reposted_chat.id
                    reposted_chat_username = reposted_chat.username if reposted_chat.username else "Нет username"

                    # Добавляем узел для репостнутого канала
                    G.add_node(reposted_chat_title, title=f"ID: {reposted_chat_id}, Username: {reposted_chat_username}", color=REPOSTED_CHANNEL_COLOR)
                    # Добавляем ребро между каналами
                    G.add_edge(channel_title, reposted_chat_title)

                    print(f"Репост из канала/группы: {reposted_chat_title}, ID: {reposted_chat_id}, Username: {reposted_chat_username}")

                    # Рекурсивное сканирование репостнутого канала
                    await recursive_scan(app, reposted_chat_id)

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        print("Сканирование завершено.")

async def recursive_scan(app, channel_id, depth=1, max_depth=3):
    """
    Рекурсивная функция для сканирования каналов.
    """
    if depth > max_depth or shutdown:
        return  # Ограничиваем глубину рекурсии или завершаем при shutdown

    try:
        # Получаем информацию о канале
        channel = await app.get_chat(channel_id)
        channel_title = channel.title
        print(f"Рекурсивное сканирование: {channel_title} (глубина {depth})")

        # Добавляем узел для канала
        G.add_node(channel_title, title=f""" 
            Информация о {channel_title}:
            name - @{channel.username}
            id - {channel_id}
            members - {channel.members_count}
            """
            , color=CHANNEL_COLOR)

        # Сканируем сообщения в канале
        async for message in app.get_chat_history(channel_id, limit=175):
            if shutdown:
                break  # Прерываем, если получен сигнал завершения

            if message.forward_from:
                # Репост от пользователя
                if isinstance(message.forward_from, types.User):
                    user = message.forward_from
                    user_name = user.first_name
                    user_id = user.id
                    username = user.username if user.username else "Нет username"

                    # Добавляем узел для пользователя
                    G.add_node(user_name, title=f"ID: {user_id}, Username: {username}", color=USER_COLOR)
                    # Добавляем ребро между каналом и пользователем
                    G.add_edge(channel_title, user_name)

                    print(f"Репост от пользователя: {user_name}, ID: {user_id}, Username: {username}")

            elif message.forward_from_chat:
                # Репост из другого канала/группы
                if isinstance(message.forward_from_chat, types.Chat):
                    reposted_chat = message.forward_from_chat
                    reposted_chat_title = reposted_chat.title
                    reposted_chat_id = reposted_chat.id
                    reposted_chat_username = reposted_chat.username if reposted_chat.username else "Нет username"

                    chan = await app.get_chat(reposted_chat_id)



                    # Добавляем узел для репостнутого канала
                    G.add_node(reposted_chat_title, title=f"ID: {reposted_chat_id}, Username: {reposted_chat_username},  members - {chan.members_count} ", color=REPOSTED_CHANNEL_COLOR)
                    # Добавляем ребро между каналами
                    G.add_edge(channel_title, reposted_chat_title)

                    print(f"Репост из канала/группы: {reposted_chat_title}, ID: {reposted_chat_id}, Username: {reposted_chat_username}")

                    # Рекурсивное сканирование репостнутого канала
                    await recursive_scan(app, reposted_chat_id, depth + 1, max_depth)

    except Exception as e:
        print(f"Ошибка при рекурсивном сканировании: {e}")

async def main():
    """
    Основная функция для запуска программы.
    """
    global shutdown
    async with Client("my_account", API_ID, API_HASH, phone_number=tel) as app:
        # Получаем список каналов
        list_ = await get_dialogues(app)
        print("Список каналов:")
        for item in list_:
            print(f"ID: {item[1]}, Название: {item[2]}")

        # Запрашиваем канал для сканирования
        chat_number_ = input("Укажи ID канала, который нужно просканировать: ")
        await scan_channel(app, chat_number_)

        # Визуализация графа
        save_graph()

if __name__ == "__main__":
    try:
        create_ascii()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Программа завершена пользователем.")
        # Сохраняем граф перед выходом
        save_graph()