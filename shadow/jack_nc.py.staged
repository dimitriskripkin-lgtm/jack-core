import os, subprocess
AF="highpass=f=200,lowpass=f=3400,afftdn=nr=12:nf=-25"
def denoise(src, dst=None):
    if not src or not os.path.isfile(src):
        return src
    if dst is None:
        dst = src + ".nc.wav"
    r = subprocess.run(["ffmpeg","-y","-hide_banner","-i",src,"-af",AF,"-ar","16000","-ac","1",dst], capture_output=True, text=True, timeout=20)
    if r.returncode==0 and os.path.isfile(dst) and os.path.getsize(dst)>500:
        return dst
    return src
