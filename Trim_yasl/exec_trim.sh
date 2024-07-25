#!/bin/bash
#PBS -l select=1:ncpus=2:mem=16gb
#PBS -l walltime=10:00:00
#PBS -N trim2

LOG_DIR="/auto/plzen1/home/valacho/SignLLM/trim/files_timestamps/files_timestamps1.csv"
IN_DIR="/auto/plzen1/home/mhruz/JSALT2024/YouTubeASL/videos/videos/"
OUT_DIR="auto/plzen1/home/mhruz/JSALT2024/YouTubeASL/clips/"


module load mambaforge
conda activate Trim
cd /storage/plzen1/home/valacho/SignLLM/trim/scripts_trim
python trim2.py \
	--inputdir ${IN_DIR} \
	--csv_dir ${LOG_DIR} \
	--output ${OUT_DIR} \