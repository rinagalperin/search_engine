import os
from bs4 import BeautifulSoup


def get_all_docs_from_file(path):
    """Divides a file into all the DOCs it contains
       """
    all_doc = []
    with open(path) as FileObj:
        text = FileObj.read()
        soup = BeautifulSoup(text, "html.parser")

        # gather doc information for the metadata
        for doc in soup.find_all('doc'):
            name = doc.find_all('docno')[0].text.strip()

            if len(doc.find_all('text')) == 0:
                continue

            text = doc.find_all('text')[0].text
            city = doc.find_all('f', p=lambda s:s.startswith('104'))
            city = city[0].text.strip().split(" ")[0] if len(city) == 1 else ""

            language = doc.find_all('f', p=lambda s: s.startswith('105'))
            language = language[0].text.strip() if len(language) == 1 else ""
            # extra 2 values of information on each doc: date, title
            date = doc.find_all('date1')
            date = date[0].text.strip() if len(date) == 1 else ""
            title = doc.find_all('ti')
            title = title[0].text.strip() if len(title) == 1 else ""
            # create the doc's metadata
            all_doc.append({
                'name': name,
                'text': text,
                'length': len(text),
                'city': city.upper(),
                'date': date,
                'title': title,
                'language': language
            })

    return all_doc


class ReadFile:
    def __init__(self, path):
        self.folders = os.listdir(path)
        self.path = path

    def get_file(self):
        """Returns all paths of inner files
           """
        files = []
        for i, folder in enumerate(self.folders):
                file_path = os.path.join(self.path, folder)
                if os.path.isdir(file_path):
                    file = os.listdir(file_path)
                    path = os.path.join(file_path, file[0])
                    files.append(path)
        return files

