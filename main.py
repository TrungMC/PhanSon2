from io import BytesIO

import chat_downloader.errors
import streamlit as st
import requests
import pandas as pd
from chat_downloader import ChatDownloader
from pytube import Playlist, YouTube
import pickle
import json


def get_chat_replay(video_id):
    chat = ChatDownloader().get_chat("https://www.youtube.com/watch?v=" + video_id)
    return chat


def get_live_videos(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={api_key}"
    response = requests.get(url)
    data = response.json()
    # print(data)
    return data['items']


def get_past_streams(channel_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=completed&type=video&key={api_key}"
    next_page_token = None
    items = []
    while True:
        response = requests.get(url + (f"&pageToken={next_page_token}" if next_page_token else ""))
        # print(response.content)
        data = response.json()
        items.extend(data['items'])
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return items


def chat_content_to_df(chat_content):
    excel_lines = []
    for message in chat_content:
        image_url = next(image['url'] for image in message['author']['images'] if image['id'] == '32x32')
        if '?' in message['message']:
            excel_lines.append([message['author']['name'], message['message'], '1', message['message_type'],
                                message['time_in_seconds'], message['author']['id'], image_url])
        else:
            excel_lines.append([message['author']['name'], message['message'], '0', message['message_type'],
                                message['time_in_seconds'], message['author']['id'], image_url])
    df = pd.DataFrame(excel_lines,
                      columns=['Author', 'Message', 'IsQuestion', 'MessageType', 'TimeinSeconds', 'AuthorID', 'Avatar'])
    return df


def export_chat_to_excel(df):
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    return excel_file


# {'time_in_seconds': 4996.176, 'action_type': 'add_chat_item', 'message': 'không sao đâu phan sơn mọi người hiểu mà', 'message_id': 'ChwKGkNNaTlxZWpqMF84
# Q0ZiekN3Z1FkdXo0RHdR', 'timestamp': 1687330465952199, 'time_text': '1:23:16', 'author': {'name': 'Nhuan Nguyen', 'images': [{'url': 'https://yt4.ggpht.c
# om/ytc/AGIKgqPcobXNPeQK77zSEBul3kQeVJIr8CCsI38e-U4l84wWl7B6ablqzezVoGsI20ED', 'id': 'source'}, {'url': 'https://yt4.ggpht.com/ytc/AGIKgqPcobXNPeQK77zSEB
# ul3kQeVJIr8CCsI38e-U4l84wWl7B6ablqzezVoGsI20ED=s32-c-k-c0x00ffffff-no-rj', 'width': 32, 'height': 32, 'id': '32x32'}, {'url': 'https://yt4.ggpht.com/ytc
# /AGIKgqPcobXNPeQK77zSEBul3kQeVJIr8CCsI38e-U4l84wWl7B6ablqzezVoGsI20ED=s64-c-k-c0x00ffffff-no-rj', 'width': 64, 'height': 64, 'id': '64x64'}], 'id': 'UCOhU-eP4o6FilWm3Rrb1y8Q'}, 'message_type': 'text_message'}

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
    question_only = st.sidebar.checkbox('Question Only', value="True")
    css = """
    <style>
      .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        overflow: hidden;
        display: inline-block;
        vertical-align: middle;
      }
    </style>
    """

    st.write(css, unsafe_allow_html=True)

    if selected_video_title is not None:

        selected_video_id = selected_video_title
        metadata = YouTube('https://www.youtube.com/watch?v=' + selected_video_id)

        url = f'https://www.youtube.com/watch?v={selected_video_id}'
        try:
            chat_replay = get_chat_replay(selected_video_id)
            df = chat_content_to_df(chat_replay)

            col1, col2, col3 = st.columns(3)
            if col1.button("Export Chat to Excel"):
                # Export chat content to Excel

                excel_file = export_chat_to_excel(df)
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

            if question_only:
                display_df = df[df["IsQuestion"] == '1']
            else:
                display_df = df
            print(display_df)
            for index, l in display_df.iterrows():
                st.markdown(
                    f"<div><div class='avatar'><img src='{l.Avatar}' alt='{l.Author}'></img></div> <b>{l.Author}</b> : {l.Message}</div>",
                    unsafe_allow_html=True)

        except chat_downloader.errors.NoChatReplay:
            st.error('No Chat Replay for this Video')


if __name__ == '__main__':
    main()
