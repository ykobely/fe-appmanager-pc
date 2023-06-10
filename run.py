#coding:utf-8
import os,sys,platform,subprocess,time,json,shutil,re,stat

#判断当前系统
isWindows = 'Windows' == platform.system()

if isWindows:
    import paramiko

bakTmp = '../__dist/'

#前端项目名
project = 'appmanager-pc'

#后端分支模板所在目录
beRelease = '../yyfq-appmanager-web/yyfq-appmanager-web-webapp/src/main/webapp/WEB-INF/views'

#前端上线发布分支所在目录
feRelease = '../fe-release-group/'


#前端上线发布分支地址
feReleaseGit = 'git@gitlab.szyy.com:fe-release-group/appmanager-pc.git'
# feReleaseGit = 'git@gitlab.szyy.com:test-fe-release-group/appmanager-pc.git'


#初始化目录
def initDir():
    if not os.path.exists(feRelease):
        exeCmd('mkdir ' + feRelease)

#获取当前git分支
def getGitBranch():
    branches = subprocess.check_output(['git', 'branch']).split('\n')
    for b in branches[0:-1]:
        if b[0] == '*':
            return b.lstrip('* ')

    return None


def exeCmd(cmd):
    if (not isWindows) and ( ('jello' in cmd) or ('rm' in cmd) or ('scp' in cmd)):
        cmd = 'sudo ' + cmd

    print '------------------------------------------------------'
    print cmd
    os.system(cmd)

def releaseDev():
    print 'release to dev'
    exeCmd('jello release -wc')

def releaseQa():
    print 'release to 172.28.3.21 start...'

    #删除遗留的__dist
    if os.path.exists(bakTmp):
        shutil.rmtree(bakTmp)

    #进行打包编译
    # cmd = 'jello release -cmD -d ' + bakTmp
    cmd = 'jello release -cD -d ' + bakTmp
    exeCmd(cmd)

    #把vm文件拷贝到后端工程
    cmd = 'scp -r ' + bakTmp + 'WEB-INF/views/page' + ' ' + beRelease
    exeCmd(cmd)

    # 1qaz#EDC(测试)
    # cmd = 'rsync -azvP --delete ' + bakTmp + 'WEB-INF/views/page' + ' ' + 'root@172.28.28.34:/home/webapp/tomcat_yysta/webapps/ROOT/WEB-INF/view'
    # exeCmd(cmd)

    #拷贝静态资源到测试服务器
    # cmd = 'scp -r ' + bakTmp + project + ' user_h5@172.28.3.21:/share/yyfq/'
    # cmd = 'rsync -azvP --delete ' + bakTmp + project + ' user_h5@172.28.3.21:/share/yyfq/'
    # exeCmd(cmd)

    # 3.53
    # cmd = 'rsync -azvP -e "ssh -p 37100" --delete ' + bakTmp + project + ' root@172.28.3.53:/www/html/'
    # exeCmd(cmd)

    # cmd = 'rm -rf ' + bakTmp
    # exeCmd(cmd)

    # print 'release to 172.28.3.21 end'

    if isWindows:
        winConnect('172.28.3.21','user_h5','yyfq.com',22)
    else:
        cmd = 'rsync -azvP --delete ' + bakTmp + project + ' user_h5@172.28.3.21:/share/yyfq/'
        exeCmd(cmd)

    print 'release to 172.28.3.21 end'
    if os.path.exists(bakTmp):
        shutil.rmtree(bakTmp)

def winConnect(host,username,password,port):
    scp=paramiko.Transport((host,port))
    scp.connect(username=username,password=password)
    sftp=paramiko.SFTPClient.from_transport(scp)
    winUpload(sftp,bakTmp)
    scp.close()

def winUpload(sftp,dir):
    files=os.listdir(dir)
    for f in files:
        rmpath = os.path.join(dir,f)
        if os.path.isdir(rmpath):
            d = re.sub(r'\\','/',rmpath.replace(bakTmp,'/share/yyfq/'))
            try:
                sftp.stat(d)
            except IOError:
                sftp.mkdir(d)
            winUpload(sftp,os.path.join(dir,f))
        else:
            rmf = re.sub(r'\\','/',os.path.join(dir,f).replace(bakTmp,'/share/yyfq/'))
            print rmf
            sftp.put(os.path.join(dir,f),rmf)

#测试替换vm
def releaseQaVM():
    print 'release to 172.28.28.32 start...'

    #删除遗留的__dist
    exeCmd('rm -rf ' + bakTmp)

    #进行打包编译
    cmd = 'jello release -cmD -d ' + bakTmp
    exeCmd(cmd)

    #把vm文件拷贝到后端工程
	##172.28.28.32 root 1qaz#EDC
    cmd = 'scp -rf ' + bakTmp + 'WEB-INF/views/page' + ' ' + 'root@172.28.28.33:/home/webapp/tomcat-shop-wap/webapps/ROOT/WEB-INF/views'
    exeCmd(cmd)

    #拷贝静态资源到测试服务器
    #cmd = 'scp -rf ' + bakTmp + project + ' user_h5@172.28.28.32:/opt/soft/tengine/html/yyfqstatic/'
    cmd = 'rsync -azvP --delete ' + bakTmp + project + ' user_h5@172.28.28.32:/opt/soft/tengine/html/yyfqstatic/'
    exeCmd(cmd)

    cmd = 'rm -rf ' + bakTmp
    exeCmd(cmd)

    print 'release to 172.28.28.32 end'


def releaseOnline():
    print 'release to fe-release start...'

    #检测是否在master分支
    if getGitBranch() != 'master':
        print 'please merge to master!'
        return

    #删除遗留的__dist
    if os.path.exists(bakTmp):
        shutil.rmtree(bakTmp)

    #进行打包编译
    cmd = 'jello release -comD -d ' + bakTmp
    exeCmd(cmd)

    #删除原有release目录并且clone最新的
    currPath = os.getcwd()
    os.chdir(os.path.join(currPath, feRelease))

    if isWindows:
        #删除原有release目录
        if(os.path.exists(project)):
            setChmod(project)
            shutil.rmtree(project)
        exeCmd('git clone ' + feReleaseGit)
        for path in os.listdir(os.path.join(feRelease, project)):
            fullpath = os.path.join(feRelease, project,path)
            if os.path.isdir(fullpath):
                if path[0] != '.':
                    shutil.rmtree(fullpath)
            else:
                os.remove(fullpath)

        #将打包编译的文件拷贝到fe-release
        os.chdir(currPath)
        src = os.path.join(bakTmp, project)
        for name in os.listdir(src):
            srcname = os.path.join(src, name)
            if os.path.isdir(srcname):
                shutil.copytree(srcname,os.path.join(feRelease, project,name))
            else:
                shutil.copy2(srcname,os.path.join(feRelease, project))
    else:
        #删除原有release目录
        exeCmd('rm -rf ' + project)
        exeCmd('git clone ' + feReleaseGit)

        #将打包编译的文件拷贝到fe-release
        os.chdir(currPath)
        exeCmd('rm -rf ' + os.path.join(feRelease, project, "*"))

        cmd = 'scp -r ' + os.path.join(bakTmp, project, '*') + ' ' + os.path.join(feRelease, project)
        exeCmd(cmd)

        cmd = 'scp -r ' + os.path.join(bakTmp, 'WEB-INF/views/page') + ' ' + os.path.join(feRelease, project)
        exeCmd(cmd)

    #切到fe-release git push
    os.chdir(os.path.join(currPath, feRelease, project))
    exeCmd('git add .')
    exeCmd('git commit -m "auto commit" *')
    exeCmd('git push')

    #打tag
    exeCmd('git tag www/' + project + '/' + time.strftime('%Y%m%d.%H%M'))
    exeCmd('git push --tags')

    #切回到当前目录
    os.chdir(currPath)
    if os.path.exists(bakTmp):
        shutil.rmtree(bakTmp)

    print 'release to fe-release end'

def setChmod(dir):
    for path in os.listdir(dir):
        fullpath = os.path.join(dir, path)
        if stat.S_ISDIR(os.lstat(fullpath).st_mode):
            setChmod(fullpath)
        else:
            os.chmod(fullpath, stat.S_IRWXU|stat.S_IRGRP|stat.S_IROTH)

def main():
    initDir()

    argv = sys.argv
    if len(argv) == 1:
        exeCmd('jello server start -p 80')
        return

    cmdType = sys.argv[1]

    if cmdType == 'dev':
        releaseDev()

    elif cmdType == 'qa':
        releaseQa()

    elif cmdType == 'qavm':
        releaseQaVM()

    elif cmdType == 'www':
        releaseOnline()

    else:
        print 'please choose one : dev,qa,www'

if __name__ == "__main__":
    main()
