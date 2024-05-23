import os
from moviepy.editor import VideoFileClip
import io
from google.oauth2 import service_account
from google.cloud import speech
import json
import re
from googletrans import Translator
from google.cloud import texttospeech
from pydub import AudioSegment
import ffmpeg
from pathlib import Path
from gtts import gTTS
from audio2speech import audio_2_text_timestamp


# Ensure FFmpeg is available
AudioSegment.ffmpeg = "C:\\Windows\\ffmpeg\\bin\\ffmpeg.exe"  # Adjust path as necessary
AudioSegment.ffprobe = "C:\\Windows\\ffmpeg\\bin\\ffprobe.exe"
AudioSegment.converter = "C:\\Windows\\ffmpeg\\bin\\ffmpeg.exe"

client_file = "piyush-personal-audio_translator.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'piyush-personal-audio_translator.json'

creds = service_account.Credentials.from_service_account_file(client_file)
CLIENT = speech.SpeechClient(credentials=creds)
client_t2s = texttospeech.TextToSpeechClient()

cleaned_data = []
translated_data = []

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

    print(response)
    print("-----------------------------")
    print(response.results)

    print(response)
    print("-----------------------------")
    print(response.results)


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

def text_2_audio(text: str, output_file):
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="hi-IN",
        name='hi-IN-Wavenet-A'
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


def main():
    audio_2_text_transcript("audio.mp3")
    timestamp = audio_2_text_timestamp("audio.mp3")
    clean_data(timestamp)
    for i in range(len(cleaned_data)):
        translated_data.append({
            "transcript": translate(cleaned_data[i]["transcript"], "hindi"),
            "start_time": cleaned_data[i]["start_time"],
            "end_time": cleaned_data[i]["end_time"],
        })
    print(translated_data)
    # for i in range(len(translated_data)):
    #     text_2_audio(translated_data[i]["transcript"], output_file=f"output_audio-{i}.mp3")
    #     print(f"output_audio-{i}.mp3 done")


def place_audios():         # FIX IT
    # # Sample input (with hypothetical English audio file for timing)
    english_audio_file = "audio.mp3"
    transcripts = [
        {
            'transcript': 'वाह, क्या दर्शक हैं, लेकिन अगर मैं ईमानदार रहूं तो मुझे इसकी परवाह नहीं है कि आप मेरी बातचीत के बारे में क्या सोचते हैं, मुझे इसकी परवाह नहीं है कि इंटरनेट मेरी बातचीत के बारे में क्या सोचता है।',
            'seconds': 21, 'nanos': 10000000},
        {
            'transcript': 'क्योंकि वे वही हैं जो इसे देखते हैं और एक शर्ट प्राप्त करते हैं और मुझे लगता है कि यही वह जगह है जहां ज्यादातर लोग गलत समझते हैं कि आप यहां आपसे बात करने के बजाय आपसे बात कर रहे हैं, यादृच्छिक व्यक्ति फेसबुक स्क्रॉल कर रहा है',
            'seconds': 33, 'nanos': 750000000},
        {
            'transcript': '2009 में आपके द्वारा देखे गए क्लिक के लिए धन्यवाद, हम सभी के पास ये अजीब छोटी चीजें हैं जिन्हें ध्यान विस्तार कहा जाता है, मैं आखिरी बार यह सोचने की कोशिश कर रहा हूं कि मैंने 18 मिनट की बातचीत कब देखी थी, सचमुच वर्षों खर्च होते हैं, इसलिए यदि आपको एक TED दिया जाता है बात जल्दी करो, मैं अपना काम कर रहा हूं और एक मिनट से कम समय में मैं अभी 44 सेकंड पर हूं, इसका मतलब है कि आपके पास एक अंतिम मजाक के लिए समय है कि गुब्बारे इतने महंगे क्यों हैं',
            'seconds': 64, 'nanos': 570000000},
        {'transcript': 'मुद्रा स्फ़ीति', 'seconds': 66, 'nanos': 880000000}
    ]

    # Load the original English audio to get timing reference
    english_audio = AudioSegment.from_mp3(english_audio_file)

    # Create individual Hindi audio segments
    hindi_segments = []
    for i, entry in enumerate(transcripts):
        text = entry['transcript']
        start_time = entry['seconds'] * 1000 + entry['nanos'] // 1000000  # convert to milliseconds
        tts = gTTS(text, lang='hi')
        tts.save(f"hindi_segment_{i}.mp3")
        segment = AudioSegment.from_mp3(f"hindi_segment_{i}.mp3")

        # Calculate duration of the original English segment
        end_time = (transcripts[i + 1]['seconds'] * 1000 + transcripts[i + 1]['nanos'] // 1000000) if i + 1 < len(
            transcripts) else len(english_audio)
        original_segment_duration = end_time - start_time

        # Adjust the Hindi segment duration to match the original English segment duration
        if segment.duration_seconds * 1000 > original_segment_duration:
            segment = segment[:original_segment_duration]
        else:
            silence = AudioSegment.silent(duration=original_segment_duration - segment.duration_seconds * 1000)
            segment += silence

        hindi_segments.append((start_time, segment))

    # Combine all segments into the final audio
    final_audio = AudioSegment.silent(
        duration=len(english_audio))  # Create a silent audio segment with the same length as the original audio

    for start_time, segment in hindi_segments:
        final_audio = final_audio.overlay(segment, position=start_time)

    # Save the final audio
    final_audio.export("final_hindi_audio.mp3", format="mp3")

    # # Clean up individual segment files
    # for i in range(len(transcripts)):
    #     os.remove(f"hindi_segment_{i}.mp3")

    print("Final audio created successfully as 'final_hindi_audio.mp3'")


if __name__ == '__main__':
    main()
    timestamp_mss = 21 * 1000
    # insert_audio(original_audio_path="audio.mp3", new_audio="output_audio-0.mp3", timestamp_ms=timestamp_mss,
    #              output_path="final.mp3")
    # WORKING but problem
    # 21 is end timestamp, how to put starting time?


