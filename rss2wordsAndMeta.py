# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import range_date
import text2wordAndMeta as twm
import fusion_dao
from datetime import datetime as dt

reload(sys)
sys.setdefaultencoding('utf-8')

def row2words(date, time):
    print 'rawdao'
    rawdao = fusion_dao.RawDbDao(sys.argv)
    print 'worddao'
    worddao = fusion_dao.WordsDbDao(sys.argv)
    print 'records'
    recoeds = rawdao.newer(date, time)
    print 'tokenizer'
    # 重複をここで除外する
    linkUrls = set([])
    for record in recoeds['rows']:
        link = record[recoeds['columns'].index('link')]
        if link in linkUrls:
            continue
        linkUrls.add(link)
        row_id = record[recoeds['columns'].index('rowid')]
        news = twm.newsWords(record[recoeds['columns'].index('description')])
        pubDate = dt.strptime(record[recoeds['columns'].index('pubDate')], '%Y-%m-%d %H:%M:%S')
        # 将来的には複数の日付に対応したい。半角スペース区切りでいいかな
        newsDatetime = repr(twm.getNewsDateTime(news, pubDate))
        worddao.appendQueue(row_id, news, newsDatetime, pubDate)
    print 'commit'
    result = worddao.commit()
    print result

def getWords(date, time):
    worddao = fusion_dao.WordsDbDao(sys.argv)
    return worddao.newer(date, time)

def getRecord(rss_ids):
    worddao = fusion_dao.WordsDbDao(sys.argv)
    return worddao.row(rss_ids)

if __name__ == '__main__':
    # row2words('2017-02-16', '09:00:00')
    # res = getWords('2017-02-16', '09:25:00')
    res = getRecord(['113000'])
    print res
