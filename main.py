from io import BytesIO

import chat_downloader.errors
import streamlit as st
import requests
import pandas as pd
from chat_downloader import ChatDownloader
from pytube import Playlist, YouTube


def get_chat_replay(video_id):
    chat = ChatDownloader().get_chat("https://www.youtube.com/watch?v=" + video_id,
                                     )

    return chat


def get_live_videos(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={api_key}"
    response = requests.get(url)
    data = response.json()
    print(data)
    return data['items']


def get_past_streams(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=completed&type=video&key={api_key}"
    next_page_token = None
    items = []
    while True:
        response = requests.get(url + (f"&pageToken={next_page_token}" if next_page_token else ""))
        print(response.content)
        data = response.json()
        items.extend(data['items'])
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return items


def export_chat_to_excel(chat_content):
    excel_lines=[]
    for message in chat_content:
        if '?' in message['message']:
            excel_lines.append([message['author']['name'],message['message']])

    df = pd.DataFrame(excel_lines,
                      columns=['Author', 'Message'])

    # df.to_excel(file_name, index=False)
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    return excel_file


def main():
    st.title("Hỏi đáp giao lưu kênh Phan Sơn")

    # Get user input for the YouTube channel ID
    channel_id = 'UC8--QWuH0jOhJ3Dg7UZclRg'  # st.text_input("Enter YouTube Channel ID:")
    api_key = 'AIzaSyBZjNz0kcBmzHgnjVJ6mxu9ccluWORoyZk'  # st.text_input("Enter YouTube API Key:")
    playlist_id = 'https://www.youtube.com/playlist?list=PLBxF30HXWgHivPqOlIKVMIhl6tJxzi_W3'

    playlist = Playlist(playlist_id)
    all_videos = []
    for url in playlist:
        all_videos.append(url.replace('https://www.youtube.com/watch?v=', ''))

    # # Create a sidebar dropdown box to select a video
    selected_video_title = st.sidebar.selectbox("Select a Video. Most recent at top", options=all_videos)

    if selected_video_title is not None:

        selected_video_id = selected_video_title
        metadata = YouTube('https://www.youtube.com/watch?v=' + selected_video_id)
        print(metadata.title)
        # Retrieve chat content for the selected video
        url = f'https://www.youtube.com/watch?v={selected_video_id}'
        try:
            chat_replay = get_chat_replay(selected_video_id)

            col1, col2, col3 = st.columns(3)
            if col1.button("Export Chat to Excel"):
                # Export chat content to Excel

                excel_file = export_chat_to_excel(chat_replay)
                file_name = f'{selected_video_id}.xlsx'
                col2.download_button(
                    label="Download data as Excel",
                    data=excel_file,
                    file_name=file_name,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                st.success(f"Chat content exported to '{file_name}'")

            # Display the chat content
            st.subheader(metadata.title)

            for message in chat_replay:
                if '?' in message['message']:
                    st.markdown(f"<div>- <b>{message['author']['name']}</b>:{message['message']}</div>",unsafe_allow_html=True                                )

        except chat_downloader.errors.NoChatReplay:
            st.error('No Chat Replay for this Video')


if __name__ == '__main__':
    main()
