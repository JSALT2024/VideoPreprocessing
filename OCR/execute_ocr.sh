#!/bin/bash
#PBS -l select=1:ncpus=4:ngpus=1:mem=50gb:plzen=True
#PBS -l walltime=23:00:00
#PBS -N ocr1

NAMES_DIR="/storage/plzen1/home/valacho/SignLLM/ocr/log_files/ocr_log1.txt"
LOG_DIR="/storage/plzen1/home/valacho/SignLLM/ocr/filenames/files_timestamps1.csv"
IN_DIR="/storage/plzen1/home/mhruz/JSALT2024/YouTubeASL/clips_cropped/"
OUT_DIR="/storage/plzen1/home/mhruz/JSALT2024/YouTubeASL/clips_cropped_ocr/"

module load mambaforge
conda activate Trim
cd /storage/plzen1/home/valacho/SignLLM/ocr
python script_ocr.py \
	--filenames ${NAMES_DIR} \
	--logfile ${LOG_DIR} \
	--input ${IN_DIR} \
	--output ${OUT_DIR}