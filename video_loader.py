# -*- coding: utf-8 -*- 

#TODO: 
# 1. get Audio from Videos - done
# 2. cut Audio (interval : 1m) -done
# 3. make script - done
# 4. merge script (10m)

from google.cloud import storage
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from topic_maker import make_topic
import io
import wave
import contextlib
from pydub import AudioSegment
import glob
import os

def download_audio(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    
    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )

def getStorageUri(bucket_name, file_name):
    return "gs://" + bucket_name + "/" + file_name


def sample_recognize_short(destination_file_name):
    """
    Transcribe a short audio file using synchronous speech recognition
    Args:
        local_file_path Path to local audio file, e.g. /path/audio.wav
    """    
    client = speech_v1.SpeechClient()

    # The language of the supplied audio
    language_code = "ko-KR"

    # Sample rate in Hertz of the audio data sent
    sample_rate_hertz = 16000

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    config = {
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
    }

    local_files = sorted(glob.glob("./sliced*"), key=os.path.getctime)
    script_index = 0
    merged_script = ""
    total_script = ""
    for local_file_path in local_files :
        if (is_start(local_file_path)) :
            print("Start Time")
            write_merged_script(merged_script, script_index)
            merged_script = ""
            script_index += 1

        with io.open(local_file_path, "rb") as f:
            content = f.read()
        audio = {"content": content}
        response = client.recognize(config, audio)
        print(u"Current File : " + local_file_path)
        for result in response.results:
            # First alternative is the most probable result
            alternative = result.alternatives[0]
            merged_script += (alternative.transcript + "\n")
            total_script += (alternative.transcript + "\n")
        os.remove(local_file_path)

    if (merged_script != "") :
        print("remained")
        write_merged_script(merged_script, script_index)
    
    write_total_script(total_script)
    return script_index + 1

def is_start(file_path) :
    start_time = int(file_path.split("_")[1].split(".")[0].split("-")[0])
    if (start_time != 0 and start_time % (590) == 0) :
        return True
    return False

def write_total_script(total_script):
    line_breaker = 10
    idx = 1
    all_words = total_script.split(' ')
    script_name = "total_script.txt"
    fd = open(script_name,'w')
    for word in all_words :
        if(idx == line_breaker):
            fd.write(word.strip('\n')+"\n")
            idx = 0
        else :
            fd.write(word.strip('\n')+" ")
        idx += 1
    fd.close()

def write_merged_script(merged_script, script_index) :
    line_breaker = 10
    idx = 1
    all_words = merged_script.split(' ')
    script_name = "script_" + str(script_index) + ".txt"
    fd = open(script_name,'w')
    for word in all_words :
        if(idx == line_breaker):
            fd.write(word.strip('\n')+"\n")
            idx = 0
        else :
            fd.write(word.strip('\n')+" ")
        idx += 1
    fd.close()

def divide_audio(destination_file_name):
    duration = get_audio_duration(destination_file_name)
    for start in range(0,duration, 59) :
        if (duration - start < 59) :
            end = duration
        else :
            end = start + 59
        save_sliced_audio(start, end, destination_file_name)

def save_sliced_audio(start,end, destination_file_name) :
    audio = AudioSegment.from_wav(destination_file_name)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    file_name = "sliced_" + str(start) + "-" + str(end) + ".wav"
    start_time = start * 1000
    end_time = end * 1000
    audio[start_time:end_time].export(file_name ,format = "wav")
    
def get_audio_duration(destination_file_name):
    with contextlib.closing(wave.open(destination_file_name, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames/float(rate)
        return int(duration)

def get_frame_rate(destination_file_name) :
    with contextlib.closing(wave.open(destination_file_name, 'r')) as f:
        return f.getframerate()