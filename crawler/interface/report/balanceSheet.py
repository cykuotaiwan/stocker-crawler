import json
import random
import time

import requests
from crawler.core.basicInfo import crawlSummaryStockNoFromTWSE
from crawler.core.report import crawlBalanceSheet
from crawler.interface.basicInfo import (getStockNoBasicInfo,
                                         getSummaryStockNoServerExist)
from crawler.interface.util import (SLEEP_TIME, balanceSheetKeySel,
                                    companyTypes, stockerUrl,
                                    transformHeaderNoun)


def getBalanceSheet(companyID=2330, westernYearIn=2019, seasonIn=2):
    """
    @Description:
        爬取及更新個別上市/上櫃公司資產負債表\n
        Crawl and update balance sheet of single sii/otc company
    @Param:
        companyID => int (stock id)
        westernYearIn => int (western year)
        seasonIn => int (1, 2, 3, 4)
    @Return:
        dict (stock id & status)
    """
    
    try:
        data = crawlBalanceSheet(companyID, westernYearIn, seasonIn)
    except ConnectionError as ce:
        return {"stock_id": companyID, "status": ce.args[0]}
    except IndexError:
        return {"stock_id": companyID, "status": 'IndexError'}
    except Exception as e:
        return {"stock_id": companyID, "status": e.args[0]}

    data = transformHeaderNoun(data, "balance_sheet")

    dataPayload = {}

    for key in balanceSheetKeySel:
        try:
            if key in data.index:
                dataPayload[key] = data.loc[key][0]
            else:
                dataPayload[key] = None
        except Exception as ex:
            print(ex)

    dataPayload['year'] = westernYearIn
    dataPayload['season'] = str(seasonIn)

    balanceSheetApi = "{}/daily_information/{}".format(stockerUrl, companyID)
    res = requests.post(balanceSheetApi, data=json.dumps(dataPayload))

    if res.status_code == 201:
        return {"stock_id": companyID, "status": "ok"}
    else:
        return {"stock_id": companyID, "status": res.status_code}


def updateBalanceSheet(westernYearIn=2019, season=1):
    """
    @Description:
        更新所有上市/上櫃公司資產負債表\n
        Update balance sheet of all sii/otc companies to
        stocker server\n
        1. Get list should be updated
        2. Update balance sheet of each company with getBalanceSheet
    @Param:
        westernYearIn => int (western year)
        seasonIn => int (1, 2, 3, 4)
    @Return:
        N/A
    """

    existStockNo = getSummaryStockNoServerExist(
        westernYearIn, season, 'balance_sheet')
    validStockNo = getStockNoBasicInfo()

    crawlList = []
    for companyType in companyTypes:
        targetStockNo = crawlSummaryStockNoFromTWSE(
            'balance_sheet', companyType, westernYearIn, season)
        if len(targetStockNo) == 0:
            continue
        if len(existStockNo) != 0:
            for no in targetStockNo:
                if str(no) not in existStockNo and\
                   str(no) in validStockNo:
                    crawlList.append(no)
        else:
            crawlList.extend(targetStockNo)

    total = len(crawlList)
    exceptList = []

    for idx, stock in enumerate(crawlList):
        print("(" + str(idx) + "/" + str(total) + ")", end=' ')
        crawlerResult = getBalanceSheet(stock, westernYearIn, season)
        print(crawlerResult['stock_id'], crawlerResult['status'])
        if crawlerResult["status"] == 'IndexError':
            time.sleep(90)
        if crawlerResult["status"] != 'ok':
            exceptList.append({
                "stock_id": crawlerResult["stock_id"],
                "retry_times": 0
            })
        time.sleep(SLEEP_TIME + random.randrange(0, 4))

    while(len(exceptList)):
        reCrawler = getBalanceSheet(
            exceptList[0]["stock_id"], westernYearIn, season)
        if reCrawler["status"] == 'ok':
            del exceptList[0]
        elif exceptList[0]["retry_times"] == 2:
            print("cancel stock_id: %s, retry over 3 times."
                  % reCrawler["stock_id"])
            del exceptList[0]
        else:
            tmpStock = exceptList.pop(0)
            tmpStock["retry_times"] = tmpStock["retry_times"]+1
            exceptList.append(tmpStock)
        time.sleep(SLEEP_TIME + random.randrange(0, 4))
