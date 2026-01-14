# coding=utf-8
import codecs
import json
import os
import re
import shutil
import sys

import requests

base_dir = 'images'
cc_date_key = {
    'us': 'startdate', 'uk': 'startdate', 'ca': 'startdate',
    'au': 'enddate', 'jp': 'enddate', 'cn': 'enddate', 'de': 'enddate', 'fr': 'enddate'
}


def download_from_bing(images_map, _cc):
    bing_url = 'https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=7&cc=' + _cc
    image_data = json.loads(requests.get(bing_url).text)
    change_dir_map = {}
    for image_item in image_data['images']:
        image_url = 'https://www.bing.com' + image_item['url']
        date_key = 'startdate'
        if _cc in cc_date_key:
            date_key = cc_date_key[_cc]
        image_date = image_item[date_key]

        image_name = re.findall(r'OHR\.([a-zA-Z]+)', image_url)[0] + '_' + re.findall(r'(\d+x\d+)\.jpg', image_url)[0]
        if image_name in images_map:
            image_date = images_map.get(image_name)
        else:
            images_map[image_name] = image_date
        image_name = image_date + "_" + image_name
        save_image_name = image_name + '.jpg'
        copyright_name = image_name + '.copyright.txt'
        image_date_dir = image_date[0:4] + '-' + image_date[4:6]
        download_dir = os.path.join(base_dir, image_date_dir)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        file_path = os.path.join(download_dir, save_image_name)

        if not os.path.exists(file_path):
            print('download ' + image_name)
            change_dir_map[download_dir] = 1
            response = requests.get(image_url, stream=True)
            with open(file_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

        copyright_file_path = os.path.join(download_dir, copyright_name)
        if not os.path.exists(copyright_file_path):
            change_dir_map[download_dir] = 1
            with codecs.open(copyright_file_path, "w", "UTF-8") as out_file:
                out_file.write(image_item['copyright'])
        elif _cc == 'uk':
            with codecs.open(copyright_file_path, "r", "UTF-8") as in_file:
                old_copyright = in_file.readline()
            if old_copyright != image_item['copyright']:
                change_dir_map[download_dir] = 1
                with codecs.open(copyright_file_path, "w", "UTF-8") as out_file:
                    out_file.write(image_item['copyright'])

    if len(change_dir_map) > 0:
        change_dir_list = sorted(change_dir_map.keys(), reverse=True)
        for change_dir in change_dir_list:
            md_content = ''
            for image_file in sorted(os.listdir(change_dir), reverse=True):
                if not image_file.endswith('.jpg'):
                    continue
                with codecs.open(os.path.join(change_dir, image_file.replace('.jpg', '.copyright.txt')), "r",
                                 "UTF-8") as in_file:
                    md_content += '#### ' + image_file.split('_', 1)[0] + ' ' + in_file.readline()
                md_content += '\n\n'
                md_content += '![](' + image_file + ')'
                md_content += '\n\n'
            with codecs.open(os.path.join(change_dir, 'README.md'), "w", "UTF-8") as out_file:
                out_file.write(md_content)
        return True
    return False


def find_newest_images(count=20):
    month_list = sorted(os.listdir(base_dir), reverse=True)
    images_map = {}
    for month_dir in month_list:
        last_change_dir = os.path.join(base_dir, month_dir)
        for image_file in sorted(os.listdir(last_change_dir), reverse=True):
            if not image_file.endswith('.jpg'):
                continue
            images_map[image_file.split('_', 1)[1][:-4]] = image_file.split('_', 1)[0]
            if len(images_map) >= count:
                break
        if len(images_map) >= count:
            break
    return images_map


def update_main_readme(is_archive=False):
    month_list = sorted(os.listdir(base_dir), reverse=True)
    found_change_path = []
    show_count = 15
    for month_dir in month_list:
        last_change_dir = os.path.join(base_dir, month_dir)
        for image_file in sorted(os.listdir(last_change_dir), reverse=True):
            if not image_file.endswith('.jpg'):
                continue
            found_change_path.append([last_change_dir, image_file])
            if len(found_change_path) >= show_count:
                break
        if len(found_change_path) >= show_count:
            break

    md_content = ''
    for last_change_dir, image_file in found_change_path:
        with codecs.open(os.path.join(last_change_dir, image_file.replace('.jpg', '.copyright.txt')), "r",
                         "UTF-8") as in_file:
            md_content += '#### ' + image_file.split('_', 1)[0] + ' ' + in_file.readline()
        md_content += '\n\n'
        md_content += ('![](' + last_change_dir + '/' + image_file + ')').replace('\\', '/')
        md_content += '\n\n'
    md_content += '\n\n\n\n#### all wallpaper\n\n'
    last_year = ''
    for month in month_list:
        if last_year != month[0:4]:
            last_year = month[0:4]
            md_content += '\n\n'
            md_content += '- ' + last_year
        md_content += '&emsp;&emsp;[' + month[5:7] + '](' + base_dir + '/' + month + '/README.md) '
    md_content += '\n\n'
    if not is_archive:
        for old_year in range(int(last_year) - 1, 2009, -1):
            md_content += '- ' + str(old_year)
            for old_month in range(12, 0, -1):
                old_month_str = '{0:02d}'.format(old_month)
                old_url = 'https://github.com/janonden/bing-wallpaper/blob/{0}/images/{0}-{1}/README.md' \
                    .format(old_year, old_month_str)
                md_content += '&emsp;&emsp;[' + str(old_month_str) + '](' + old_url + ') '
            md_content += '\n\n'
    with codecs.open('README.md', "w", "UTF-8") as out_file:
        print('update README.md')
        out_file.write(md_content)


def archive_last_year(last_year):
    if len(last_year) == 0:
        return
    print('Archive ' + last_year)
    month_list = sorted(os.listdir(base_dir), reverse=True)
    for month_dir in month_list:
        if not month_dir.startswith(last_year):
            shutil.rmtree(os.path.join(base_dir, month_dir))
    if len(os.listdir(base_dir)) == 0:
        return
    update_main_readme(is_archive=True)


if __name__ == '__main__':
    if len(sys.argv) >= 3 and 'archive' == sys.argv[1]:
        archive_last_year(sys.argv[2])
    else:
        newest_images_map = find_newest_images()
        is_update = False
        for cc in ['us', 'uk', 'au', 'cn', 'jp', 'de', 'ca', 'fr']:
            is_update = download_from_bing(newest_images_map, cc) or is_update
        if is_update or not os.path.exists('README.md'):
            update_main_readme()



