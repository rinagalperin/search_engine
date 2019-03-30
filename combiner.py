import json
import ujson
import numpy as np
import os
from multiprocessing import Process
from shutil import copyfile

from process_utils import split_tasks_by_processes


def combine_cities(output_path):
    """Combines all the sub-inverted indexes we gathered for the cities into one
        """
    file_city = os.listdir(output_path + "/output/cities")
    all = {}
    for file in file_city:
        with open(output_path + '/output/cities/' + file, 'r') as f:
            city_dict = ujson.load(f)
            for city, val in city_dict.items():
                all[city] = all.get(city, {})
                all[city].update(val)

    with open(output_path + '/output/cities.txt', 'w') as cities_file:
        ujson.dump(all, cities_file)


def combine_minis(output_path):
    """Handles the assignment of mini inverted indexes to the processes,
    which they will be combining pair by pair until one inverted index is created.
            """
    process_list = []
    dir_names = os.listdir(output_path + "/output/mini")

    for p, tasks in enumerate(split_tasks_by_processes(dir_names)):
        p = Process(target=combine_two_files, args=(tasks, p, output_path))
        p.start()
        process_list.append(p)

    for p in process_list:
        p.join()


def combine_docs(list_of_process_task, output_path):
    """Combines all the information the processes have gathered about
    all the docs to form one index for docs and their metadata.
            """
    with open(output_path + '/output/docs.txt', 'w') as doc_file:
        for i in range(len(list_of_process_task)):
            with open(output_path + '/output/docs/docs' + str(i) + '.txt', 'r') as doc_task_file:
                doc_file.write(doc_task_file.read())

    with open(output_path + '/output/docs.txt', 'r') as doc_file:
        num_of_docs = len(doc_file.readlines())

    return num_of_docs


def combine_two_files(dir_names, p, output_folder):
    """Combines two mini inverted indexes at a time into one,
        each time reading only one line from each one and comparing the terms.
        The path of combined result is then entered into the list of paths for combining
        to be combined again with another mini inverted index.
    """
    for dir_name in dir_names:
        dir_path = os.path.join(output_folder + "/output/mini", dir_name)
        path_output = os.path.join(output_folder + '/output/inverted_index', dir_name)
        file_path = [os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)]
        cont = 0
        while len(file_path) > 1:
            path1 = file_path.pop(0)
            path2 = file_path.pop(0)

            output_path = os.path.join(output_folder + '/output/combine_file', str(p) + '_' + str(cont) + ".txt")
            cont += 1
            file_path.append(output_path)

            # opens the two mini inverted indexes and the desired output destination
            with open(output_path, 'w') as output:
                with open(path1, 'r') as mini_1:
                    with open(path2, 'r') as mini_2:
                        # read first term from each mini inverted index
                        line_1 = mini_1.readline()
                        line_2 = mini_2.readline()
                        while line_1 and line_2:

                            # get the metadata for the terms
                            term_metadata_1 = ujson.loads(line_1)
                            term_metadata_2 = ujson.loads(line_2)

                            # get the term itself
                            term_1 = term_metadata_1['name']
                            term_2 = term_metadata_2['name']

                            # compare which term comes first in a lexicographic order
                            if term_1.lower() < term_2.lower():
                                output.write(line_1)
                                line_1 = mini_1.readline()
                            elif term_2.lower() < term_1.lower():
                                output.write(line_2)
                                line_2 = mini_2.readline()
                            # if it's the same term - combine their metadatas
                            else:
                                term_metadata_1['appearances'] += term_metadata_2['appearances']
                                if term_1 != term_2:
                                    term_metadata_1['name'] = term_1.lower()

                                output.write(ujson.dumps(term_metadata_1) + '\n')
                                line_1 = mini_1.readline()
                                line_2 = mini_2.readline()

                        # check which file ended first
                        mini_last = mini_1 if line_1 else mini_2

                        # append the rest of the unfinished file to the output file
                        while True:
                            line = mini_last.readline()
                            if line:
                                output.write(line)

                            if not line:
                                break

        dst = path_output + ".txt"
        src = file_path.pop(0)
        copyfile(src, dst)

def craete_inv(output_path):
    """Once all the posting files have been created, the dictionary is created as well,
    containing the sum of appearances for a term and a pointer to its posting file
            """
    dir_path = output_path + "/output/inverted_index"
    dir_names = os.listdir(dir_path)
    num_of_terms = 0

    with open(output_path + '/output/inverted_index.txt', 'w') as output:
        for dir in dir_names:
            with open(os.path.join(dir_path,dir), 'r') as mini:
                for i,l in enumerate(mini.readlines()):
                    num_of_terms += 1
                    line_json = ujson.loads(l)
                    sum_of_the_appearances =  np.sum(np.array(line_json["appearances"])[:, 1].astype(np.int))
                    #output.write(line_json['name'] + ': ' + str(sum_of_the_appearances) + '\n')
                    output.write(json.dumps({'term': line_json['name'],
                                              'appearances': str(sum_of_the_appearances),
                                              'ptr': str(i)}) + '\n')

    return num_of_terms
