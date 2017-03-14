#encoding=utf-8
"""每层帖子信息的实体类
"""

import os

class Information(object):
    """每层帖子信息的实体类
    """
    #userInformation = ""
    #commentContent = ""
    #img_urls = []
    #likedNum = 0
    #currentPostion = 0

    def __init__(self, userInformation, img_urls, likedNum, floorNum):
        self.userInformation = userInformation
        #self.commentContent = commentContent
        self.img_urls = img_urls
        self.likedNum = likedNum
        self.floorNum = floorNum

    def getLikedNum(self):
        return self.likedNum