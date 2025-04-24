from videos2h5 import load_frames_from_index
import cv2
import os


def show_video(frames, window_name="Video", wait=30):
    """Display video frames using OpenCV.

    Args:
        frames (list or np.ndarray): List or array of frames (H x W x 3).
        window_name (str): Name of the display window.
        wait (int): Delay between frames in milliseconds.
    """
    for frame in frames.asnumpy():
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow(window_name, rgb_frame)
        if cv2.waitKey(wait) & 0xFF == ord('q'):  # Press 'q' to quit early
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    h5_path = r"w:\korpusy_cv\JSALT\How2Sign_v2\data\val"

    frames = load_frames_from_index('videos_index.json',
                                    'fyI1Ev5m1w4_6-8-rgb_front', h5_path=h5_path)
    print(f"{len(frames)} frames loaded from video1")
    show_video(frames, wait=30)

