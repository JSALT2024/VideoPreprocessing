import argparse
import h5py
import os
import decord
from io import BytesIO


def save_raw_videos_to_h5(video_paths, h5_path):
    with h5py.File(h5_path, 'w') as f:
        for path in video_paths:
            video_name = os.path.splitext(os.path.basename(path))[0]
            with open(path, 'rb') as file:
                byte_data = file.read()
                byte_array = bytearray(byte_data)
                f.create_dataset(video_name, data=byte_array, dtype='uint8')


def load_raw_video_from_h5(h5_path, video_name, output_path):
    with h5py.File(h5_path, 'r') as f:
        byte_array = f[video_name][:]
        with open(output_path, 'wb') as out_file:
            out_file.write(byte_array.tobytes())


def find_video_files(directory, extensions=None):
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv']
    video_files = []
    for fname in os.listdir(directory):
        if any(fname.lower().endswith(ext) for ext in extensions):
            video_files.append(os.path.join(directory, fname))
    return video_files


def video_bytes_to_frames_decord(byte_data, as_array=True):
    """Decode video bytes into frames using decord.

    Args:
        byte_data (bytes): Raw bytes of the video file.
        as_array (bool): If True, return frames as a stacked NumPy array. Else, return list of frames.

    Returns:
        np.ndarray or list: Video frames.
    """
    decord.bridge.set_bridge('numpy')  # Use NumPy backend
    video_stream = decord.VideoReader(BytesIO(byte_data), ctx=decord.cpu(0))
    frames = video_stream.get_batch(range(len(video_stream)))  # Efficient batch load

    return frames if as_array else [frame.asnumpy() for frame in frames]


def main():
    parser = argparse.ArgumentParser(description='Store video files as raw bytes in an HDF5 file.')
    parser.add_argument('input_dir', type=str, help='Directory containing video files.')
    parser.add_argument('output_h5', type=str, help='Output HDF5 file path.')
    parser.add_argument('--ext', nargs='*', default=['.mp4', '.avi', '.mov', '.mkv'],
                        help='List of video file extensions to include (default: .mp4 .avi .mov .mkv)')
    args = parser.parse_args()

    video_files = find_video_files(args.input_dir, args.ext)
    if not video_files:
        print("No video files found in the specified directory with the given extensions.")
        return

    print(f"Found {len(video_files)} video files. Saving to {args.output_h5}")
    save_raw_videos_to_h5(video_files, args.output_h5)
    print("Done.")
