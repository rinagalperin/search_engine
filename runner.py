# if __name__ == '__main__':
#     main("corpus", "../", False)
import os
import time
from multiprocessing import Process

from combiner import combine_docs, combine_cities, combine_minis, craete_inv
from process_utils import split_tasks_by_processes, process_run
from read_file import ReadFile


def run(input_path, output_path, stem):
    t0 = time.time()

    # read the corpus and divide to files (and to processes)
    read_file = ReadFile(input_path)
    process_list = []
    paths_of_files = read_file.get_file()
    list_of_process_task = split_tasks_by_processes(paths_of_files)

    # create all necessary folders if they don't already exist
    if not os.path.exists(output_path + "/output"):
        os.makedirs(output_path + "/output")

    if not os.path.exists(output_path + "/output/mini"):
        os.makedirs(output_path + "/output/mini")

    if not os.path.exists(output_path + "/output/docs"):
        os.makedirs(output_path + "/output/docs")

    if not os.path.exists(output_path + '/output/combine_file'):
        os.makedirs(output_path + '/output/combine_file')

    if not os.path.exists(output_path + '/output/inverted_index'):
        os.makedirs(output_path + '/output/inverted_index')

    if not os.path.exists(output_path + '/output/cities'):
        os.makedirs(output_path + '/output/cities')

    for i, task in enumerate(list_of_process_task):
        p = Process(target=process_run, args=(task, i, output_path, stem, input_path))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()

    # create the inverted indexes and finally the dictionary
    num_of_docs = combine_docs(list_of_process_task, output_path)
    combine_cities(output_path)
    combine_minis(output_path)
    num_of_terms = craete_inv(output_path)

    #print(int((time.time() - t0) / 60), ":", int(time.time() - t0) % 60)
    return num_of_docs, num_of_terms, (time.time() - t0)