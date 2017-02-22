# -*- coding: utf-8 -*-
from datetime import datetime as dt
from apiclient.http import MediaInMemoryUpload
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

class _DaoHelper(object):
    def __init__(self):
        self._service = None

    def getFusionService(self):
        if self._service == None:
            self._service = _initFusionService()
        return self._service

def _initFusionService():
    from googleapiclient import sample_tools
    args = [None, '--noauth_local_webserver']
    service, flags = sample_tools.init(args, 'fusiontables', 'v2', __doc__, __file__)
    return service

def _initFusionService1(args):
    from oauth2client.client import GoogleCredentials
    from googleapiclient.discovery import build
    import os
    if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './credentials.js'
    credentials = GoogleCredentials.get_application_default()
    return build('fusiontables', 'v2', credentials=credentials)

class RawDbDao(object):
    """
    RSSの生データにアクセスするためのDAO
    """
    def __init__(self):
        self.service = _helper.getFusionService()
        self.table_id = '1BjdqgQI9WJYskX_gB3FFbA0L6riNa_ZNL6eaFHL0'

    def newer(self, date, time = '00:00:00'):
        '''
        pubDateが指定より新しいのみを取得（形態素解析用）
        fusiontablesがdatetime型に（多分）対応していないため、時刻の絞り込みはスクリプト上で実施
        '''
        # ROWIDでの絞り込みが理想だが、数値型っぽく見えるけど文字列のように振る舞うので絞り込みに使えないorz

        sql = 'SELECT ROWID, source, title, link, pubDate, description FROM %s WHERE pubDate > \'%s\' order by pubDate DESC' % (self.table_id, date)
        # sql = 'SELECT ROWID, source, title, link, pubDate, description FROM %s WHERE ROWID > %d' % (self.table_id, row_id)
        records = self.service.query().sql(sql = sql).execute()
        if records.has_key('rows') and time != '00:00:00':
            # 時刻でフィルタ
            pubDateCol = records['columns'].index('pubDate')
            keyDateTime = dt.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
            records['rows'] = filter(lambda row: dt.strptime(row[pubDateCol], '%Y-%m-%d %H:%M:%S') >= keyDateTime ,records['rows'])
        elif not records.has_key('rows'):
            records['rows'] = []
        return records

    def row(self, row_ids):
        '''
        ROW_IDのリストを渡すと生データのリストを返す（Web用）
        '''
        sql = 'SELECT ROWID, source, title, link, pubDate, description FROM %s WHERE ROWID IN (%s)' % (self.table_id, ','.join([str(i) for i in row_ids]))
        records = self.service.query().sql(sql = sql).execute()
        if not records.has_key('rows'):
            records['rows'] = []
        return records

class WordsDbDao(object):
    '''
    ニュースが単語分割されたテーブルにアクセスするためのDAO
    '''
    def __init__(self):
        self.service = _helper.getFusionService()
        self.table_id = '1OEGMKcgMxGfz4e9UX_MYhv9SF1VKiv0px_T518uS'
        self.queue = []

    def appendQueue(self, rss_id, news, newsDatetime, pubDate):
        '''
        FusionTablesのアクセス制限に引っかからないように、insertは一括で実行するのが基本
        insertするデータをキューに加える
        '''
        self.queue.append({'rss_id': rss_id, 'news': news, 'newsDatetime': newsDatetime, 'pubDate': pubDate})

    def resetQueue(self):
        '''キューを空にする'''
        self.queue = []

    def commit(self):
        '''
        キューのデータをDBに書き込む
        return: 件数
        '''
        print '[debug] QUEUE COUNT: %d' % (len(self.queue))
        if len(self.queue) == 0:
            return 0
        rows = ''
        # RssId, WordList, NumberList, NewsDate, pubDate
        for q in self.queue:
            row = u'%s,"%s","%s","%s","%s"' % (q['rss_id'], ' '.join(q['news'].noun()), ' '.join(q['news'].meta().values()), q['newsDatetime'], q['pubDate'])
            rows += row + '\r\n'

        media = MediaInMemoryUpload(body = rows.encode('UTF-8'), mimetype='application/octet-stream', resumable=True)
        response = self.service.table().importRows(tableId = self.table_id, media_body=media, encoding='UTF-8').execute()
        self.queue = []
        return response[u'numRowsReceived']

    def newer(self, date, time = '00:00:00'):
        '''
        pubDateが指定より新しいのみを取得（新規ニュースの類似度判定）
        fusiontablesがdatetime型に（多分）対応していないため、時刻の絞り込みはスクリプト上で実施
        '''
        # ROWIDでの絞り込みが理想だが、数値型っぽく見えるけど文字列のように振る舞うので絞り込みに使えないorz

        sql = 'SELECT RssId, WordList, NumberList, NewsDate, PubDate FROM %s WHERE PubDate > \'%s\'' % (self.table_id, date)
        # sql = 'SELECT ROWID, source, title, link, pubDate, description FROM %s WHERE ROWID > %d' % (self.table_id, row_id)
        records = self.service.query().sql(sql = sql).execute()
        if records.has_key('rows') and time != '00:00:00':
            # 時刻でフィルタ
            pubDateCol = records['columns'].index('PubDate')
            keyDateTime = dt.strptime('%s %s' % (date, time), '%Y-%m-%d %H:%M:%S')
            records['rows'] = filter(lambda row: dt.strptime(row[pubDateCol], '%Y-%m-%d %H:%M:%S') >= keyDateTime ,records['rows'])
        elif not records.has_key('rows'):
            records['rows'] = []
        return records

    def row(self, rss_ids):
        '''
        RSS_IDのリストを渡すと生データのリストを返す（Web用）
        '''
        sql = 'SELECT RssId, WordList, NumberList, NewsDate, PubDate FROM %s WHERE RssId IN (%s)' % (self.table_id, ','.join([str(i) for i in rss_ids]))
        records = self.service.query().sql(sql = sql).execute()
        if not records.has_key('rows'):
            records['rows'] = []
        return records

    def delDuplicated(self):
        '''
        重複するレコードを削除するメンテナンス用のコマンド
        '''
        # TODO implement
        pass

_helper = _DaoHelper()

if __name__ == "__main__":
    pass
