
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import time
import os

# --- CONFIGURATION ---
CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
REDIRECT_URI = os.environ['SPOTIPY_REDIRECT_URI']
SCOPE = "playlist-modify-public"

# --- AUTHENTICATION ---
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    show_dialog=True
)

token_info = None
if "token_info" not in st.session_state:
    code = sp_oauth.get_authorize_url()
    st.write("## Step 1: Login with Spotify")
    st.markdown(f"[Click here to log in with Spotify]({code})")

    redirect_response = st.text_input("Paste the full URL you were redirected to after login:")
    if redirect_response:
        parsed_code = sp_oauth.parse_response_code(redirect_response)
        token_info = sp_oauth.get_access_token(parsed_code, as_dict=True)
        st.session_state.token_info = token_info
else:
    token_info = st.session_state.token_info

# --- VALID TOKEN CHECK ---
if token_info:
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state.token_info = token_info

    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)
    st.write("# 🎶 Custom Playlist Generator")

    # --- USER INPUT ---
    genres = [
        "rock", "metal", "pop", "hip hop", "country", "jazz", "classical",
        "indie", "alternative", "electronic", "blues", "folk", "funk", "punk"
    ]

    selected_genres = st.multiselect("Select genres:", genres)
    total_tracks = st.slider("How many total tracks?", min_value=20, max_value=200, value=100, step=10)
    playlist_name = st.text_input("Playlist name:", value="My Custom Genre Mix")

    if st.button("🎧 Generate Playlist") and selected_genres:
        user_id = sp.current_user()['id']
        tracks_per_genre = total_tracks // len(selected_genres)
        final_tracks = set()

        def get_genre_tracks(genre, limit=5):
            try:
                results = sp.search(q=genre, type='playlist', limit=limit)
                if results is None or 'playlists' not in results:
                    st.warning(f"No results for genre: {genre}")
                    return []
                playlists = results['playlists'].get('items', []) or []
                if not playlists:
                    st.warning(f"No playlists found for genre: {genre}")
                tracks = set()
                for pl in playlists:
                    items = sp.playlist_items(pl['id'], limit=50).get('items', [])
                    for item in items:
                        track = item.get('track')
                        if track and track.get('id'):
                            tracks.add(track['id'])
                return list(tracks)
            except Exception as e:
                st.warning(f"Error fetching tracks for {genre}: {e}")
                return []

        for genre in selected_genres:
            genre_tracks = get_genre_tracks(genre)
            random.shuffle(genre_tracks)
            final_tracks.update(genre_tracks[:tracks_per_genre])
            time.sleep(0.2)

        final_tracks = list(final_tracks)
        random.shuffle(final_tracks)

        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        sp.playlist_replace_items(playlist_id=playlist['id'], items=final_tracks[:100])
        for i in range(100, len(final_tracks), 100):
            sp.playlist_add_items(playlist_id=playlist['id'], items=final_tracks[i:i+100])

        st.success("✅ Playlist created!")
        st.markdown(f"[Open Playlist on Spotify]({playlist['external_urls']['spotify']})")
