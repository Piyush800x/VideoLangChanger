import os
from moviepy.editor import VideoFileClip
import io
from google.oauth2 import service_account
from google.cloud import speech
import json
import re
from googletrans import Translator
from google.cloud import texttospeech

client_file = "piyush-personal-audio_translator.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'piyush-personal-audio_translator.json'

creds = service_account.Credentials.from_service_account_file(client_file)
CLIENT = speech.SpeechClient(credentials=creds)
client_t2s = texttospeech.TextToSpeechClient()

cleaned_data = []

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


# Specify the paths
# video_path = 'video.mp4'
# audio_path = 'audio.mp3'
#
# extract_audio(video_path, audio_path)


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
def audio_2_text(audio):
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
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print(response)
    print("-----------------------------")
    print(response.results)

    print(response)
    print("-----------------------------")
    print(response.results)


audio_2_text("audio1.mp3")


# It will clean that
def clean_data():
    f = open('data.json')

    data = json.load(f)
    print(len(data))
    # print(type(data))
    for i in range(len(data)):
        # print(data[i]["alternatives"][0]["transcript"])
        # print(data[i]["result_end_time"]["seconds"])
        cleaned_data.append({
            "transcript": data[i]["alternatives"][0]["transcript"],
            "seconds": data[i]["result_end_time"]["seconds"],
            "nanos": data[i]["result_end_time"]["nanos"],
        })
    print("Data cleaned")


# DONE
def translate(data: str, dest: str):
    try:
        translation = translator.translate(data, dest=dest)
    except ValueError:
        return translate(data, "en")
    return translation.text


# print(translate("Hello, How are you?", dest="hindi"))

def text_2_audio(text: str, lang: str):
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name='en-US-Studio-O'
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

    with open("output_audio.mp3", "wb") as out:
        out.write(response.audio_content)
        print("Audio content written successfully!")
