from sys import setrecursionlimit
setrecursionlimit(100000)
from gevent import monkey
from gevent.pool import Pool
monkey.patch_all()
import requests, re, queue,  time
from os.path import exists
from os import makedirs, mkdir


class LoginIn():
    """登陆程序"""
    def __init__(self):
        """初始化"""
        self.res = re.compile(r'pixivAccount\.postKey":"(.+)","pixivAccount\.captchaType')
        self.session = requests.Session()
        self.headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'zh-CN,zh;q=0.9',
                'cache-control': 'max-age=0',
                'referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                }
        self.headers_1 = {
                'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                'origin': 'https://accounts.pixiv.net',
                'referer': 'https://accounts.pixiv.net/login?lang = zh & source = pc & view_type = page & ref = wwwtop_accounts_index',
        }
        self.url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        self.urlS = 'https://accounts.pixiv.net/api/login?lang=zh'
        self.postKey = ''
        requests.packages.urllib3.disable_warnings()

    def Key(self):
        """获取postkey"""
        try:
            web_data = self.session.get(url=self.url, headers=self.headers, verify=False).content.decode('utf-8')
            keyurl = re.findall(self.res, web_data)
            self.postKey = keyurl[0]
            print('获取Key:', self.postKey)
        except requests.exceptions.ConnectionError:
            self.postKey = None
            print('链接pixiv失败，可能是网络原因')
        return self.postKey

    def login(self):
        """账户密码登陆"""
        get_user = input('请输入用户名/邮箱：')
        get_password = input('请输入密码：')
        # 组合登陆信息
        self.data = {
                'pixiv_id': get_user,
                'password': get_password,
                'post_key': self.postKey,
                'captcha:': '',
                'g_recaptcha_response': '',
                'source': 'pc',
                'return_to': 'www.pixiv.net',
                'ref': 'wwwtop_accounts_index',
            }

        self.content = self.session.post(self.urlS, headers=self.headers, data=self.data)
        self.cookies = self.session.cookies.get_dict()
        return self.cookies
    '''
    def cookieslogin(self):
        """cookies登陆"""
        cookiesd = {}
        cookie = input('请输入cookies：')
        cookiesd['cookies'] = cookie
        self.cookies = cookiesd
    '''
    def getname(self):
        """获取昵称 验证登陆"""
        res = re.compile(r'<a class="user-name js-click-trackable-later"href="/member\.php\?id=[0-9]+"data\-click\-category="mypage\-profile\-column\-simple"data\-click\-action="click\-profile"data\-click\-label="">(.+)</a></div></li><li>')
        urlr = 'https://www.pixiv.net/'
        self.user_name = self.session.get(urlr, headers=self.headers_1, cookies=self.cookies, verify=False)
        self.search_name = re.search(res, self.user_name.text)
        if self.search_name != None:
            nametext = re.findall(res, self.user_name.text)
            self.name = nametext[0]
            print('您好！', self.name)
        else:
            print('登陆失败请重试!', end='\n\n')
            self.Key()
            self.login()
            self.getname()


class ImageDownload():
    """寻找并下载图片"""

    def __init__(self):
        """初始化"""
        self.picturnum = 0
        self.pid_list = []
        self.picturedown = []
        # 储存下载地址的列表
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        }
        self.que = queue.Queue()
        # 设置正则匹配模式
        self.res_1 = re.compile(r'ugoira')
        self.res_2 = re.compile(r'"original":"(.+)"},"tags"')
        self.res_3 = re.compile(r'data-src="(.+?)_master1200\.jpg" data-index="[0-9]">')
        self.res_4 = re.compile(r'png')
        # 设置线程数
        while True:
            self.thrnum = input('请输入线程数(建议1-10)直接回车默认5线程：')
            if self.thrnum == '':
                self.thrnum = 5
                break
            else:
                try:
                    self.thrnum = int(self.thrnum)
                    break
                except ValueError:
                    print('请输入数字！')
        print('线程数', self.thrnum)
        self.num = self.thrnum

    def getPid(self, cookie):
        """抓取图片pid"""
        # 储存pid的列表
        res = re.compile(r'data-click-label="([0-9]+)"data-type')
        # 用于抓取图片id的正则
        while True:
            self.uid = input('请输入UID：')
            try:
                int(self.uid)
                break
            except ValueError:
                print('UID是纯数字,请重试')
                # 目录下新建文件夹
        folder = exists(r'./' + self.uid)
        if not folder:
            makedirs(r'./' + self.uid)
            print('已创建文件夹', self.uid)
        else:
            print('已存在文件夹', self.uid)
        i = 1
        while True:
            url = 'https://www.pixiv.net/member_illust.php?id=' + self.uid + '&type=all&p=' + str(i)
            # 组合url
            web_data = requests.session().get(url=url, headers=self.headers, cookies=cookie, verify=False)
            pid = re.findall(res, web_data.text)
            # 抓取数据

            if pid != []:
                # 如果这一页有图片，则将pid储存入列表并翻页，如果无图片则结束循环
                print('.'.join(pid))
                self.pid_list += pid
                i += 1
            else:
                break
            print('得到PID', len(self.pid_list), '个')
        print('正在写入队列...')
        for i in self.pid_list:
            self.que.put(i)
        print('写入完成，总队列数', self.que.qsize())

    def download(self, cookie):
        """下载图片"""
        if self.que.empty() == False:
            img = self.que.get()
            try:
                # 根据pid抓取图片页面
                moreP_url = 'https://www.pixiv.net/member_illust.php?mode=manga&illust_id=' + img
                img_data = requests.session().get(url=moreP_url, headers=self.headers, cookies=cookie, verify=False)
                downurl = re.findall(self.res_3, img_data.text)

                if downurl == []:
                    # 判断是否是单张图片或者动图
                    i = 0
                    oneP_url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + img
                    img_data = requests.session().get(url=oneP_url, headers=self.headers, cookies=cookie, verify=False)
                    downurl = re.findall(self.res_2, img_data.text)
                    du = downurl[0].replace('\\', '')
                    postfix = re.search(self.res_4, du)
                    postfix_gif = re.search(self.res_1, du)
                    if postfix and postfix_gif == None:
                        # 判断是否为png格式
                        filename = './' + self.uid + '/' + img + '_p' + str(i) + '.png'
                        header = {
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                            'X-DevTools-Emulate-Network-Conditions-Client-Id': 'A3BD4CDC56B8B0E33DF51F378B366089',
                            'Referer': du}
                        imgfile = requests.session().get(url=du, headers=header, verify=False)
                        imgfilecontent = imgfile.content
                        self.picturedown.append(du)
                        with open(filename, 'wb') as f:
                            f.write(imgfilecontent)
                        print('完成', filename)
                        self.picturnum += 1

                    elif postfix == None and postfix_gif == None:
                        # 判断是否是jpg
                        filename = './' + self.uid + '/' + img + '_p' + str(i) + '.jpg'
                        header = {
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                            'X-DevTools-Emulate-Network-Conditions-Client-Id': 'A3BD4CDC56B8B0E33DF51F378B366089',
                            'Referer': du}
                        imgfile = requests.session().get(url=du, headers=header, verify=False)
                        imgfilecontent = imgfile.content
                        self.picturedown.append(du)
                        with open(filename, 'wb') as f:
                            f.write(imgfilecontent)
                        print('完成', filename)
                        self.picturnum += 1

                    elif postfix_gif:
                        # 判断是否是动图
                        mkdir('./'+self.uid+'/'+img+'_动图')
                        # 给动图新建文件夹
                        gif_old = 'ugoira0'
                        while True:
                            gif = 'ugoira' + str(i)
                            du = du.replace(gif_old, gif)
                            filename = './' + self.uid + '/' + img +'_动图'+'/' + img + '_ugoira' + str(i) + '.jpg'
                            header = {
                                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                                'X-DevTools-Emulate-Network-Conditions-Client-Id': 'A3BD4CDC56B8B0E33DF51F378B366089',
                                'Referer': du}
                            imgfile = requests.session().get(url=du, headers=header, verify=False)
                            if imgfile.text == '<!DOCTYPE html>\n<html>\n    <h1>404 Not Found</h1>\n</html>\n':
                                break
                            imgfilecontent = imgfile.content
                            self.picturedown.append(du)
                            with open(filename, 'wb') as f:
                                f.write(imgfilecontent)
                            print('完成', filename)
                            self.picturnum += 1
                            i += 1
                            gif_old = 'ugoira' + str(i-1)

                elif downurl != []:
                    # 判断是否是多图
                    mkdir('./' + self.uid + '/' + img + '_多图')
                    i = 0
                    for img_org in downurl:
                        du = img_org.replace('master', 'original')
                        du += '.jpg'
                        self.picturedown.append(du)
                        header = {
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
                            'X-DevTools-Emulate-Network-Conditions-Client-Id': 'A3BD4CDC56B8B0E33DF51F378B366089',
                            'Referer': du}
                        # 模拟浏览器组合头文件，这里的referer和user-agent是必须的，否则引发403
                        imgfile = requests.session().get(url=du, headers=header, verify=False)
                        if imgfile.text == '<!DOCTYPE html>\n<html>\n    <h1>404 Not Found</h1>\n</html>\n':
                            # 判断是否不是jpg格式图片(这里写的不是很好，主观认为不是jpg就是png，如果以后有其他格式的图片将有错误)
                            du = du.replace('jpg', 'png')
                            imgfile = requests.session().get(url=du, headers=header, verify=False)
                            filename = './' + self.uid + '/' + img + '_多图' + '/' + img + '_p' + str(i) + '.png'
                        else:
                            filename = './' + self.uid + '/' + img + '_多图' + '/' + img + '_p' + str(i) + '.jpg'
                        i += 1
                        with open(filename, 'wb') as f:
                            # 将获取的数据以二进制存入
                            f.write(imgfile.content)
                        self.picturnum += 1
                        print('完成:', filename)
                print('队列剩余', self.que.qsize())
            except FileExistsError:
                print('图片已存在')
            except requests.exceptions.SSLError:
                print('网络错误,当前图片下载失败,重新写入队列')
                self.que.put(img)
            except requests.exceptions.ProxyError:
                print('网络错误,当前图片下载失败,重新写入队列')
                self.que.put(img)
            except requests.exceptions.ChunkedEncodingError:
                print('网络错误,当前图片下载失败,重新写入队列')
                self.que.put(img)

        else:
            pass

    def thr(self, cookie):
        """协程"""
        startime = float('{:.2f}'.format(time.time()))
        pool = Pool(self.thrnum)
        while not self.que.empty():
            pool.spawn(self.download, cookie)

        endtime = float('{:.2f}'.format(time.time()))
        usetime = endtime - startime
        print('————完成', self.uid, '共用时', usetime, '秒——————')


def main():
    """主程序"""
    print("{0:*^50}".format('说明'))
    print('1.本程序不提供翻墙\n2.ssTap或者ss、ssr需要开启全局代理\n3.修改Hosts文件是可以的，但是请注意：\n'
          ' -需要accounts.pixiv.net，否则无法登陆\n -需要www.pixiv.net，否则无法获取列表\n -请确保hosts可用\n4.线程数在5-10线程较好')
    print("{0:*^50}".format('登陆'))
    try:
        a = LoginIn()
        a.Key()
        a.login()
        a.getname()
        print("{0:*^50}".format('下载设置'))
        b = ImageDownload()
        print("{0:*^50}".format('下载主循环'))
        while True:
            # 程序主循环
            b.getPid(a.cookies)
            b.thr(a.cookies)
    except requests.ConnectionError:
        print('登陆失败，请关闭重试')


if __name__ == '__main__':
    main()