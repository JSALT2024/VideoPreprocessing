import os
import time
import re
import shutil
import warnings
import argparse
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import numpy as np
import easyocr
import logging
import matplotlib.pyplot as plt
from multiprocessing import current_process
from threading import Thread
from queue import Queue
from moviepy.editor import VideoFileClip
import cv2
import ffmpeg

warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

reader = None

def initialize_reader():
    global reader
    if reader is None:
        reader = easyocr.Reader(['en'], gpu=True)
        logging.info(f"Initialized EasyOCR Reader on process {current_process().name}")

def shrink_bbox(xy, shrink_factor=1):
    xy1, xy2, xy3, xy4 = xy[0], xy[1], xy[2], xy[3]
    center_x = (xy1[0] + xy3[0]) / 2
    center_y = (xy1[1] + xy3[1]) / 2

    new_xy = []
    for point in [xy1, xy2, xy3, xy4]:
        new_x = center_x + shrink_factor * (point[0] - center_x)
        new_y = center_y + shrink_factor * (point[1] - center_y)
        new_xy.append([int(new_x), int(new_y)])
    
    return new_xy

def plot_img(img, results, boxes=True):
    plt.figure()
    plt.imshow(img)
    if boxes:
        for res in results:
            xy = res[0]
            det, conf = res[1], res[2]
            
            xy1, xy2, xy3, xy4s = xy
            
            plt.plot([xy1[0], xy2[0], xy3[0], xy4s[0], xy1[0]], [xy1[1], xy2[1], xy3[1], xy4s[1], xy1[1]], 'r-')
            plt.text(xy1[0], xy1[1], f'{det} [{round(conf, 2)}]')

    plt.show()

def inpaint_image_bboxes(image, quadrilaterals):
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    
    for bbox in quadrilaterals:
        points = np.array(bbox[0], dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)

    inpainted_image_ns = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
    return inpainted_image_ns

def inpaint_image_mask(image, mask):
    inpainted_image_ns = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
    return inpainted_image_ns

def resize_frame(frame, target_size=1024):
    height, width = frame.shape[:2]
    if height > width:
        new_height = target_size
        new_width = int(width * (target_size / height))
    else:
        new_width = target_size
        new_height = int(height * (target_size / width))
    resized_frame = cv2.resize(frame, (new_width, new_height))
    return resized_frame, (width / new_width, height / new_height)

def process_frame(frame, original_size):
    initialize_reader()
    
    resized_frame, scale_factors = resize_frame(frame)
    img_copy = frame.copy()
    height, width, _ = resized_frame.shape

    frame_gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    
    results_upper = reader.readtext(frame_gray[:int(0.2 * height), :])
    results_lower = reader.readtext(frame_gray[int(0.7 * height):, :])
    
    for result in results_lower:
        for point in result[0]:
            point[1] += int(0.7 * height)
    
    results = results_upper + results_lower
    
    for i, res in enumerate(results):
        xy = res[0]
        for point in xy:
            point[0] = int(point[0] * scale_factors[0])
            point[1] = int(point[1] * scale_factors[1])
        xys = shrink_bbox(xy, shrink_factor=0.95)
        results[i][0][:] = xys
        
    img_inpainted = inpaint_image_bboxes(img_copy, results)
    
    return img_inpainted

def sample_frames_for_ocr_check(input_video_path, sample_count=5):
    try:
        clip = VideoFileClip(input_video_path)
    except OSError as e:
        logging.error(f"Error loading video file {input_video_path}: {e}")
        return []
    
    frame_count = int(clip.fps * clip.duration)
    frame_indices = np.linspace(0, frame_count - 1, sample_count, dtype=int)

    frames = []
    for idx in frame_indices:
        try:
            frame = clip.get_frame(idx / clip.fps)
            frames.append(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        except Exception as e:
            logging.warning(f"Warning: Unable to get frame at index {idx} from {input_video_path}: {e}")
            continue

    return frames

def contains_text(frames):
    initialize_reader()
    for frame in frames:
        resized_frame, _ = resize_frame(frame)
        height, width, _ = resized_frame.shape
        upper_region = resized_frame[:int(0.2 * height), :]
        lower_region = resized_frame[int(0.7 * height):, :]
        
        results_upper = reader.readtext(upper_region)
        results_lower = reader.readtext(lower_region)
        
        if results_upper or results_lower:
            return True
    return False

def load_video(input_video_path, queue):
    clip = VideoFileClip(input_video_path)
    frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in clip.iter_frames()]
    queue.put(frames)

def get_video_bitrate(input_video_path):
    probe = ffmpeg.probe(input_video_path)
    bitrate = next((stream['bit_rate'] for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return int(bitrate) if bitrate else None

def update_line(file_path, filename, new_number):
    try:
        # Read the CSV file
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        # Regular expression to match a comma followed by any number
        pattern = re.compile(r',\d+')
        
        # Find and update the specific line
        for i, line in enumerate(lines):
            if filename in line:
                lines[i] = pattern.sub(f',{new_number}', line)
                break
        else:
            print(f"Error: The filename '{filename}' was not found in the CSV file.")
            return
        
        # Write the updated lines back to the CSV file
        with open(file_path, 'w') as file:
            file.writelines(lines)
        
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def process_video(input_video_path, output_video_path, log_file_path, file_ocred_log):
    sample_frames = sample_frames_for_ocr_check(input_video_path)
    text_detected = contains_text(sample_frames)
    update_line(log_file_path, input_video_path[-29:], 1)
    
    if not text_detected:
        with open(file_ocred_log, 'a') as file:
            file.write(str(input_video_path[-29:])+(', ')+str(False)+"\n")
        shutil.copy(input_video_path, output_video_path)
        logging.info(f"No text detected in video: {input_video_path}. Skipping processing.")
        return
    else:
        with open(file_ocred_log, 'a') as file:
            file.write(str(input_video_path[-29:])+(', ')+str(True)+"\n")

    queue = Queue()
    load_thread = Thread(target=load_video, args=(input_video_path, queue))
    load_thread.start()
    load_thread.join()
    frames = queue.get()

    clip = VideoFileClip(input_video_path)
    fps = clip.fps
    frame_height, frame_width = frames[0].shape[:2]
    bitrate = get_video_bitrate(input_video_path)

    # Write frames to pipe using ffmpeg
    process = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(frame_width, frame_height), framerate=fps)
        .output(output_video_path, pix_fmt='yuv420p', video_bitrate=bitrate, an=None)  # an=None removes the audio
        .overwrite_output()
        .global_args('-loglevel', 'quiet')  # Suppress ffmpeg console output
        .run_async(pipe_stdin=True)
    )
    
    for frame in frames:
        processed_frame = process_frame(frame, (frame_width, frame_height))
        process.stdin.write(processed_frame.tobytes())
    
    process.stdin.close()
    process.wait()

def main():
    file_ocred_log = "files_ocr_log.csv"
    PATH_input = "data/video"
    PATH_output = 'clips_ocr/'
    log_file_path = "files_subchunks.csv"
    
    if not os.path.exists(PATH_output):
        os.makedirs(PATH_output, exist_ok=True)
        
    with open(log_file_path, mode='r', encoding='utf-8') as infile:
        for filename in infile:
            filename = filename.strip()
            filename = filename[:-2]
            filename = "2.mp4"
            input_video_path = os.path.join(PATH_input, filename)
            output_video_path = os.path.join(PATH_output, '{}'.format(filename))
            if os.path.exists(output_video_path):
                update_line(log_file_path, input_video_path[-29:], 1)
                continue
            if not os.path.exists(input_video_path):
                update_line(log_file_path, input_video_path[-29:], 2)
                logging.error(f"Error loading video file {input_video_path}")
                continue
            else:
                process_video(input_video_path, output_video_path, log_file_path, file_ocred_log)
                print(f'Finished processing segment: {output_video_path}')

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(end-start)
