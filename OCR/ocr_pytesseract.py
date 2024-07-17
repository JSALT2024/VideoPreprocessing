import os
import time
import shutil
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import numpy as np
import pytesseract
import logging
import matplotlib.pyplot as plt
from multiprocessing import current_process
from threading import Thread
from queue import Queue
from moviepy.editor import VideoFileClip
import cv2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            
            xy1, xy2, xy3, xy4 = xy
            
            plt.plot([xy1[0], xy2[0], xy3[0], xy4[0], xy1[0]], [xy1[1], xy2[1], xy3[1], xy4[1], xy1[1]], 'r-')
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

def process_frame(frame):
    img_copy = frame.copy()
    height, width, _ = frame.shape
    
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # OCR using pytesseract
    results_upper = pytesseract.image_to_data(frame_gray[:int(0.2 * height), :], output_type=pytesseract.Output.DICT ,config='--psm 6')
    results_lower = pytesseract.image_to_data(frame_gray[int(0.7 * height):, :], output_type=pytesseract.Output.DICT ,config='--psm 6')
    
    def extract_boxes(results, y_offset=0):
        n_boxes = len(results['level'])
        bboxes = []
        for i in range(n_boxes):
            if int(results['conf'][i]) > 0:  # filter out weak detections
                (x, y, w, h) = (results['left'][i], results['top'][i], results['width'][i], results['height'][i])
                bbox = [(x, y + y_offset), (x + w, y + y_offset), (x + w, y + h + y_offset), (x, y + h + y_offset)]
                bboxes.append(bbox)
        return bboxes
    
    bboxes_upper = extract_boxes(results_upper)
    bboxes_lower = extract_boxes(results_lower, y_offset=int(0.7 * height))
    results = bboxes_upper + bboxes_lower
    
    shrunk_bboxes = [shrink_bbox(bbox, shrink_factor=0.95) for bbox in results]
    img_inpainted = inpaint_image_bboxes(img_copy, [[bbox, 'text', 1] for bbox in shrunk_bboxes])
    
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
    for frame in frames:
        height, width, _ = frame.shape
        upper_region = frame[:int(0.2 * height), :]
        lower_region = frame[int(0.7 * height):, :]
        
        # OCR using pytesseract
        results_upper = pytesseract.image_to_data(upper_region, output_type=pytesseract.Output.DICT)
        results_lower = pytesseract.image_to_data(lower_region, output_type=pytesseract.Output.DICT)
        
        def has_text(results):
            return any(int(conf) > 0 for conf in results['conf'])
        
        if has_text(results_upper) or has_text(results_lower):
            return True
    return False

def load_video(input_video_path, queue):
    clip = VideoFileClip(input_video_path)
    frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in clip.iter_frames()]
    queue.put(frames)

def process_video(input_video_path, output_video_path, log_file_path, segment_text_mask=1):
    # Sample frames to check for OCR-detectable text
    sample_frames = sample_frames_for_ocr_check(input_video_path)
    text_detected = contains_text(sample_frames)
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{os.path.basename(input_video_path)}, {text_detected}\n")
    
    if not text_detected:
        shutil.copy(input_video_path, output_video_path)
        logging.info(f"No text detected in video: {input_video_path}. Skipping processing.")
        return

    # Load video frames in a separate thread
    queue = Queue()
    load_thread = Thread(target=load_video, args=(input_video_path, queue))
    load_thread.start()

    # Wait for frames to be loaded
    load_thread.join()
    frames = queue.get()

    clip = VideoFileClip(input_video_path)
    fps = clip.fps
    frame_height, frame_width = frames[0].shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    for frame in frames:
        processed_frame = process_frame(frame)
        out.write(processed_frame)
    
    out.release()

def main():
    pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
    filenames = "files_subchunks.txt"
    PATH_input = "data/video"
    PATH_output = 'clips_ocr/'
    log_file_path = 'video_processing_log.txt'
            
    if not os.path.exists(PATH_output):
        os.makedirs(PATH_output, exist_ok=True)
        
    with open(filenames, mode='r', encoding='utf-8') as infile:
        for filename in infile:
            filename = filename.strip()
            input_video_path = os.path.join(PATH_input, filename)
            output_video_path = os.path.join(PATH_output, '{}'.format(filename))
            if os.path.exists(output_video_path):
                continue
            else:
                process_video(input_video_path, output_video_path, log_file_path)

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(end-start)
