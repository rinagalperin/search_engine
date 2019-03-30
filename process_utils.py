import ujson
import time

import read_file
from indexer import Indexer
from parse import Parser

num_of_process = 8
files_per_process = 20


def split_tasks_by_processes(lst):
    """Splits the array of paths
        according to the number of desires processes,
        so that each process has a list of paths to go over.
        each 'task' is a list of paths for a process, and 'ans' contains all such tasks.
       """
    task_list = []
    ans = []
    for file in lst:
        task_list.append(file)
        if len(task_list) > len(lst) / num_of_process:
            ans.append(task_list)
            task_list = []

    if len(task_list) > 0:
        ans.append(task_list)
    return ans


def process_run(task, p, output_path, stem, corpus_path):
    """process 'p' will perform 'task' - a list of files, each one contains several docs.
        The process will parse each doc and then index it.
        once the desired number of files per process is reached -
        the indexer saves the result as a 'mini inverted index'.
           """
    city_minis = dict()
    parser = Parser(stem, corpus_path)
    with open(output_path + '/output/docs/docs' + str(p) + '.txt', 'w') as doc_file:
        indexer = Indexer()

        for i, file in enumerate(task):
            docs = read_file.get_all_docs_from_file(file)
            for doc in docs:
                parser_result = parser.parse(doc)
                if len(parser_result) > 0:
                    indexer.add_to_dict(parser_result, doc, doc_file, file, city_minis)

            # the desired number of files per process is reached - save the result
            # and 'clear' the indexer by creating a new one
            if i % files_per_process == 0 and i != 0:
                indexer.save(file, output_path)
                indexer = Indexer()

        # save again in case the number wasn't precisely divided by 'files_per_process'
        indexer.save(file, output_path)

    with open(output_path + '/output/cities/' + str(p) + '.txt', 'w') as cities_file:
        ujson.dump(city_minis, cities_file)
