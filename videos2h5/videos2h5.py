import argparse
import h5py
import os
import decord
from io import BytesIO
import json


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


def load_video_from_index(index_path, video_name, h5_path=""):
    """Load raw video bytes using a metadata index file."""
    with open(index_path, 'r') as f:
        video_index = json.load(f)

    if video_name not in video_index:
        raise KeyError(f"Video '{video_name}' not found in index.")

    shard_path = video_index[video_name]
    with h5py.File(os.path.join(h5_path, shard_path), 'r') as f:
        byte_array = f[video_name][:]
        return byte_array.tobytes()


def load_frames_from_index(index_path, video_name, h5_path="", use_decord=True):
    video_bytes = load_video_from_index(index_path, video_name, h5_path=h5_path)

    return video_bytes_to_frames_decord(video_bytes)


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
    decord.bridge.set_bridge('native')  # Use NumPy backend
    video_stream = decord.VideoReader(BytesIO(byte_data), ctx=decord.cpu(0))
    frames = video_stream.get_batch(range(len(video_stream)))  # Efficient batch load

    return frames if as_array else [frame.asnumpy() for frame in frames]


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def save_videos_to_shards(video_paths, output_prefix, files_per_shard, index_file='videos_index.json'):
    video_index = {}

    for i, chunk in enumerate(chunk_list(video_paths, files_per_shard)):
        shard_name = f"{output_prefix}_{i:03d}.h5"
        print(f"Saving {len(chunk)} videos to shard: {shard_name}")
        save_raw_videos_to_h5(chunk, shard_name)

        # Add entries to the index
        for path in chunk:
            video_name = os.path.splitext(os.path.basename(path))[0]
            shard_local_name = os.path.basename(shard_name)
            video_index[video_name] = shard_local_name

    # Save index to JSON
    with open(index_file, 'w') as f:
        json.dump(video_index, f, indent=2)

    print(f"Metadata index saved to {index_file}")


def main():
    parser = argparse.ArgumentParser(description='Store video files as raw bytes in HDF5 shards.')
    parser.add_argument('input_dir', type=str, help='Directory containing video files.')
    parser.add_argument('output_prefix', type=str, help='Prefix for output HDF5 shard files.')
    parser.add_argument('--ext', nargs='*', default=['.mp4', '.avi', '.mov', '.mkv'],
                        help='List of video file extensions to include.')
    parser.add_argument('--files_per_shard', type=int, default=100,
                        help='Maximum number of video files per HDF5 shard (default: 100).')
    parser.add_argument('--index_file', type=str, default='videos_index.json',
                        help='Path to output JSON index file (default: videos_index.json)')

    args = parser.parse_args()
    video_files = find_video_files(args.input_dir, args.ext)

    if not video_files:
        print("No video files found in the specified directory with the given extensions.")
        return

    print(f"Found {len(video_files)} video files.")
    save_videos_to_shards(video_files, args.output_prefix, args.files_per_shard, args.index_file)
    print("All shards saved.")


if __name__ == "__main__":
    main()
