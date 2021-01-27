import argparse
import requests, zipfile, io
from urllib.request import urlparse, urlopen, urlretrieve
import urllib
from bs4 import BeautifulSoup
import re
import os
import patoolib
import shutil
from urllib.parse import unquote

def file_name(url):
    a = urlparse(url)
    return os.path.basename(a.path)

def create_dir_if_not_exist(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def remove_empty_dirs(path):
    """
    Remove all empty directories in 'path'
    """
    for root, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            try:
                os.rmdir((os.path.realpath(os.path.join(root, dirname))))
            except OSError:
                pass

def download_file(exceptions, outdir, anime_name, url):
    """
    Download the file pointed at 'url' in the directory 'outdir',
    unless its extension is in 'exceptions'. If this file is an archive, extract
    it and keep only the files with the the wanted extensions.
    """
    if url.endswith((".rar", ".zip", ".7z")):
        path = urlparse(url).path
        ext = os.path.splitext(path)[1]
        archive_name = unquote(os.path.splitext(path)[0]).rsplit('/', 1)[-1]
        
        create_dir_if_not_exist(outdir)
        try:
            urlretrieve(url, os.path.join(outdir,"tempo" + ext))
            file_retrieved = True
        except Exception:
            print("Something went wrong with downloading the file")
            file_retrieved = False
        
        if file_retrieved is True:
            create_dir_if_not_exist("tempo_kitsunekko")
            
            try:
                patoolib.extract_archive(os.path.join(outdir,"tempo" + ext),
                                            outdir="tempo_kitsunekko",
                                            verbosity=0
                                        )
            except Exception:
                print(f"\n----- Ignore {archive_name} because of too long file in it -----")
        
            os.remove(os.path.join(outdir,"tempo" + ext))
        
            # the archive may have subfolders
            for subdir, dirs, files in os.walk("tempo_kitsunekko"):
                for file in files:
                    if file.endswith(exceptions):
                        os.remove(os.path.join(subdir, file))
            
            remove_empty_dirs("tempo_kitsunekko")
            
            if len(os.listdir("tempo_kitsunekko")) > 0:
                create_dir_if_not_exist(os.path.join(outdir, anime_name))
                shutil.move("tempo_kitsunekko",
                            os.path.join(outdir, anime_name, archive_name))
            else:
                shutil.rmtree("tempo_kitsunekko")
    
    if not url.endswith((".rar", ".zip", ".7z")):
        create_dir_if_not_exist(os.path.join(outdir, anime_name, "various"))
        try:
            urlretrieve(url,
                        os.path.join(outdir, anime_name, "various", file_name(url)))
        except:
            print("Something went wrong with downloading the file")


def download_relevant(anime_url : str, exceptions : tuple, outdir, anime_name):
    page = requests.get(anime_url)    
    data = page.text
    soup = BeautifulSoup(data)
    
    if not anime_url.endswith("%2F"):
        print("-----", anime_url, "-----")
        download_file(exceptions, outdir, anime_name, url)
    else:
        for link in soup.find_all('a'):
            url_part = link.get('href')
            if url_part.startswith("subtitles/japanese/") and not url_part.endswith(exceptions) and not url_part.endswith(
                                ("subtitles/japanese/", "asc", "desc")):
                
                url = urllib.parse.urljoin("https://kitsunekko.net/",
                                        urllib.parse.quote(url_part))
                
                print("-----", url, "-----")
                download_file(exceptions, outdir, anime_name, url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kitsunekko parser')
    
    parser.add_argument('--outdir', type=str, help='output directory')
    
    args = parser.parse_args()

    url = "https://kitsunekko.net/dirlist.php?dir=subtitles%2Fjapanese%2F"

    page = requests.get(url)    
    data = page.text
    soup = BeautifulSoup(data)

    for link in soup.find_all('a'):
        url_part = link.get('href')
        if url_part.startswith("/dirlist.php?dir=subtitles") and not url_part.endswith(("subtitles%2Fjapanese%2F", "asc", "desc")):
            anime_url = urllib.parse.urljoin("https://kitsunekko.net/", link.get('href'))
            
            # extract the anime name from the url
            anime_name = unquote(link.get('href'))
            anime_name = os.path.basename(os.path.normpath(anime_name))

            # download relevant files
            download_relevant(anime_url,
                              exceptions=(".ssa", ".ass", ".srt",
                                          ".txt", ".lrc"),
                              outdir=args.outdir,
                              anime_name=anime_name)

"""
download_file(exceptions=(".ssa", ".ass", ".srt", ".txt", ".lrc"),
              outdir="bidon",
              anime_name="MYNAME",
              url="https://kitsunekko.net/subtitles/japanese/Dumbbell%20Nan%20Kilo%20Moteru%253F/1-12%20Dumbbell%20Nan%20Kilo%20Moteru%5BSynched%20for%20HorribleSubs%5D.rar")

print("Went through")
"""