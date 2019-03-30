import json
import multiprocessing
import ujson
import os
import shutil
import tkinter as tk
import webbrowser
import pandas as pd
from random import randint
from tkinter import *
from tkinter import ttk, filedialog

from classifier import is_alpha
from ranker import Ranker
from runner import run
from searcher import Searcher


class GUI:
    def __init__(self, master):
        self.inverted_index = {}
        self.results = {}
        self.entities = {}
        self.chosen_cities = []

        self.corpus_path_str = tk.StringVar()
        self.output_path_str = tk.StringVar()
        self.query_str = tk.StringVar()
        self.queries_path_str = tk.StringVar()
        self.results_path_str = tk.StringVar()
        self.doc_entities_name_str = tk.StringVar()
        self.language = tk.IntVar()

        self.master = master

        # Text input name
        Label(master, text="Corpus and Stop-Words path:", background='gray21', fg='gray77').grid(row=0)
        Label(master, text="Output path:", background='gray21', fg='gray77').grid(row=1)
        Label(master, text="Insert query:", background='gray21', fg='gray77').grid(row=9)
        Label(master, text="Choose queries path:", background='gray21', fg='gray77').grid(row=10)
        Label(master, text="Choose query results path:", background='gray21', fg='gray77').grid(row=12)
        Label(master, text="Doc name for entities:", background='gray21', fg='gray77').grid(row=13)

        # window title
        master.wm_title("Search Engine Project - Shachar Oren & Rina Galperin")

        ########################
        #     Paths Choice     #
        ########################

        # get user's input
        self.corpus_path = tk.Entry(master, textvariable=self.corpus_path_str, background='gray21', fg='gray77', highlightbackground='gray23')
        self.output_path = tk.Entry(master, textvariable=self.output_path_str, background='gray21', fg='gray77', highlightbackground='gray23')
        self.query = tk.Entry(master, textvariable=self.query_str, background='gray21', fg='gray77', highlightbackground='gray23')
        self.queries_path = tk.Entry(master, textvariable=self.queries_path_str, background='gray21', fg='gray77', highlightbackground='gray23')
        self.results_path = tk.Entry(master, textvariable=self.results_path_str, background='gray21', fg='gray77', highlightbackground='gray23')
        self.doc_entities_name = tk.Entry(master, textvariable=self.doc_entities_name_str, background='gray21', fg='gray77', highlightbackground='gray23')

        # input location on screen
        self.corpus_path.grid(row=0, column=1)
        self.output_path.grid(row=1, column=1)
        self.query.grid(row=9, column=1)
        self.queries_path.grid(row=10, column=1)
        self.results_path.grid(row=12, column=1)
        self.doc_entities_name.grid(row=13, column=1)

        # interface buttons
        self.browse_corpus_btn = Button(text="Browse", command=self.choose_corpus_path, background='gray21', fg='gray77', highlightbackground='gray21')
        self.browse_corpus_btn.grid(row=0, column=2)

        self.browse_output_btn = Button(text="Browse", command=self.choose_output_path, background='gray21', fg='gray77', highlightbackground='gray21')
        self.browse_output_btn.grid(row=1, column=2)

        self.search_query_btn = Button(text="RUN", command=self.search_query, background='gray21', fg='gray77', highlightbackground='gray21')
        self.search_query_btn.grid(row=9, column=2)

        self.browse_queries_btn = Button(text="Browse", command=self.choose_queries_path, background='gray21', fg='gray77', highlightbackground='gray21')
        self.search_queries_btn = Button(text="RUN", command=self.search_queries, background='gray21', fg='gray77', highlightbackground='gray21')

        self.browse_results_output_btn = Button(text="Browse", command=self.choose_results_output_path, background='gray21', fg='gray77', highlightbackground='gray21')
        self.browse_results_output_btn.grid(row=12, column=2)

        self.save_results_btn = Button(text="Save", command=self.save_results, background='gray21', fg='gray77', highlightbackground='gray21')
        self.save_results_btn.grid(row=12, column=3)

        self.browse_queries_btn.grid(row=10, column=2)
        self.search_queries_btn.grid(row=10, column=3)

        self.choose_city_btn = Button(text="Choose cities", command=self.pop_cities, background='gray21', fg='gray77', highlightbackground='gray21')
        self.choose_city_btn.grid(row=4, column=0)

        self.search_doc_entities_btn = Button(text="Search Entities", command=self.search_entities, background='gray21', fg='gray77', highlightbackground='gray21')
        self.search_doc_entities_btn.grid(row=13, column=2)

        ########################
        #    Stemming Choice   #
        ########################

        self.stem = tk.IntVar()
        tk.Checkbutton(master, text="use stemming", variable=self.stem, background='gray21', fg='gray77').grid(row=2, column=1, sticky=tk.W)

        ###########################
        #    Dictionary Choices   #
        ###########################
        self.city = tk.IntVar()

        self.create_dictionary_btn = Button(text="Create Dictionary", command=self.create_dictionary, background='gray21', fg='gray77', highlightbackground='gray21')
        self.create_dictionary_btn.grid(row=2, column=0)

        self.display_dictionary_btn = Button(text="Display Dictionary", command=self.display_dictionary, background='gray21', fg='gray77', highlightbackground='gray21')
        self.display_dictionary_btn.grid(row=3, column=0)

        self.save_dictionary_btn = Button(text="To Memory", command=self.load_dictionary_to_memory, background='gray21', fg='gray77', highlightbackground='gray21')
        self.save_dictionary_btn.grid(row=3, column=1)

        self.reset_all_btn = Button(text="Reset All", command=self.reset_all, background='gray21', fg='gray77', highlightbackground='gray21')
        self.reset_all_btn.grid(row=3, column=2)

        #####################################
        #    Semantic and Entities Choice   #
        #####################################
        self.is_semantic = tk.IntVar()
        tk.Checkbutton(master, text="perform semantic search", variable=self.is_semantic, background='gray21', fg='gray77').grid(row=11, column=0, sticky=tk.W)

        self.is_entities = tk.IntVar()
        tk.Checkbutton(master, text="perform entities search", variable=self.is_entities, background='gray21', fg='gray77').grid(row=11, column=1, sticky=tk.W)

    # create pop-up message
    def pop_up_msg(self, msg, title="Message"):
        win = tk.Toplevel()
        win.wm_title(title)

        l = tk.Label(win, text=msg)
        l.grid(row=0, column=0)

        b = tk.Button(win, text="OK", command=win.destroy)
        b.grid(row=1, column=0)

    # create a message upon exiting
    def exit_msg(self, msg):
        win = tk.Toplevel()
        win.wm_title("Exit")

        l = tk.Label(win, text=msg)
        l.grid(row=0, column=0)

        b = tk.Button(win, text='OK', command=self.close)
        b.grid(row=1, column=0)

    # when exiting - exit code will be 0
    def close(self):
        exit(0)

    def create_dictionary(self):
        """retrieves all the parameters given by the user and initiates the entire logical process
                        """
        valid = self.validate_paths()
        if valid:
            corpus = self.corpus_path.get()
            output = self.output_path.get()
            if self.stem.get():
                output += '/stem'
            else:
                output += '/no_stem'

            num_of_docs, num_of_terms, time = run(corpus, output, self.stem.get())

            self.pop_up_msg("number of docs: " + str(num_of_docs) + '\n' +
                            "number of terms: " + str(num_of_terms) + '\n' +
                            "run time in seconds: " + str(time) + '\n')

    def reset_all(self):
        """deletes all the folders and items in them that were created during the run of the program
        (indexes, dictionary, posting files)
                        """
        valid = self.validate_paths()
        if valid:
            if os.path.exists(self.output_path.get() + '/no_stem'):
                try:
                    shutil.rmtree(self.output_path.get() + '/no_stem')
                except:
                    pass
            if os.path.exists(self.output_path.get() + '/stem'):
                    try:
                        shutil.rmtree(self.output_path.get() + '/stem')
                    except:
                        pass

            self.inverted_index = {}
            self.pop_up_msg("successfully cleared all output files")

    def display_dictionary(self):
        """Displays the dictionary to the user
                """
        valid = self.validate_paths()
        output = self.output_path.get()

        if valid:
            if self.stem.get():
                output += '/stem'
            else:
                output += '/no_stem'

            inverted_index_path = output + '/output/inverted_index.txt'
            webbrowser.open(inverted_index_path)

    def load_dictionary_to_memory(self):
        """loads the dictionary file to a variable in the program's memory
                """
        valid = self.validate_paths()
        output = self.output_path.get()

        if self.stem.get():
            output += '/stem'
        else:
            output += '/no_stem'
        if valid:
            with open(output + '/output/inverted_index.txt') as terms:
                for l in terms.readlines():
                    json_line = ujson.loads(l)
                    self.inverted_index[json_line['term']] = {'appearances': json_line['appearances'],
                                                              'ptr': json_line['ptr']}

            self.ranker = Ranker(output)
            self.display_languages()

            self.pop_up_msg("dictionary was successfully loaded to memory")

    def display_languages(self):
        """loads languages from all docs language tag
                        """
        output = self.output_path.get()

        if self.stem.get():
            output += '/stem'
        else:
            output += '/no_stem'

        Label(self.master, text="Choose a language for the documents: ", background='gray21', fg='gray77').grid(row=4, column=1)
        language_choices = []
        with open(output + '/output/docs.txt') as docs:
            for l in docs.readlines():
                json_line = json.loads(l)
                if 'language' in json_line and is_alpha(json_line['language']) and json_line['language'] not in language_choices:
                    language_choices.append(json_line['language'])
        # language_choices = ['English', 'German', 'Russian', 'French', 'Arabic']  # all possible choices
        self.language.set('English')  # the default option
        popup_menu = OptionMenu(self.master, self.language, *language_choices, 'English')
        popup_menu.grid(row=4, column=2)

    def choose_corpus_path(self):
        """open a dialog to allow user to choose a path for the corpus and stop_words.txt file
                """
        self.corpus_path_str.set(self.corpus_path.get())
        self.corpus_path_str.set(filedialog.askdirectory())

    def choose_output_path(self):
        """open a dialog to allow user to choose a path for the output files
                        """
        self.output_path_str.set(self.output_path.get())
        self.output_path_str.set(filedialog.askdirectory())

    def choose_queries_path(self):
        """open a dialog to allow user to choose a path for the output files
                        """
        self.queries_path_str.set(self.queries_path.get())
        self.queries_path_str.set(filedialog.askdirectory())

    def search_query(self):
        """searches a single query
                        """
        if len(self.inverted_index) == 0:
            self.pop_up_msg("please load dictionary to memory")
        elif self.query_str.get() == '':
            self.pop_up_msg("please enter a query")
        else:
            output = self.output_path.get()
            if self.stem.get():
                output += '/stem'
            else:
                output += '/no_stem'

            searcher = Searcher(self.inverted_index, output, self.ranker, self.corpus_path.get())
            query = self.query_str.get()
            query_num = randint(0, 9)
            res, res_entities = searcher.search(query, query_num, self.is_semantic.get(), self.is_entities.get(),
                                                self.chosen_cities)
            self.results = {}
            self.entities = {}

            if self.is_entities.get():
                self.results[query_num] = res
                self.entities = res_entities
            else:
                self.results[query_num] = res

            self.display_results()
            self.chosen_cities = []

    def search_queries(self):
        """searches a file of queries
                        """
        if len(self.inverted_index) == 0:
            self.pop_up_msg("please load dictionary to memory")
        else:
            output = self.output_path.get()
            if self.stem.get():
                output += '/stem'
            else:
                output += '/no_stem'

            searcher = Searcher(self.inverted_index, output, self.ranker, self.corpus_path.get())

            queries_file_path = self.queries_path_str.get()

            with open(queries_file_path, 'r') as queries_file:
                data = queries_file.read().replace('\n', '')

            queries = {}
            self.results = {}
            self.entities = {}

            subs = ['<top>', '<num>', '<desc', '<narr>', '</top>']
            res = re.findall(r'({0})\s*(.*?)(?=\s*(?:{0}|$))'.format("|".join(subs)), data)
            for x in res:
                if x[0] == '<num>':
                    num_title = x[1].split('<title> ')
                    num = num_title[0].split('Number: ')[1].strip()
                    query = num_title[1].strip()
                    queries[num] = query

            for query_num, query in queries.items():
                res, res_entities = searcher.search(query, query_num, self.is_semantic.get(), self.is_entities.get(), self.chosen_cities)
                self.results[query_num] = res

                if self.is_entities.get():
                    self.entities = self.append_dict(self.entities, res_entities)

            self.display_results()
            self.chosen_cities = []

    def append_dict(self, dict1: dict, dict2: dict):
        """merges 2 dictionaries
                        """
        ans = {}
        keys = set(dict1.keys()) | set(dict2.keys())
        for k in keys:
            if k in dict1:
                ans[k] = dict1[k]
            else:
                ans[k] = dict2[k]

        return ans

    def display_results(self):
        """displays the results found for the queries onto the screen
                        """
        with open("results.txt", "w") as text_file:
            for key, value in self.results.items():
                d = {}
                for doc, score in value:
                    d['docs'] = d.get('docs', []) + [doc]
                    d['score'] = d.get('score', []) + [score]

                df = pd.DataFrame(data=d)

                text_file.write('query ' + '#' + str(key) + ':\n')
                text_file.write(df.to_string())
                text_file.write('\n')

        webbrowser.open("results.txt")

    def save_results(self):
        """saves the results to a file
                        """
        results_output = self.results_path.get()
        if not os.path.exists(results_output):
            self.pop_up_msg("please choose a valid directory")
        else:
            # format: query_id, iter, docno, rank, sim, run_id
            ans = ''
            for query_num, query_results in self.results.items():
                for doc_num, doc_rank in query_results:
                    ans += str(query_num) + ' 0 ' + str(doc_num) + ' ' + str(doc_rank) + ' 1.0 mt\n'

            with open(results_output + '/query_results.txt', 'w') as file:
                file.write(ans)

            self.pop_up_msg('results file was created successfully')

    def search_entities(self):
        """gets a specific doc's entities
                        """
        if len(self.inverted_index) == 0:
            self.pop_up_msg("please load dictionary to memory")
        elif len(self.results) == 0:
            self.pop_up_msg("please search a query")
        elif len(self.doc_entities_name.get()) == 0:
            self.pop_up_msg("please enter a doc name to get its entities")
        elif not self.doc_entities_name.get() in self.entities.keys():
            self.pop_up_msg("please enter a valid doc name")
        else:
            self.pop_up_msg(self.entities[self.doc_entities_name.get()])

    def choose_results_output_path(self):
        """open a dialog to allow user to choose a path for the results file
                                """
        self.results_path_str.set(self.results_path.get())
        self.results_path_str.set(filedialog.askdirectory())

    def validate_paths(self):
        """checks if two paths were provided by the user before starting the entire logical process
                        """
        corpus = self.corpus_path.get()
        output = self.output_path.get()

        if not os.path.isdir(corpus) or not os.path.isdir(output):
            self.pop_up_msg("please choose a valid directory")
            return False
        else:
            return True

    def pop_cities(self):
        """creates a pop up window with all optional cities, allows multiple choice of cities
            for query search
            """
        valid = self.validate_paths()
        if valid:
            if self.stem.get():
                output = '/stem'
            else:
                output = '/no_stem'
            if os.path.exists(self.output_path.get() + output + '/output/cities.txt'):
                choices = []
                with open(self.output_path.get() + output + '/output/cities.txt') as cities:
                    all_cities = ujson.loads(cities.readlines()[0])
                    for city in all_cities:
                        json_city = all_cities[city]

                        if 'name' in json_city and json_city['name'] not in choices:
                            choices.append(json_city['name'])

                self.master2 = Toplevel()
                self.master2.title("Choose cities")
                self.master2.geometry("+50+150")
                self.master2.protocol("WM_DELETE_WINDOW", self.master2_close)
                frame = ttk.Frame(self.master2, padding=(3, 3, 12, 12))
                frame.grid(column=0, row=0, sticky=(N, S, E, W))

                city_options = StringVar()
                city_options.set(choices)

                self.lstbox = Listbox(frame, listvariable=city_options, selectmode=MULTIPLE, width=20, height=10)
                self.lstbox.grid(column=0, row=0, columnspan=2)

                btn = ttk.Button(frame, text="OK", command=self.select_cities)
                btn.grid(column=1, row=1)
                self.master2.mainloop()
            else:
                self.pop_up_msg('Please create the dictionary first')

    def select_cities(self):
        """extracts chosen cities to be used while answering the query
            """
        result_list = list()
        selections = self.lstbox.curselection()
        for selection in selections:
            result_list.append(self.lstbox.get(selection))

        self.master2_close()
        self.chosen_cities = result_list

    def master2_close(self):
        """closes window
            """
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.master2.destroy()

    def master3_close(self):
        """closes window
            """
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        self.master3.destroy()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    root = Tk()
    root.configure(background='gray21')
    my_gui = GUI(root)
    root.mainloop()

