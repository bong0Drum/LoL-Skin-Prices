import requests, re, math
from bs4 import BeautifulSoup

getSoup = lambda url: BeautifulSoup(requests.get(url).content, 'html.parser')
wrapInQuotes = lambda s: f'"{s}"'
# if we're writing to a CSV, we need to wrap columns in quotations if the column may contain commans
writeCSVLine = lambda wf, arr: wf.write(','.join(arr) + '\n')
roundDecimalsUp = lambda d: math.ceil(d*100.0)/100
# if we're talking money, can't simply use the round function, gotta round up
getText = lambda el: el.get_text().strip()

mobafireUrl = "https://www.mobafire.com/league-of-legends/skins"

def writeSkinDataAndGetTotalRp():
    mobafireSoup = getSoup(mobafireUrl)

    pageEls = mobafireSoup.find("div", "browse-pager__pages").find_all()
    lastPageNo = int(pageEls[-1].get_text())

    mobafirePages = [mobafireSoup]

    print('\tgetting skins...')

    for pageNo in range(2, lastPageNo + 1):
        print(f'\t\tgetting page {pageNo}/{lastPageNo}')
        pageSoup = getSoup(f'{mobafireUrl}?page={pageNo}')
        mobafirePages.append(pageSoup)


    totalRp = 0

    with open('skins.csv', 'w') as f:

        wroteHeader = False
        
        for page in mobafirePages:
            skins = page.find_all("a", class_="champ-skins__item")
            for skin in skins:
                
                nameContainer = skin.find("div", class_="champ-skins__item__meta")
                name = wrapInQuotes(getText(nameContainer.find("h3")))
                
                skinType = getText(skin.find("p", class_="byline").find())
                
                skinUrlMatch = re.search(r'/league-of-legends/skins/([^#]+)#(.*)', skin['href'])
                champName = skinUrlMatch.group(1)
                skinLine = wrapInQuotes(skinUrlMatch.group(2))
                
                costEl = skin.find("div", class_="champ-skins__item__cost")
                cost = '' if costEl is None else getText(costEl)

                totalRp += int(cost or '0')

                dateEl = skin.find("p", class_="date").find()
                date = '' if dateEl is None else wrapInQuotes(getText(dateEl))

                if skinLine == 'classic':
                    continue
                
                data = {'name': name, 'cost': cost, 'champName': champName, 'skinLine': skinLine, 'date': date}
                
                if not wroteHeader:
                    wroteHeader = True
                    writeCSVLine(f, data.keys())
                    
                writeCSVLine(f, data.values())

    return totalRp

def getMaxDollarRpRatio():
    rpPriceSoup = getSoup('https://na.leagueoflegends.com/en/community/prepaid-cards')
    usRpPriceTable = rpPriceSoup.find_all('tbody')[0]

    maxDollarRpRatio = 0

    for usRpPriceRow in usRpPriceTable:
        dollarAmtStr, rpAmtStr = [getText(col) for col in usRpPriceRow.find_all()]
        
        dollarAmt = float(re.search(r'\$(\d*\.?\d*) US', dollarAmtStr).group(1))
        rpAmt = int(rpAmtStr.replace(',', ''))

        dollarRpRatio = rpAmt / dollarAmt
        maxDollarRpRatio = max(maxDollarRpRatio, dollarRpRatio)

    return maxDollarRpRatio

if __name__ == "__main__":
    

    totalRp = writeSkinDataAndGetTotalRp()
    print('\ntotal RP for all skins:', totalRp, 'RP')

    maxDollarRpRatio = getMaxDollarRpRatio()
    print(f'best RP to US dollar ratio: {roundDecimalsUp(maxDollarRpRatio):.2f}')

    totalCost = roundDecimalsUp(totalRp / maxDollarRpRatio)
    print(f'total cost of all skins in US dollars: ${totalCost:.2f}')

