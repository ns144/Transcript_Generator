curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip -o "ffmpeg.zip"

tar -xf "ffmpeg.zip"

move "ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" "ffmpeg.exe"
move "ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe" "ffprobe.exe"

del "ffmpeg.zip"
rmdir /s /q "ffmpeg-master-latest-win64-gpl"
