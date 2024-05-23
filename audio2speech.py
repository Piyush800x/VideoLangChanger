import json
import os
from google.cloud import speech, storage
from pydub import AudioSegment
import re

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "piyush-personal-audio_translator.json"
BUCKET_NAME = "video-lang-changer"


def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    return gcs_uri


def long_running_transcribe_audio(uri):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=600)  # Adjust timeout as necessary

    return response


def extract_timestamps(response):
    timestamps = []
    for result in response.results:
        for alternative in result.alternatives:
            for word in alternative.words:
                if len(timestamps) == 0 or timestamps[-1]['end_time'] < word.start_time.total_seconds():
                    timestamps.append({
                        'start_time': word.start_time.total_seconds(),
                        'end_time': word.end_time.total_seconds(),
                    })
                else:
                    timestamps[-1]['end_time'] = word.end_time.total_seconds()
    return timestamps


def parse_string(data):
    # Remove any new lines and unnecessary whitespace
    string_data = re.sub(r"\s+", " ", data)

    # Use regex to parse the string into a JSON structure
    pattern = re.compile(r'({.*})')
    match = pattern.search(string_data)

    if match:
        json_string = match.group(1)
        json_data = json.loads(json_string)
        return json_data
    else:
        print("No valid JSON structure found in the string.")


def audio_2_text_timestamp(original_audio_path):
    audio_path = original_audio_path
    destination_blob_name = "uploaded_audio.wav"

    # Convert audio to the correct format if necessary
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    converted_audio_path = "converted_audio.wav"
    audio.export(converted_audio_path, format="wav")

    # Upload the audio file to GCS
    gcs_uri = upload_to_gcs(BUCKET_NAME, converted_audio_path, destination_blob_name)

    # Transcribe the audio file
    response = long_running_transcribe_audio(gcs_uri)
    timestamps = extract_timestamps(response)

    return timestamps


# def main():
#     audio_path = "audio.mp3"
#     destination_blob_name = "uploaded_audio.wav"
#
#     # Convert audio to the correct format if necessary
#     audio = AudioSegment.from_file(audio_path)
#     audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
#     converted_audio_path = "converted_audio.wav"
#     audio.export(converted_audio_path, format="wav")
#
#     # Upload the audio file to GCS
#     gcs_uri = upload_to_gcs(BUCKET_NAME, converted_audio_path, destination_blob_name)
#
#     # Transcribe the audio file
#     response = long_running_transcribe_audio(gcs_uri)
#     timestamps = extract_timestamps(response)
#
#     for segment in timestamps:
#         print(f"Speech segment: Start time: {segment['start_time']}s, End time: {segment['end_time']}s")
