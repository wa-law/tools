import requests_cache
from bs4 import BeautifulSoup

api_root_url = "http://wslwebservices.leg.wa.gov"

requests = requests_cache.CachedSession("cache")

for start_year in range(2019, 2023, 2):
    biennium = f"{start_year:4d}-{(start_year+1) % 100:02d}"
    print(biennium)

    url = api_root_url + f"/SponsorService.asmx/GetRequesters?biennium={biennium}"
    requesters = requests.get(url)
    requesters = BeautifulSoup(requesters.text, "xml")
    count = 0
    for info in requesters.find_all("LegislativeEntity"):
        count += 1
    print(count, "requesters")

    sponsors_by_id = {}

    url = api_root_url + f"/SponsorService.asmx/GetSponsors?biennium={biennium}"
    sponsors = requests.get(url)
    sponsors = BeautifulSoup(sponsors.text, "xml")
    count = 0
    for info in sponsors.find_all("Member"):
        # if count == 0:
        #     print(info)
        sponsors_by_id[info.Id.text] = info.Email.text
        count += 1
    print(count, "sponsors")


    url = api_root_url + f"/LegislativeDocumentService.asmx/GetAllDocumentsByClass?biennium={biennium}&documentClass=Bills"
    print(url)
    all_bill_docs = BeautifulSoup(requests.get(url).text, "xml")
    docs_by_id = {}
    count = 0
    for doc in all_bill_docs.find_all("LegislativeDocument"):
        bill_id = doc.BillId.text
        # if count == 0:
        #     print(doc)
        docs_by_id[bill_id] = doc
        # print(amendment.Name.text, amendment.BillId.text)
        count += 1
    print(count, "bill docs")

    url = api_root_url + f"/LegislationService.asmx/GetLegislationByYear?year={start_year}"
    legislation = requests.get(url)
    legislation = BeautifulSoup(legislation.text, "xml")
    count = 0
    bills_by_sponsor = {}
    for info in legislation.find_all("LegislationInfo"):
        bill_number = info.BillNumber.text
        bill_id = info.BillId.text
        # Skip governor appointments
        if bill_id.startswith("SGA"):
            continue

        bills = api_root_url + f"/LegislationService.asmx/GetLegislation?biennium={biennium}&billNumber={bill_number}"
        bills = requests.get(bills)
        bills = BeautifulSoup(bills.text, "xml")
        full_info = None
        for bill in bills.find_all("Legislation"):
            if bill_id != bill.BillId.text:
                continue
            full_info = bill
        sponsor_id = full_info.PrimeSponsorID.text
        if bill_id not in docs_by_id:
            print(bill_id, "missing doc")
        if sponsor_id not in sponsors_by_id:
            print(sponsor_id, "missing sponsor for bill", bill_id)
        if sponsor_id not in bills_by_sponsor:
            bills_by_sponsor[sponsor_id] = []
        bills_by_sponsor[sponsor_id].append(full_info)

        count += 1
    print(count, "legislation")
    print()

    url = api_root_url + f"/LegislationService.asmx/GetLegislationByYear?year={start_year+1}"
    legislation = requests.get(url)
    legislation = BeautifulSoup(legislation.text, "xml")
    count = 0
    for info in legislation.find_all("LegislationInfo"):
        bill_number = info.BillNumber.text
        # if count == 0:
        #     print(info)
        #     bill = api_root_url + f"/LegislationService.asmx/GetLegislation?biennium={biennium}&billNumber={bill_number}"
        #     bill = requests.get(bill)
        #     bill = BeautifulSoup(bill.text, "xml")
        #     print(bill)
        # print(amendment.Name.text, amendment.BillId.text)
        count += 1
    print(count, "legislation")

    amendments_by_bill_id = {}

    url = api_root_url + f"/AmendmentService.asmx/GetAmendments?year={start_year}"
    amendments = requests.get(url)
    amendments = BeautifulSoup(amendments.text, "xml")
    count = 0
    for amendment in amendments.find_all("Amendment"):
        bill_id = amendment.BillId.text
        if bill_id not in amendments_by_bill_id:
            amendments_by_bill_id[bill_id] = []
        amendments_by_bill_id[bill_id].append(amendment)
        # print(amendment.Name.text, )
        count += 1
    print(count, "amendments")

    url = api_root_url + f"/AmendmentService.asmx/GetAmendments?year={start_year+1}"
    amendments = requests.get(url)
    amendments = BeautifulSoup(amendments.text, "xml")
    count = 0
    for amendment in amendments.find_all("Amendment"):
        bill_id = amendment.BillId.text
        if bill_id not in amendments_by_bill_id:
            amendments_by_bill_id[bill_id] = []
        amendments_by_bill_id[bill_id].append(amendment)
        # print(amendment.Name.text, amendment.BillId.text)
        count += 1
    print(count, "amendments")
    print()


    robinson = "16499"

    for bill in bills_by_sponsor[robinson]:
        bill_id = bill.BillId.text
        print(bill_id, bill.ShortDescription.text)
        print(bill.HistoryLine.text)
        if bill_id in amendments_by_bill_id:
            for amendment in amendments_by_bill_id[bill_id]:
                print(amendment.Name.text, amendment.SponsorName, amendment.Description.text, amendment.FloorAction.text)
                print(amendment.HtmUrl.text)
                print(amendment)
                print()
            # print(amendment)
        else:
            print("no amendments")
        print()
    print(sponsor_id, sponsors_by_id[robinson])
