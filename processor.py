import os
from moviepy.editor import VideoFileClip, AudioFileClip
import io
from google.oauth2 import service_account
from google.cloud import speech
import json
from googletrans import Translator
from google.cloud import texttospeech
from pydub import AudioSegment
from pathlib import Path
from audio2speech import audio_2_text_timestamp
from tkinter.ttk import Progressbar


# Ensure FFmpeg is available
AudioSegment.ffmpeg = "ffmpeg.exe"  # Adjust path as necessary
AudioSegment.ffprobe = "ffprobe.exe"
AudioSegment.converter = "ffmpeg.exe"

client_file = "piyush-personal-audio_translator.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'piyush-personal-audio_translator.json'

creds = service_account.Credentials.from_service_account_file(client_file)
CLIENT = speech.SpeechClient(credentials=creds)
client_t2s = texttospeech.TextToSpeechClient()

cleaned_data = []
translated_data = []
lang_segment_files = []
lang_timestamps = []
global audio_lang

# Translator
translator = Translator()


# DONE
def extract_audio(video_path, audio_path):
    try:
        # Load the video file
        video = VideoFileClip(video_path)

        # Extract the audio
        audio = video.audio

        # Save the audio to a file
        audio.write_audiofile(audio_path)

        print(f"Audio extracted and saved to {audio_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def export_video(original_video_path, audio_path, output_file_path):
    # Load the original video
    video = VideoFileClip(f"{original_video_path}")

    # Load the new audio
    new_audio = AudioFileClip(f"{audio_path}")

    # Set the new audio to the video
    video_with_new_audio = video.set_audio(new_audio)

    # Write the result to a new video file  # GIVE EXTENSION
    video_with_new_audio.write_videofile(f"{output_file_path}", codec='libx264', audio_codec='aac')


# Define a function to parse the string
# DONE
def parse_string(data):
    data = data.strip().split("results {")
    parsed_data = []
    for result in data[1:]:
        result_dict = {}
        alternatives = result.split("alternatives {")[1].split("}")[0]
        transcript = alternatives.split("transcript: ")[1].split('"')[1]
        confidence = float(alternatives.split("confidence: ")[1].split("}")[0])
        result_dict["alternatives"] = [{"transcript": transcript, "confidence": confidence}]
        result_dict["result_end_time"] = {"seconds": int(result.split("seconds: ")[1].split(" ")[0]),
                                          "nanos": int(result.split("nanos: ")[1].split("}")[0])}
        result_dict["language_code"] = result.split("language_code: ")[1].split("}")[0]
        parsed_data.append(result_dict)
    return parsed_data


# DONE
def audio_2_text_transcript(audio):
    audio_file = audio
    with io.open(audio_file, 'rb') as f:
        content = f.read()
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
        sample_rate_hertz=44100,
        language_code='en-US'
    )

    response = CLIENT.recognize(config=config, audio=audio)

    response_str = f"{response}"

    # Parse the string
    data = parse_string(response_str)

    # SAVE TO .json
    with open("rawdata.json", "w") as f:
        json.dump(data, f, indent=4)


# It will clean that
def clean_data(timestamps: list):
    f = open('rawdata.json')

    data = json.load(f)
    print(len(data))
    # print(type(data))
    for i in range(len(data)):
        # print(data[i]["alternatives"][0]["transcript"])
        # print(data[i]["result_end_time"]["seconds"])
        cleaned_data.append({
            "transcript": data[i]["alternatives"][0]["transcript"],
            "start_time": timestamps[i]["start_time"],
            "end_time": timestamps[i]["end_time"],
        })
    print(cleaned_data)
    print("Data cleaned")
    with open("data.json", "w") as out:
        json.dump(cleaned_data, out)


# DONE
def translate(data: str, lang: str):
    try:
        translation = translator.translate(data, dest=lang)
    except ValueError:
        return translate(data, "en")
    return translation.text


# print(translate("Hello, How are you?", dest="hindi"))

def text_2_audio(text: str, output_file, voice: str):
    if voice == "Male (Hindi)":
        lang_code = "hi-IN"
        audio_speech = "hi-IN-Wavenet-B"
    elif voice == "Female (Hindi)":
        lang_code = "hi-IN"
        audio_speech = "hi-IN-Wavenet-A"
    elif voice == "Female (Bengali)":
        lang_code = "bn-IN"
        audio_speech = "bn-IN-Standard-C"
    elif voice == "Male (Bengali)":
        lang_code = "bn-IN"
        audio_speech = "bn-IN-Standard-D"
    elif voice == "rus":
        lang_code = "ru-RU"
        audio_speech = "ru-RU-Standard-B"
    else:
        audio_speech = "hi-IN-Wavenet-B"

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=f'{audio_speech}'
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id=['small-bluetooth-speaker-class-device'],
        speaking_rate=1,
        pitch=1
    )

    response = client_t2s.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(f"{output_file}", "wb") as out:
        out.write(response.audio_content)
        print("Audio content written successfully!")
        lang_segment_files.append(f"{output_file}")


def insert_audio(original_audio_path, new_audio, timestamp_ms, output_path):
    # try:
    origin_file = Path(original_audio_path)
    original_audio = AudioSegment.from_file(origin_file)
    inserted_audio = AudioSegment.from_file(new_audio)
    combined_audio = original_audio[:timestamp_ms] + inserted_audio + original_audio[timestamp_ms:]
    combined_audio.export(output_path, format="mp3")
    print(f"Combined audio written to file {output_path}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")


def replace_segments_with_hindi(input_file, output_file, hindi_files, segments):
    """
    Replace segments of an English audio file with segments of Hindi audio files.

    :param input_file: Path to the input English audio file.
    :param output_file: Path to save the output audio file.
    :param hindi_files: List of paths to the Hindi audio files, matching the segments to replace.
    :param segments: List of tuples containing start and end times in milliseconds for the segments to be replaced.
                     Example: [(start1, end1), (start2, end2), ...]
    """
    # Load the English audio file
    english_audio = AudioSegment.from_file(input_file)

    # Sort segments and corresponding Hindi files by start time
    segments, hindi_files = zip(*sorted(zip(segments, hindi_files), key=lambda x: x[0][0]))

    # Ensure the segments do not overlap and are within bounds
    segments = [(max(0, start), min(len(english_audio), end)) for start, end in segments]

    # Initialize an empty audio segment for the result
    output_audio = AudioSegment.empty()

    # Track the end of the last segment processed
    previous_end = 0

    # Iterate through segments and corresponding Hindi audio files
    for (start, end), hindi_file in zip(segments, hindi_files):
        # Add the part of the English audio before the current segment
        output_audio += english_audio[previous_end:start]
        # Load the corresponding Hindi audio segment
        hindi_segment = AudioSegment.from_file(hindi_file)
        # Adjust the Hindi segment to match the duration of the segment to replace
        hindi_segment = hindi_segment[:end - start]
        output_audio += hindi_segment
        # Update previous_end to the end of the current segment
        previous_end = end

    # Add the remaining part of the English audio after the last segment
    output_audio += english_audio[previous_end:]

    # Export the final audio
    output_audio.export(output_file, format="mp3")
    print("FINAL AUDIO OUT")

    for item in hindi_files:
        os.remove(item)


def job(progress: Progressbar, video_path, audio_voice: str):
    global audio_lang
    if "Hindi" in audio_voice:
        audio_lang = "hindi"
    elif "Bengali" in audio_voice:
        audio_lang = "bengali"
    elif "rus" in audio_voice:
        audio_lang = "russian"

    video_path = video_path
    audio_path = "audio.mp3"
    extract_audio(video_path, audio_path)
    progress['value'] += 20
    # AUDIO -> TEXT and CLEANING
    audio_2_text_transcript("audio.mp3")
    timestamp = audio_2_text_timestamp("audio.mp3")
    clean_data(timestamp)
    for i in range(len(cleaned_data)):
        translated_data.append({
            "transcript": translate(cleaned_data[i]["transcript"], audio_lang),
            "start_time": cleaned_data[i]["start_time"],
            "end_time": cleaned_data[i]["end_time"],
        })
        lang_timestamps.append((int(cleaned_data[i]["start_time"]) * 1000, int(cleaned_data[i]["end_time"]) * 1000))
    print(f"LANG TIMESTAMP: {lang_timestamps}")
    print(f"Lang Segment: {lang_segment_files}")
    print(translated_data)
    progress['value'] += 20
    # TEXT -> AUDIO
    for i in range(len(translated_data)):
        text_2_audio(translated_data[i]["transcript"], f"temp_out-{i}.mp3", audio_voice)
    progress['value'] += 20
    # AUDIO SEGMENTS > Final Audio with sync
    replace_segments_with_hindi("audio.mp3", "final_audio.mp3", lang_segment_files, lang_timestamps)
    progress['value'] += 20
    # Export Video
    export_video(video_path, "final_audio.mp3", "export.mp4")
    progress['value'] += 20


# if __name__ == '__main__':
#     main()
#
