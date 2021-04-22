import requests_cache
from bs4 import BeautifulSoup, NavigableString
import re

api_root_url = "http://wslwebservices.leg.wa.gov"

requests = requests_cache.CachedSession("cache")

rcw_pattern = re.compile("RCW  ([0-9A-Z]+)\\.([0-9A-Z]+)\\.([0-9A-Z]+)")
chapter_pattern = re.compile("([0-9A-Z]+)\\.([0-9A-Z]+) RCW")

def get_citation(xml):
    t = xml.TitleNumber
    if t:
        t = t.text
    c = xml.ChapterNumber
    if c:
        c = c.text
    s = xml.SectionNumber
    if s:
        s = s.text
    return (t, c, s)

AMEND_INCLUDE = ("add", )
AMEND_EXCLUDE = ("strike", "strikemarkright", "strikemarknone")


for start_year in range(2021, 2023, 2):
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

        # Skip resolutions
        if bill_id.startswith("HR") or bill_id.startswith("SR"):
            continue
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


    for sponsor in bills_by_sponsor:
        print(sponsor, sponsors_by_id[sponsor])
        for bill in bills_by_sponsor[sponsor]:
            bill_id = bill.BillId.text
            print(bill_id, bill.ShortDescription.text)
            print(bill.LongDescription.text)
            print(bill.HistoryLine.text)
            # print(bill.CurrentStatus.IntroducedDate.text, bill.CurrentStatus.ActionDate.text)
            # print(bill.CurrentStatus.Status.text)
            if bill_id in amendments_by_bill_id:
                for amendment in amendments_by_bill_id[bill_id]:
                    # print(amendment.Name.text, amendment.SponsorName, amendment.Description.text, amendment.FloorAction.text)
                    url = amendment.PdfUrl.text
                    url = url.replace("Pdf", "Xml").replace("pdf", "xml")
                    # print(url)
                    response = requests.get(url)
                    # if not response.ok:
                    #     print("missing xml version")
                    #     print(amendment)
                    amendment_text = BeautifulSoup(response.content, 'xml')
                    for section in amendment_text.find_all("AmendSection"):
                        # print(section.AmendItem.P.text)
                        new_sections = section.find_all("BillSection")
                        # if not new_sections:
                        #     print(section)
                        #print()
                    #print(amendment)
                    # print()
                    # print()
                # print(amendment)
            else:
                print("no amendments")
            if bill_id in docs_by_id:
                doc = docs_by_id[bill_id]
                url = doc.PdfUrl.text
                url = url.replace("Pdf", "Xml").replace("pdf", "xml")
                print(url)
                text = requests.get(url).content
                bill_text = BeautifulSoup(text, 'xml')
                sections = {}
                new_chapters = {}
                for section in bill_text.find_all("BillSection"):
                    section_number = section.BillSectionNumber.Value.text
                    # print("Bill section", section.attrs, section_number)
                    if "action" not in section.attrs:
                        if section["type"] == "new":
                            lines = []
                            for paragraph in section.find_all("P"):
                                lines.append(paragraph.text)
                            sections[section_number] = lines
                        else:
                            print(section)
                    elif section["action"] == "repeal":
                        # print("delete", get_citation(section))
                        pass
                    elif section["action"] == "amend":
                        # print("amend", get_citation(section))
                        # print("##", section.Caption.text)
                        section_lines = []
                        for paragraph in section.find_all("P"):
                            line = []
                            for child in paragraph.children:
                                if isinstance(child, NavigableString):
                                    line.append(str(child))
                                else:
                                    if child.name != "TextRun":
                                        if child.name == "Hyphen" and child["type"] == "nobreak":
                                            line.append("‑")
                                        elif child.name not in ("Leader",):
                                            print(paragraph)
                                            raise RuntimeError()
                                    if "amendingStyle" not in child.attrs:
                                        # print("no amend style", child.name, child)
                                        pass
                                    elif child["amendingStyle"] in AMEND_INCLUDE:
                                        line.append(child.text)
                            if line:
                                section_lines.append("".join(line))
                    elif section["action"] == "addsect":
                        # print("add section to", get_citation(section))
                        # print(section)
                        pass
                    elif section["action"] == "addchap":
                        # print("add chapter to", get_citation(section))
                        # print(section.P.text)
                        pass
                    elif section["action"] == "effdate":
                        # When sections of the bill go into effect. (PR merge date.)
                        # print("add chapter to", get_citation(section))
                        # print(section.P.text)
                        pass
                    elif section["action"] == "emerg":
                        # Emergency bill that would take immediate effect.
                        # print("add chapter to", get_citation(section))
                        # print(section.P.text)
                        pass
                    elif section["action"] == "repealuncod":
                        # Repeal a section of a session law that is uncodified.
                        pass
                    elif section["action"] == "amenduncod":
                        # Amend a section of a session law that is uncodified.
                        pass
                    elif section["action"] == "remd":
                        # Reenact and amend a section. Looks like two bills from the same session
                        # changed the same location and the code revisor had to merge them.
                        pass
                    else:
                        print(section, section.attrs)
            print()


        print("------------------------")
        print()
