import urllib2
import re
import ssl
import time
import redis
rds = redis.Redis(host='localhost', port=6379)
rid = rds.get('auth_yuxiang')



class Getbuild:
    def __init__(self,id):
        self.usr_pwd = rid
        self.id = str(id)
        self.link = {'bxtp_m':'https://mcg-depot.intel.com/artifactory/cactus-absp-jf/build/eng-builds/bxtp_ivi_m/PSI/weekly/',\
                     'bxtp_o':'https://mcg-depot.intel.com/artifactory/cactus-absp-jf/build/eng-builds/omr1_bxtp_ivi_maint/PSI/weekly/',\
                     'bxtp_p':'https://mcg-depot.intel.com/artifactory/cactus-absp-jf/build/eng-builds/master/PSI/weekly/',
                     'acrn_gfx':'https://buildbot.sh.intel.com/absp/builders/f_o_mr1_acrn_pnp-engineering'
                     }
        self.datas = self.get_html()

    def get_html(self):
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            build = self.link[self.id]
            request = urllib2.Request(build)
            request.add_header("Authorization","Basic %s" % self.usr_pwd)
            response = urllib2.urlopen(request)
            list_all = response.read()
            return list_all
        except Exception,e:
            print "Get %s weekly error:" % self.id,e
            return None


    def get_weekly(self):
        # list_all = []
        ldate = str(time.strftime("%Y"))
        lists = self.datas
        week_list = re.findall(r'(\d+_WW\d+_?[A-Z]?)', lists)
        week_list.reverse()
        week_slist = list(set(week_list))
        week_slist.sort(key=week_list.index)
        # data = re.findall(r'(\d+_WW\d+_?[A-Z]?)', lists)[-1]
        if week_list:
            # list_all.append(data)
            # list_all.append((self.link[self.id])+str(data)+'/')
            return week_slist
        else:
            return None

    def get_links(self):
        list_all = self.datas
        data = re.findall(r'(\d+_WW\d+_?[A-Z]?)', list_all)[-1]
        if data:
            if self.id == "bxtp_o":
                links = self.link[self.id] + "{0}/gordon_peak/userdebug/".format(str(data))
                self.link[self.id] =links
                s = self.get_html()
                if s:
                    l = re.findall(r'gordon_\w+-flashfiles-[A-Z]\d+.zip',s)
                    if l:
                        eb = l[0]
                        link_full = links+str(eb)
                        return link_full
                    else:
                        print "Get EB_O failed"
                        return None
            elif self.id == "bxtp_m":
                links = self.link[self.id] + "{0}/r0_bxtp_abl/userdebug/".format(str(data))
                self.link[self.id] = links
                s = self.get_html()
                l = re.findall(r'r0_bxtp_abl-flashfiles-bxtp_ivi_m-rc-\d+.zip',s)
                if l:
                    eb = l[0]
                    link_full = links+str(eb)
                    return link_full
                else:
                    print "Get EB_M failed"
                    return None
            else:
                print "No build_type was found"
                return None
        else:
            print "Get Latest weekly failed:",data
            return None

