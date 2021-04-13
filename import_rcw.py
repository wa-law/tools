import string
import requests_cache
import sqlite3
from bs4 import BeautifulSoup

rcw_root_url = "https://apps.leg.wa.gov/rcw/"

requests = requests_cache.CachedSession("cache")

root = requests.get(rcw_root_url)

soup = BeautifulSoup(root.text, 'html.parser')

sections = soup.find(id="ContentPlaceHolder1_dgSections")
titles = {}
for row in sections.find_all("tr"):
    data = row.find_all("td")
    link = data[0].find("a")
    directory_name = link.text[len("Title "):]
    title_name = data[1].text.strip()
    print(link["href"], directory_name, title_name)
    titles[directory_name] = {"link": link["href"], "title": title_name, "chapters": {}}

all_citations = set()

for title in titles:
    print("title", title)
    info = titles[title]
    soup = BeautifulSoup(requests.get(rcw_root_url + info["link"]).text, 'html.parser')
    table = soup.find("table")
    for row in table.find_all("tr"):
        link = row.find("a")
        section_info = {}
        info["chapters"][link.text] = {"link": link["href"] + "&full=true",
                                       "title": data[1].text.strip(),
                                       "sections": section_info}
        print(link["href"], link.text)
        data = row.find_all("td")
        print(data[1].text)

        chapter = BeautifulSoup(requests.get(link["href"] + "&full=true").text, 'html.parser')
        sections = chapter.find(id="ContentPlaceHolder1_dlSectionContent")
        if not sections:
            continue
        for section in sections.find_all("span"):
            divs = section.find_all("div", recursive=False)
            if not divs:
                continue
            number_link = divs[0].find("a")
            # TODO: Chapter 11.130 has articles to partition sections.
            if not number_link:
                continue
            number = number_link.text
            name = divs[1].h3.text
            full_div = 2
            if "CHANGE IN" in divs[full_div].text:
                full_div = 3
            full_text = [d.text for d in divs[full_div].find_all("div")]
            citations = []
            section_info[number] = {"title": name, "body": full_text, "citations": citations}
            print(number, name)
            # if number == "2.36.010":
            #     print(section.prettify())
            # print("full", full_text)
            if len(divs) == full_div + 1:
                continue
            full_citations = divs[full_div+1].text
            full_citations = full_citations.replace("(i)", "").replace("(ii)", "")
            full_citations = full_citations.replace("(1)", "").replace("(2)", "") 
            full_citations = full_citations.replace(". Prior:", ";")
            raw_citations = full_citations.strip("[] .").split(";")
            if not raw_citations:
                continue
            if ". Formerly RCW" in raw_citations[-1]:
                raw_citations[-1] = raw_citations[-1].split(". Formerly RCW")[0]
            history = [x.strip() for x in raw_citations]
            links = {}
            for link in divs[full_div+1].find_all("a"):
                links[link.text] = link["href"]
            chapter_citations = []
            for citation in history:
                if "repealed by" in citation:
                    cs = citation.strip("()").split(" repealed by ")
                elif "expired" in citation:
                    print(citation)
                    cs = citation.strip("()").split(" expired ")[:1]
                else:
                    cs = [citation]
                for c in cs:
                    citations.append((c, links.get(c, None)))
                    c = c.strip("()")
                    chapter_citation = c.split("§")[0].strip()
                    if chapter_citation.startswith("1 H.C."):
                        print(c)
                        raise RuntimeError()
                    all_citations.add(chapter_citation)

            print()
    #print(titles)

ordered = sorted(all_citations)
print(len(ordered))
print(ordered[:2000])

