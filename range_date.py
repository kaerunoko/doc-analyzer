# -*- coding: utf-8 -*-
from datetime import datetime, date
from dateutil.rrule import *
from dateutil.relativedelta import relativedelta
import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

class range_date:
    '''
    「年だけ」「年月だけ」「年月日」を表現するクラス
    '''
    def __init__(self, year, month, day):
        if year == None:
            raise Exception('Year must not be None')
        if month == None and day != None:
            raise Exception('Illegal argument')
        if month != None and not month in range(1, 13):
            raise Exception('Month must be 1..12')
        self._year = year
        self._month = month
        self._day = day
        self._week = None

    def __str__(self):
        return '%d,%s,%s' % (self._year, str(self._month) if self._month != None else '*', str(self._day) if self._day != None else '*')\
        + ('[week: %d]' % (self._week) if self._week != None else '')

    def __eq__(self, other):
        return isinstance(self, range_date) \
              and isinstance(other, range_date) \
              and self.startDate() == other.startDate() \
              and self.endDate() == other.endDate()

    def __ne__(self, other):
        return not isinstance(self, range_date) \
              or not isinstance(other, range_date) \
              or not self.startDate() == other.startDate() \
              or not self.endDate() == other.endDate()

    def startDate(self):
        y = self._year
        m = self._month if self._month != None else 1
        d = self._day if self._day != None else 1
        if self._week == None:
            return date(y, m, d)
        else:
            weekSun = date(self._year, self._month, self._day) + relativedelta(days=+1, weekday=SU(-1))
            if self._week != 0:
                weekSun = weekSun + relativedelta(days = 7 * self._week)
            return weekSun

    def endDate(self):
        y = self._year
        if self._month == None:
            return date(y, 1, 1) + relativedelta(years = 1) - relativedelta(days = 1)
        elif self._day == None:
            return date(y, self._month, 1) + relativedelta(months = 1) - relativedelta(days = 1)
        elif self._week == None:
            return date(y, self._month, self._day)
        else:
            weekSun = date(self._year, self._month, self._day) + relativedelta(days=+1, weekday=SU(-1))
            if self._week != 0:
                weekSun = weekSun + relativedelta(days = 7 * self._week)
            return weekSun + relativedelta(days = +7)

    def minus(self, year, month, day):
        if year != None:
            year = -year
        if month != None:
            month = -month
        if day != None:
            day = -day
        return self.add(year, month, day)

    def add(self, year, month, day):
        self._week = None
        if self._month == None and month != None:
            raise Exception('Month does not defined')
        if self._day == None and day != None:
            raise Exception('Day does not defined')

        if month == None and day == None: #3年前　とか
            if year != None:
                self._year += year
            self._month = None
            self._day = None
        elif day == None: #2年2ヶ月前　とか
            if year != None:
                self._year += year
            if month != None:
                self._month += month
                if self._month > 12:
                    self._month -= 12
                    self._year += 1
                elif self._month < 1:
                    self._month += 12
                    self._year -= 1
            self._day = None
        else:
            if year == None:
                year = 0
            if month == None:
                month = 0
            newDay = date(self._year, self._month, self._day) + relativedelta(years = year) + relativedelta(months = month) + relativedelta(days = day)
            self._year = newDay.year
            self._month = newDay.month
            self._day = newDay.day

        return self

    def year(self, year):
        self._year = year
        self._week = None
        return self

    def month(self, month):
        self._month = month
        self._week = None
        return self

    def day(self, day):
        self._day = day
        self._week = None
        return self

    def minusWeek(self, week):
        if week != None:
            week = -week
        return self.addWeek(week)

    def addWeek(self, week):
        if week != None\
        and (self._day == None\
        or self._month == None):
            raise Exception('When use week, month and day must be defined')
        self._week = week
        return self


def _doTest(tester):
    start = time.time()
    tester()
    elapsed_time = time.time() - start
    print ("elapsed_time:{0}".format(elapsed_time)) + "[sec]"

if __name__ == '__main__':
    def range_date_test():
        range_date(2017, None, None)
        range_date(2017, 12, None)
        range_date(2017, 12, 1)

        try:
            range_date(2017, None, 1)
            raise AssertionError()
        except AssertionError as e:
            raise e
        except Exception as e:
            pass

        try:
            range_date(2017, 13, 1)
            raise AssertionError()
        except AssertionError as e:
            raise e
        except Exception as e:
            pass

        assert range_date(2017, None, None).startDate() == date(2017, 1, 1)
        assert range_date(2017, None, None).endDate() == date(2017, 12, 31)
        assert range_date(2017, 2, None).startDate() == date(2017, 2, 1)
        assert range_date(2017, 2, None).endDate() == date(2017, 2, 28)
        assert range_date(2017, 3, 4).startDate() == date(2017, 3, 4)
        assert range_date(2017, 3, 4).endDate() == date(2017, 3, 4)
        assert range_date(2017, 3, 4).add(1,None,None).startDate() == date(2018, 1, 1)
        assert range_date(2017, 3, 4).add(None,1,None).startDate() == date(2017, 4, 1)
        # 先月5日
        assert range_date(2017, 3, 4).add(None,-1,None).endDate() == date(2017, 2, 28)
        assert range_date(2017, 3, 4).add(None,-1,None).day(5).endDate() == date(2017, 2, 5)

        # 今週：日曜始まり・月曜始まりの揺れをカバーするため、前後の日曜を含むようにする
        assert range_date(2017, 2, 1).addWeek(0).startDate() == date(2017, 1, 29)
        assert range_date(2017, 2, 1).addWeek(0).endDate() == date(2017, 2, 5)
        assert range_date(2017, 2, 5).addWeek(0).startDate() == date(2017, 2, 5)
        assert range_date(2017, 2, 5).addWeek(0).endDate() == date(2017, 2, 12)
        assert range_date(2017, 2, 1).addWeek(1).startDate() == date(2017, 2, 5)
        assert range_date(2017, 2, 1).addWeek(1).endDate() == date(2017, 2, 12)
        assert range_date(2017, 2, 1).addWeek(-1).startDate() == date(2017, 1, 22)
        assert range_date(2017, 2, 1).addWeek(-1).endDate() == date(2017, 1, 29)
        assert range_date(2017, 2, 1).minusWeek(1).startDate() == date(2017, 1, 22)
        assert range_date(2017, 2, 1).minusWeek(1).endDate() == date(2017, 1, 29)
        assert range_date(2017, 2, 1).addWeek(None).startDate() == date(2017, 2, 1)
        assert range_date(2017, 2, 1).addWeek(None).endDate() == date(2017, 2, 1)

        assert range_date(2017, 2, 1).addWeek(1).day(4).endDate() == date(2017, 2, 4)

    _doTest(range_date_test)
