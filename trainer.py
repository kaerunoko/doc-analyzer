# -*- coding: utf-8 -*-
from __future__ import with_statement
import os

class FileDao(object):
    """
    ローカルに保存するデータを司る
    """
    _TSV_FILE_NAME_ = 'rss_words_db.tsv'

    def __init__(self, filename = _TSV_FILE_NAME_):
        super(FileDao, self).__init__()
        self.filename = filename

    def download(self):
        '''
        リモートからローカルにダウンロードする。
        大量にダウンロードしつつ学習、というのがリスキーなため。
        API制限もあるし。
        '''
        import fusion_dao
        dao = fusion_dao.WordsDbDao()
        rec = dao.newer('2017-01-01')
        count = 0
        with file(self.filename, 'w') as f:
            f.write('\t'.join(rec['columns']))
            f.write('\n')
            for row in rec['rows']:
                f.write('\t'.join(row))
                f.write('\n')
                count += 1
        return count

    def reader(self):
        '''
        1レコードずつ返すジェネレータ
        '''
        with file(self.filename, 'r') as f:
            for line in f:
                yield line[:-1].decode('UTF-8').split('\t')


    def remove(self):
        '''
        ダウンロードしたファイルを削除
        '''
        os.remove(self.filename)

def dbreader():
    import fusion_dao
    dao = fusion_dao.WordsDbDao()
    records = dao.newer('2017-02-19')
    for record in records['rows']:
        # TODO カラム名との紐付け
        yield record


def train(filename = 'word2vec.model', mode = 'download', clean = False):
    '''
    mode 学習データの取得方法
    - download (default): DBから一旦ローカルに保存。そのファイルを読み込で学習
    - local: ローカルに保存されているファイルから学習
    - direct: 直接DBから読み込んで学習

    crean ローカルに保存されている学習用データを削除するかどうか
    - true: 学習後に削除する
    - false: 学習後に削除しない
    '''
    reader = None
    if mode == 'download':
        f = FileDao()
        f.download()
        reader = f.reader
    elif mode == 'local':
        reader = FileDao().reader
    elif mode == 'direct':
        reader = dbreader
    else:
        raise Exception('something wrong!')



if __name__ == "__main__":
    fileDao = FileDao()
    fileDao.download()
