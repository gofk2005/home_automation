"""
Раскладываем неупорядоченный набор файлов (например, фото) по папкам: год/месяц.
Исходный набор файлов (фото) может быть в любом виде с любой структурой каталогов.
В текущей версии скрипт разделяет файлы на:
- фото
- исходники фото (RAW) 
- видео
- неизвестные файлы (все остальное)
Разделение по типам файлов можно настроть редактированием словаря types
По умолчанию файлы не удаляются из исходной директории. Это можно настроить (читаем комментарии по тексту).
Если при копировании файла в целевой директории уже есть файл с таким именем - к имени файла добавляется текущий timestamp.
При обработке игнорируются директории, в названии которых содержится символ '@' (типа @__thumb, @eaDir и т.п.)


"""

from genericpath import isfile, isdir
import os
import datetime
import time

resultFiles = []

logFile = "/home/gofk/Документы/test_images/result.log"
photoDir = "/home/gofk/Документы/test_images" # папка куда необходимо положить исходные фото для сортировки
output_dir = "/home/gofk/Документы/result_images" # папка, где появятся отсортированные фото

# список типов (редактируем по необходимости), base folder - папка, в которую будут помещаться файлы этого типа
types = {}
types['jpg'] = {'base_folder': 'images_by_date'}
types['jpeg'] = {'base_folder': 'images_by_date'}
types['bmp'] = {'base_folder': 'images_by_date'}
types['png'] = {'base_folder': 'images_by_date'}
types['raf'] = {'base_folder': 'raw_by_date'}
types['raw'] = {'base_folder': 'raw_by_date'}
types['cr2'] = {'base_folder': 'raw_by_date'}
types['nef'] = {'base_folder': 'raw_by_date'}
types['psd'] = {'base_folder': 'raw_by_date'}
types['dng'] = {'base_folder': 'raw_by_date'}
types['mov'] = {'base_folder': 'video_by_date'}
types['mp4'] = {'base_folder': 'video_by_date'}


count = 0

def toLog(deviceName, *text):
    """ Используем вместо print, печатаем на экран и пишем в лог """
    now = datetime.datetime.now()
    record = "[" + str(now) + "] (" + str(deviceName) + ") "
    if len(text)>1:
        for t in text:
            record += str(t) + " "
    else:
        record += str(text[0])
    print(record)
    record += '\n'
    f = open(logFile, 'a+')
    f.write(record)
    f.close()


def getFiles(directory):
    global filesList
    global count

    toLog('Directory', directory)
    for root, dirs, files in os.walk(directory):

        for dir in dirs:
            if dir not in ('.', '..'):
                getFiles(dir)        

        for name in files:
            currentFile = os.path.join(root, name)
            count += 1
            if isfile(currentFile) and "@" not in root:
                info = os.stat(currentFile)
                ext = os.path.splitext(name)[-1][1:]                

                # копируем файл в папку по датам

                date = datetime.datetime.fromtimestamp(int(info.st_mtime))
                year = str(date.year)
                month = str(date.month)

                if ext.lower() in types:
                    folder = types[ext.lower()]['base_folder']
                    resultDir = os.path.join(output_dir, folder, year, month) # раскладываем в структуру "год/месяц"
                else:
                    folder = 'unknown'
                    resultDir = os.path.join(output_dir, folder, year) # неизвестные файлы раскладываем только по годам

                toLog(count, 'File', currentFile)
                toLog(count, 'Result directory', resultDir)
                if not os.path.isdir(resultDir): # целевая директория еще не создана
                    toLog(count, 'Create result directory', resultDir)
                    os.makedirs(resultDir)
                
                resultFileName = os.path.join(resultDir, name)
                toLog(count, 'Result file', resultFileName)
                if os.path.exists(resultFileName): # если файл с таким именем уже есть - добавляем к имени текущий timestamp
                    now = str(int(time.time()))
                    name = os.path.splitext(name)[0] + '_' + now + '.' + ext
                    toLog(count, 'Rename file. New filename', name)

                # Перенос файла
                # os.replace(currentFile, resultFileName)
                # toLog(count, 'File moved', resultFileName)

                # Копирование файла
                cmd = 'cp "' + currentFile + '" "' + resultFileName + '"'
                toLog(count, cmd)
                os.system(cmd)
                toLog(count, 'File copied', resultFileName)

getFiles(photoDir)
