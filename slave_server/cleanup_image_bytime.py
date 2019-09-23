#! *_* encoding: utf-8

import os
import time
from enum import Enum

image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner", "flash", "image")
ImageType = Enum("Weekly", "Daily", "Eng")
image_info = {
    ImageType.Weekly: {"name": ImageType.Weekly, "prefix": "gordon_peak-flashfiles-O10"},
    ImageType.Daily: {"name": ImageType.Daily, "prefix": "gordon_peak-flashfiles-O1l"},
    ImageType.Eng: {"name": ImageType.Eng, "prefix": "gordon_peak-flashfiles-O1e"}
}
eng_keep_days = 30
sudo_pwd = "123456"


def GetFreeSpace():
    res = os.popen("df -h / | tail -n 1")
    result = res.read().split()[-2][0:-1]
    result = int(result) if result.isdigit() else -1
    return result


def IsDelete():
    is_delete = False
    free = GetFreeSpace()
    if free < 0:
        print "can't get the free space."
    elif free < 30:
        print "don't need delete some image."
    else:
        print "need delete some image."
        is_delete = True
    return is_delete


def DeleteImage(image_type):
    image_list = os.listdir(image_path)
    for image in image_list:
        image_file = os.path.join(image_path, image)
        if image.startswith(image_type["prefix"]):
            if image_type["name"] == ImageType.Eng:
                timespan = (time.time() - os.path.getctime(image_file)) / 60 / 60 / 24
                if timespan > eng_keep_days:
                    print "echo {0}|sudo -S rm -rf {0}".format(sudo_pwd, image_file)
                    os.system("echo {0}|sudo -S rm -rf {0}".format(sudo_pwd, image_file))
            else:
                print "echo {0}|sudo -S rm -rf {1}".format(sudo_pwd, image_file)
                os.system("echo {0}|sudo -S rm -rf {1}".format(sudo_pwd, image_file))

def main():
    if IsDelete():
        DeleteImage(image_info[ImageType.Weekly])
    if IsDelete():
        DeleteImage(image_info[ImageType.Daily])
    if IsDelete():
        DeleteImage(image_info[ImageType.Eng])


if __name__ == "__main__":
    main()
