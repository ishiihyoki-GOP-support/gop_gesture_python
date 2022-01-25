import cv2
import math
import time
import goplt
"""
高解像の画像から任意のオフセット(TX,TY),回転角(deg),倍率(ratio)で480x480範囲の画像を切り出しclip.jpgで保存
"""
def getjpg(ratio,deg,tx,ty):
    im=cv2.imread('4kimage.jpg')
    size=(int(480/ratio),int(480/ratio))
    w,h,_=im.shape
    center=(w/2+tx,h/2+ty)
    rot_mat = cv2.getRotationMatrix2D(center, deg, 1.0)
# -(元画像内での中心位置)+(切り抜きたいサイズの中心)
    rot_mat[0][2] += -center[0]+size[0]/2
# 同上 
    rot_mat[1][2] += -center[1]+size[1]/2
    imclip= cv2.warpAffine(im, rot_mat, size,flags=cv2.INTER_LANCZOS4)
    imresize=cv2.resize(imclip,(480,480),interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite('clip.jpg',imresize,[int(cv2.IMWRITE_JPEG_QUALITY), 60])



"""
メイン
"""
def main():
    #GOPのCDC接続が確立されるまでループ
    while True:
        try:
            gop=goplt.Goplt('/dev/ttyACM0')
            break
        except Exception:
            print("ポートオープン失敗.1秒後に再接続試行")
            time.sleep(1)

    #クリップ範囲の初期値
    a_ratio=0.5
    a_rad=0
    a_tx=0
    a_ty=0
    getjpg(a_ratio,a_rad,a_tx,a_ty)
    gop.RamUpload(0,'clip.jpg')
    tx=0
    ty=0
    angle_deg=0
    scale=100
    block=0
    try:
        gop.WriteMem('GESTUREFRAME_0.TX',tx,ty,angle_deg,scale,block,0)
        while True:
            s=gop.Enq()
            if(s!=''):
                if(s==b'TOUCH_UP'):
                    tx,ty,angle_deg,scale,block=gop.ReadMem('GESTUREFRAME_0.TX',5) 
                    old_ratio=a_ratio
                    old_rad=a_rad
                    a_ratio=a_ratio*scale/100.0
                    a_rad=(a_rad+angle_deg)%360
                    dx=math.cos(math.radians(old_rad))*tx-math.sin(math.radians(old_rad))*ty
                    dy=math.sin(math.radians(old_rad))*tx+math.cos(math.radians(old_rad))*ty

                    a_tx=a_tx-(dx/old_ratio)
                    a_ty=a_ty-(dy/old_ratio)
                    getjpg(a_ratio,a_rad,a_tx,a_ty)

                    block=8000 if block==0 else 0

                    gop.RamUpload(block,'clip.jpg')

                    gop.WriteMem('TOUCH_ANGLE',0)
                    gop.WriteMem('GESTUREFRAME_0.TX',0,0,0,100,block,0)
                    gop.WriteMem('G_0TX',a_tx,a_ty,a_rad,a_ratio*100)
    except ValueError as e:
        print(e)
               
main()
