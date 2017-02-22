# -*- coding: utf-8 -*-

from janome.tokenizer import Tokenizer
import normalize_neologd as nn
from range_date import range_date
import sys
import re


# import os

reload(sys)
sys.setdefaultencoding('utf-8')

t = Tokenizer()

class newsWords:
    '''
    与えられたニュース記事を正規化し、単語に分割する
    noun: 名詞の一覧
    meta: 日付に関する単語
    '''

    def __init__(self, text):
        self.text = nn.normalize_neologd(text)
        self.words = _getWords(self.text)

    def __str__(self):
        return '[%s] noun: %s / meta: %s' % \
            (self.text,\
            ','.join(self.words[0]),\
            ','.join([str(k) + ':' + self.words[1][k] for k in self.words[1]]))

    def noun(self):
        '''名詞の一覧'''
        return self.words[0]

    def meta(self):
        '''日付・時刻に関する数値を含む単語の一覧'''
        return self.words[1]

def _getWords(text):
    '''
    return forTrain, numbers
    基本的に名詞の表層表現を返す
    ただし数値に関して以下の取り扱いとする
    ・連続する数値は結合する（10,万 → 10万）
    ・数字＋接尾 は結合して考える（'4台 3階 10万円 など'）
    ・上記が日付の場合かつ日付が続く場合、結合して返す（1月,23日→1月23日）
    ・日付の直後の「前」「後」は結合して返す（「ごろ」など曖昧表現は加味しない）
    数量・日付はforTrainには出力されない（数値を学習しても意味がなく、ノイズ）
    numbersに一覧で出力される
    '''

    # 日時はそれを単語として扱う
    __timeSuffixA__ = [
                    u'月',
                    u'年',
                    u'週',
                    u'日',
                    u'時',
                    u'分',
                    u'秒',
                    u'か月',
                    u'ヶ月',
                    u'カ月',
                    u'ヵ月',
                    u'週間']
    __timeSuffixB__ = [u'前', u'後']
    __timePrefix__ = [u'明治', u'大正', u'昭和', u'平成', u'西暦', u'午前', u'午後'] #本当は年号と午前午後は分けるべき

    # 日付にならないもの
    # 年間
    # 月間
    # 日間
    # 時間
    # 分間
    # 秒間

    tokens = t.tokenize(text)

    # まずは下処理：名詞だけを抜き出す。それ以外のところは歯抜け状態にする
    empty = ['', '']
    wps = [['', u'-first-']]
    for token in tokens:
        pos = token.part_of_speech.split(',')
        if pos[0] == u'名詞':
            w = token.surface
            if w in [u'ヵ月', u'か月']:
                w = u'ヶ月'
            wordWithPos = [w, pos[1]]
            wps.append(wordWithPos)
        else:
            wps.append(empty)

    # "前後"を考慮するため、indexで考える
    for index in range(len(wps)):

        # 数字の処理：直後の数と結合
        if wps[index - 1][1] == u'数' and wps[index][1] == u'数':
            wps[index][0] = wps[index - 1][0] + wps[index][0]
            wps[index - 1][0] = ''
            wps[index - 1][1] = u'-num-'
            continue

        if wps[index - 1][1] == u'数' and wps[index][0] in __timeSuffixA__:
            wps[index][0] = wps[index - 1][0] + wps[index][0]
            wps[index][1] = u'date'
            wps[index - 1][0] = ''
            wps[index - 1][1] = u'-num-'

            for wp in wps[index - 1::-1]:
                if wp[1] == u'-num-':
                    continue
                elif wp[1] == u'date' or wp[0] in __timePrefix__ :
                    wps[index][0] = wp[0] + wps[index][0]
                    wp[0] = ''
                    wp[1] = u'-num-'
                else:
                    break

            continue

        if wps[index - 1][1] == u'date' and wps[index][0] in __timeSuffixB__:
            wps[index][0] = wps[index - 1][0] + wps[index][0]
            wps[index][1] = u'date'
            wps[index - 1][0] = ''
            wps[index - 1][1] = u'-num-'
            continue

        if wps[index - 1][1] == u'数' and wps[index][1] in [u'接尾']:
            wps[index][0] = wps[index - 1][0] + wps[index][0]
            wps[index][1] = u'数量'
            wps[index - 1][0] = ''
            wps[index - 1][1] = u'-num-'
            continue

    new_wps = filter(lambda wp: not wp[0] == '', wps)

    noun = map(lambda w: w[0], filter(lambda wp: wp[0] != '' and not wp[1] in [u'数', u'数量', u'date'], new_wps))
    noun = filter(lambda w: w not in u'!"#$%&\'()*+,-./:;<=>?@[¥]^_`{|}~｡､･｢｣', noun)

    meta = {}
    for index, wp in enumerate(new_wps):
        if wp[1] in [u'数量', u'date']:
            meta[index] = wp[0]

    return noun, meta

def _getJapaneseDate(nounlist, pubDate):
    # 日本語→数値
    dy = None
    dm = None
    dd = None
    dw = None
    for noun in nounlist:
        if noun in [u'おととい', u'一昨日']:
            dd = -2
            break
        if noun in [u'きのう', u'昨日', u'昨日', u'昨夜', u'昨晩', u'昨夕', u'前夜']:
            dd = -1
            break
        if noun in [u'今日',u'今朝',u'今晩',u'今夜']:
            dd = 0
            break
        if noun in [u'明日']:
            dd = 1
            break
        if noun in [u'明後日']:
            dd = 2
            break

        if noun in [u'先々週']:
            dw = -2
            break
        if noun in [u'先週']:
            dw = -1
            break
        if noun in [u'今週']:
            dw = 0
            break
        if noun in [u'来週']:
            dw = 1
            break
        if noun in [u'再来週']:
            dw = 2
            break

        if noun in [u'先々月']:
            dm = -2
            break
        if noun in [u'先月']:
            dm = -1
            break
        if noun in [u'来月']:
            dm = 1
            break
        if noun in [u'再来月']:
            dm = 2
            break

        if noun in [u'一昨年']:
            dy = -2
            break
        if noun in [u'昨年', u'去年']:
            dy = -1
            break
        if noun in [u'ことし', u'今年', u'本年']:
            dy = 0
            break
        if noun in [u'来年']:
            dy = 1
            break

    return dy, dm, dd, dw

def _getNewsDateTime(nounlist, meta, pubDate):
    '''
    いつの事件に関する記事かを解析する
    return range_date

    日時を特定できない場合はpubDateの日に発生した事象とみなす
    '''

    py = pubDate.year
    pm = pubDate.month
    pd = pubDate.day
    japaneseDate = _getJapaneseDate(nounlist, pubDate)

    # 「週」がほかの日付文字列と同時に出現することはほぼない（「先週12日」のような表現は、多少範囲が広くなるが「先週」で代替）
    if japaneseDate[3] != None:
        return range_date(py, pm, pd).addWeek(japaneseDate[3])

    pattern_ymd = u"^((平成|西暦){0,1}(\d+)(年前|年後|年)){0,1}((\d+)(ヶ+月前|ヶ+月後|月前|月後|月)){0,1}((\d+)(日前|日後|日)){0,1}"
    # 最初に見つかった時点で探索を終了する
    for k in meta:
        match = re.search(u'(\d+)週間(前|後)', meta[k])
        if match != None and match.group(0) != None:
            if match.group(2) == u'前':
                return range_date(py, pm, pd).minusWeek(int(match.group(1)))
            else:
                return range_date(py, pm, pd).addWeek(int(match.group(1)))

        match = re.search(pattern_ymd , meta[k])

        y_full = match.group(1) #年full
        y_gengo = match.group(2) #元号
        y_num = match.group(3) #年数値
        y_unit = match.group(4) #年記号

        m_full = match.group(5) #月full
        m_num = match.group(6) #月数値
        m_unit = match.group(7) #月記号

        d_full = match.group(8) #日full
        d_num = match.group(9) #日数値
        d_unit = match.group(10) #月記号

        if y_num == None and m_num == None and d_num == None and japaneseDate == (None, None, None, None):
            continue

        y = int(y_num) if isinstance(y_num, unicode) else None
        m = int(m_num) if isinstance(m_num, unicode) else None
        d = int(d_num) if isinstance(d_num, unicode) else None
        d_unit = d_unit if d_unit != None else ''
        m_unit = m_unit if m_unit != None else ''
        y_unit = y_unit if y_unit != None else ''

        # n年前 @ 日本語 e.g. 去年
        if japaneseDate[0] != None:
            return range_date(py, pm, pd).add(japaneseDate[0], None, None).month(m).day(d)

        # n月前 @ 日本語 e.g. 先月
        if japaneseDate[1] != None:
            return range_date(py, pm, pd).add(None, japaneseDate[1], None).day(d)

        # n日前 @ 日本語 e.g. 昨日
        if japaneseDate[2] != None:
            return range_date(py, pm, pd).add(None, None, japaneseDate[2])

        # y年m月d日前
        if u'前' in d_unit:
            return range_date(py, pm, pd).minus(y, m, d)
        if u'後' in d_unit:
            return range_date(py, pm, pd).add(m, m, d)

        # y年m月前 d日
        if u'前' in m_unit:
            return range_date(py, pm, pd).minus(y, m, None).day(d)
        if u'後' in m_unit:
            return range_date(py, pm, pd).add(m, m, None).day(d)

        # y年前 m月d日
        if u'前' in y_unit:
            return range_date(py, pm, pd).minus(y, None, None).month(m).day(d)
        if u'後' in y_unit:
            return range_date(py, pm, pd).add(y, None, None).month(m).day(d)

        # y年m月d日
        if y == None:
            y = py
            if m == None:
                m = pm
        elif y_gengo == u'平成':
            y += 1988
        elif y < 100:
            y += 2000

        return range_date(y, m, d)

    # n年前 @ 日本語 e.g. 去年
    if japaneseDate[0] != None:
        return range_date(py, pm, pd).add(japaneseDate[0], None, None)

    # n月前 @ 日本語 e.g. 先月
    if japaneseDate[1] != None:
        return range_date(py, pm, pd).add(0, japaneseDate[1], None)

    # n日前 @ 日本語 e.g. 昨日
    if japaneseDate[2] != None:
        return range_date(py, pm, pd).add(0, 0, japaneseDate[2])

    return range_date(py, pm, pd)

def getNewsDateTime(news, pubDate):
    return _getNewsDateTime(news.noun(), news.meta(), pubDate)

def _getNewsDateTime_old(nounlist, meta, pubDate):
    '''
    いつの事件に関する記事かを解析する
    return start, end

    日時を特定できない場合はpubDateの日に発生した事象とみなす
    '''

    japaneseDate = _getJapaneseDate(nounlist, pubDate)

    datetype_y = None
    datetype_m = None
    datetype_d = None

    py = pubDate.year
    pm = pubDate.month
    pd = pubDate.day

    pattern = u"^((平成|西暦){0,1}(\d+)(年前|年後|年)){0,1}((\d+)(ヶ+月前|ヶ+月後|月前|月後|月)){0,1}((\d+)(日前|日後|日)){0,1}"
    for k in meta:
        y = None
        m = None
        d = None


        match = re.search(pattern , meta[k])

        if True:
            print '------'
            print k
            for i in range(11):
                print i, match.group(i)
            print '------'

        y_full = match.group(1) #年full
        y_gengo = match.group(2) #元号
        y_num = match.group(3) #年数値
        y_unit = match.group(4) #年記号

        m_full = match.group(5) #月full
        m_num = match.group(6) #月数値
        m_unit = match.group(7) #月記号

        d_full = match.group(8) #日full
        d_num = match.group(9) #日数値
        d_unit = match.group(10) #月記号

        if y_gengo == u'平成':
            y = 1988 + int(y_num)
        elif y_num != None:
            y = int(y_num)
        if m_num != None:
            m = int(m_num)
        if d_num != None:
            d = int(d_num)

        # y年m月前 と y年前(の)m月 を区別に留意

        if y_unit in [u'年']:
            datetype_y = 'th'
        if y_unit in [u'年前']:
            datetype_y = 'ago'
        if y_unit in [u'年後']:
            datetype_y = 'after'

        if m_unit in [u'月']:
            datetype_m = 'th'
        if m_unit in [u'月前', u'ヶ月前']:
            datetype_m = 'ago'
        if m_unit in [u'月後', u'ヶ月後']:
            datetype_m = 'after'

        if d_unit in [u'日']:
            datetype_d = 'th'
        if d_unit in [u'日前']:
            datetype_d = 'ago'
        if d_unit in [u'日後']:
            datetype_d = 'after'

        print '*', y, datetype_y, m, datetype_m, d, datetype_d

        if datetype_y == 'ago':
            return range_date(py, pm, pd).minus(y, None, None)
        if datetype_m == 'ago':
            return range_date(py, pm, pd).minus(y, m, None)
        if datetype_d == 'ago':
            return range_date(py, pm, pd).minus(y, m, d)

        if datetype_y == 'after':
            return range_date(py, pm, pd).add(y, None, None)
        if datetype_m == 'after':
            return range_date(py, pm, pd).add(y, m, None)
        if datetype_d == 'after':
            return range_date(py, pm, pd).add(y, m, d)


        datetype = [datetype_y == 'th', datetype_m == 'th', datetype_d == 'th']
        # 末日
        if datetype in [[True, False, False]]:
            if y < 100:
                y += 2000
            return range_date(y, None, None)
        if datetype in [[True, True, False], [False, True, False]]:
            if japaneseDate[0] != None:
                y == py + japaneseDate[0]
            if y == None:
                y = py
            if y < 100:
                y += 2000
            return range_date(y, m, None)
        if datetype in [[True, True, True], [False, True, True], [False, False, True]]:
            if japaneseDate[0] != None:
                y = py + japaneseDate[0]
            if y == None:
                y = py
            if y < 100:
                y += 2000

            if japaneseDate[1] != None:
                return range_date(y, pm, None).add(0, japaneseDate[1], None).day(d)

            if m == None:
                m = pm
            return range_date(y, m, d)
        if datetype == [False, False, False]:
            if japaneseDate[0] != None:
                return range_date(py, None, None).add(japaneseDate[0], None, None)
            elif japaneseDate[1] != None:
                return range_date(py, pm, None).add(0, japaneseDate[1], None)
            elif japaneseDate[2] != None:
                return range_date(py, pm, pd).add(0, 0, japaneseDate[2])

    return  range_date(py, pm, pd)


def _doTest(tester):
    import time
    start = time.time()
    tester()
    elapsed_time = time.time() - start
    print ("elapsed_time:{0}".format(elapsed_time)) + "[sec]"

if __name__ == '__main__':


    def getWordsTest():
        assert _getWords(u'夕飯を食べる') == ([u'夕飯'], {})
        assert _getWords(u'あの日あの時') == ([u'日', u'時'], {})
        assert _getWords(u'ナンバー3の男') == ([u'ナンバー', u'男'], {})
        assert _getWords(u'3分クッキング') == ([u'クッキング'], {0: u'3分'}) # 3分 を時刻にするかどうかは次のステップ
        assert _getWords(u'建物の12階から') == ([u'建物'], {1: u'12階'})
        assert _getWords(u'年俸12億円以上') == ([u'年俸', u'以上'], {1: u'12億円'})
        assert _getWords(u'1兆2345億6789万1000円') == ([], {0: u'1兆2345億6789万1000円'})
        assert _getWords(u'先月1日未明') == ([u'先月', u'未明'], {1: u'1日'})
        assert _getWords(u'これから1月30日まで') == ([], {0: u'1月30日'})
        assert _getWords(u'犯人は3日前に') == ([u'犯人'], {1: u'3日前'})
        assert _getWords(u'3月前の') == ([], {0: u'3月前'})
        assert _getWords(u'3ヵ月前の') == ([], {0: u'3ヶ月前'})
        assert _getWords(u'3か月前の') == ([], {0: u'3ヶ月前'})
        assert _getWords(u'3ヶ月前の') == ([], {0: u'3ヶ月前'})
        assert _getWords(u'今年1年間の') == ([u'今年'], {1: u'1年間'})
        assert _getWords(u'3週間前に') == ([], {0: u'3週間前'})
        assert _getWords(u'1月1週の') == ([], {0: u'1月1週'})
        assert _getWords(u'3月3回目の') == ([u'目'], {0: u'3月', 1: u'3回'})
        assert _getWords(u'きょう午前5時ごろ') == ([u'きょう', u'ごろ'], {1: u'午前5時'})
        assert _getWords(u'これは、2016年10月30日に') == ([u'これ'], {1: u'2016年10月30日'})
        assert _getWords(u'3日午後、') == ([u'午後'], {0: u'3日'})
        assert _getWords(u'平成27年12月期') == ([u'期'], {0: u'平成27年12月'})
        assert _getWords(u'今年14回目の') == ([u'今年', u'目'], {1: '14回'})
        assert _getWords(u'今年1月、') == ([u'今年'], {1: u'1月'})
        assert _getWords(u'3年前の1月') == ([], {0: u'3年前', 1: u'1月'})

    def getNewsDateTimeTest():
        from datetime import date
        pubDate = date(2017,5,27)

        assert _getNewsDateTime([], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'昼食'], {}, pubDate) == range_date(2017, 5, 27)

        # 「月」「日」など不完全に数値指定
        assert _getNewsDateTime([], {0: u'12月'}, pubDate) == range_date(2017, 12, None)
        assert _getNewsDateTime([], {0: u'2日'}, pubDate) == range_date(2017, 5, 2)
        assert _getNewsDateTime([], {0: u'2月2日'}, pubDate) == range_date(2017, 2, 2)
        assert _getNewsDateTime([], {0: u'2016年'}, pubDate) == range_date(2016, None, None)
        assert _getNewsDateTime([], {0: u'2016年4月'}, pubDate) == range_date(2016, 4, None)
        assert _getNewsDateTime([], {0: u'2016年4月5日'}, pubDate) == range_date(2016, 4, 5)

        # 元号
        assert _getNewsDateTime([], {0: u'西暦2016年'}, pubDate) == range_date(2016, None, None)
        assert _getNewsDateTime([], {0: u'西暦2016年4月5日'}, pubDate) == range_date(2016, 4, 5)
        assert _getNewsDateTime([], {0: u'平成28年'}, pubDate) == range_date(2016, None, None)

        # 不明なやつは無視
        assert _getNewsDateTime([], {0: u'16年'}, pubDate) == range_date(2016, None, None)

        # n月前、n日前など相対値指定
        assert _getNewsDateTime([], {0: u'3日前'}, pubDate) == range_date(2017, 5, 24)
        # 2ヶ月前のできごと＝61日前ではない
        assert _getNewsDateTime([], {0: u'2月前'}, pubDate) == range_date(2017, 3, None)
        assert _getNewsDateTime([], {0: u'2ヶ月前'}, pubDate) == range_date(2017, 3, None)
        assert _getNewsDateTime([], {0: u'2年前'}, pubDate) == range_date(2015, None, None)
        assert _getNewsDateTime([], {0: u'2年2ヶ月前'}, pubDate) == range_date(2015, 3, None)
        assert _getNewsDateTime([], {0: u'2年後'}, pubDate) == range_date(2019, None, None)

        # 時・分は無視
        assert _getNewsDateTime([u'午前'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([], {0: u'午前2時'}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([], {0: u'13時'}, pubDate) == range_date(2017, 5, 27)

        # 日本語での指定
        assert _getNewsDateTime([u'きょう'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'本日'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'今日'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'今朝'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'今晩'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'今夜'], {}, pubDate) == range_date(2017, 5, 27)
        assert _getNewsDateTime([u'昨日'], {}, pubDate) == range_date(2017, 5, 26)
        assert _getNewsDateTime([u'きのう'], {}, pubDate) == range_date(2017, 5, 26)
        assert _getNewsDateTime([u'昨夜'], {}, pubDate) == range_date(2017, 5, 26)
        assert _getNewsDateTime([u'昨晩'], {}, pubDate) == range_date(2017, 5, 26)
        assert _getNewsDateTime([u'おととい'], {}, pubDate) == range_date(2017, 5, 25)
        assert _getNewsDateTime([u'一昨日'], {}, pubDate) == range_date(2017, 5, 25)
        assert _getNewsDateTime([u'明日'], {}, pubDate) == range_date(2017, 5, 28)
        assert _getNewsDateTime([u'明後日'], {}, pubDate) == range_date(2017, 5, 29)
        assert _getNewsDateTime([u'先月'], {}, pubDate) == range_date(2017, 4, None)
        assert _getNewsDateTime([u'先々月'], {}, pubDate) == range_date(2017, 3, None)
        assert _getNewsDateTime([u'来月'], {}, pubDate) == range_date(2017, 6, None)
        assert _getNewsDateTime([u'再来月'], {}, pubDate) == range_date(2017, 7, None)
        assert _getNewsDateTime([u'ことし'], {}, pubDate) == range_date(2017, None, None)
        assert _getNewsDateTime([u'今年'], {}, pubDate) == range_date(2017, None, None)
        assert _getNewsDateTime([u'去年'], {}, pubDate) == range_date(2016, None, None)
        assert _getNewsDateTime([u'昨年'], {}, pubDate) == range_date(2016, None, None)
        assert _getNewsDateTime([u'来年'], {}, pubDate) == range_date(2018, None, None)

        # 複合
        assert _getNewsDateTime([u'今月'], {1: u'2日'}, pubDate) == range_date(2017, 5, 2)
        assert _getNewsDateTime([u'先月'], {1: u'24日'}, pubDate) == range_date(2017, 4, 24)
        assert _getNewsDateTime([u'今年'], {1: u'3月'}, pubDate) == range_date(2017, 3, None)
        assert _getNewsDateTime([u'昨年'], {1: u'12月14日'}, pubDate) == range_date(2016, 12, 14)
        assert _getNewsDateTime([u'昨夜'], {1: u'10時'}, pubDate) == range_date(2017, 5, 26)

        # 期間
        assert _getNewsDateTime([u'先月', u'今月'], {}, pubDate) == range_date(2017, 4, None)
        assert _getNewsDateTime([], {0: u'1月', 1: u'3月'}, pubDate) == range_date(2017, 1, None)

        # 最初のやつ採用
        # 期間じゃない
        assert _getNewsDateTime([u'今年'], {0: '4日'}, pubDate) == range_date(2017, None, None)
        # 「今月4日に発表された昨年の雇用統計」
        assert _getNewsDateTime([u'昨年', u'今月'], {0: '4日'}, pubDate) == range_date(2016, None, None)
        assert _getNewsDateTime([u'今年', u'昨年'], {0: '4日'}, pubDate) == range_date(2017, None, None)

        # いったん日曜はじまりで
        assert _getNewsDateTime([u'先週'], {}, pubDate) == range_date(2017, 5, 27).minusWeek(1)
        assert _getNewsDateTime([u'再来週'], {}, pubDate) == range_date(2017, 5, 27).addWeek(2)
        assert _getNewsDateTime([], {0: u'2週間前'}, pubDate) == range_date(2017, 5, 27).minusWeek(2)

        # 複数 ...?


    _doTest(getWordsTest)

    _doTest(getNewsDateTimeTest)
